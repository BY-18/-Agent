# 导入 copy：合并取值时复制字段实体，避免原地修改 state 里的同一份对象
from copy import copy
# 导入 Runtime：LangGraph 注入的运行时对象，可读取上下文、写流式输出
from langgraph.runtime import Runtime

# 导入运行时上下文类型（从中取字段/表元数据仓储）
from APP.agent.agent_runtime_context import AgentRuntimeContext
# 导入状态结构：全局状态 + 三种“输出结构”类型
from APP.agent.agent_state import AgentState, TableInfoState, ColumnInfoState, MetricInfoState
# 导入字段信息实体类型
from APP.entity.column_info_entity import ColumnInfoEntity
# 导入表信息实体类型
from APP.entity.table_info_entity import TableInfoEntity
# 导入全局日志对象
from APP.utils.log_util import logger


async  def mergeRetrieval(state:AgentState,runtime:Runtime[AgentRuntimeContext]):
    '''
        1、从状态中获取字段、指标、取值
        2、将指标中字段信息取出，查询mysql数据库
        3、取值的信息存入字段的examples属性中
        4、根据表的ID进行数据分组
        5、根据表id查询表的主键和外键
        6、构建完整的表信息和指标信息结构
    '''
    # 从状态中取出前面三个并行节点写入的召回结果
    retrieval_columns = state["retrieval_columns"]
    retrieval_metrics = state["retrieval_metrics"]
    retrieval_values = state["retrieval_values"]

    # 从运行时上下文中获取对象
    column_mysql_repository = runtime.context['column_mysql_repository']
    table_mysql_repository = runtime.context['table_mysql_repository']
    # 将字段列表转换为字典，方便快速查询
    retrieval_columns_map = {
        retrieval_column.id: retrieval_column
        for retrieval_column in retrieval_columns
    }

    # 将指标信息的相关字段添加到字段字典中
    # 原因：指标召回时只知道“指标”，但它依赖的字段可能没有被字段召回节点召回，
    #       必须把这些字段补进来，否则最终表结构里会缺列
    for metric in retrieval_metrics:
        # 取出该指标关联的字段 id 列表；该字段在库里可能为 NULL，用 or [] 兜底
        relevant_columns = metric.relevant_columns or []
        # 循环指标关联字段
        for retrieval_column in relevant_columns:
            # 判断指标字段id不在字段列表字典中，需要完善数据
            if retrieval_column not in retrieval_columns_map:
                # 按字段 id 回查 MySQL 拿到字段的完整信息
                column_info = await column_mysql_repository.get_column_info_by_id(retrieval_column)
                # 库里查不到该字段时跳过，避免把 None 存进字典导致后面 None.examples 报错
                if column_info is None:
                    logger.warning('指标关联字段在元数据库中不存在，已跳过：{}', retrieval_column)
                    continue
                # 将查询的数据添加到字典中
                retrieval_columns_map[retrieval_column] = column_info

    #将取值合并到字段字典中
    # 原因：按值召回得到的是“某个字段的某个取值”，要把它挂到对应字段上
    for retrieval_value in retrieval_values:
        # 该取值所属的字段 id
        column_id = retrieval_value.column_id
        # 取值本身（正常是字符串；ES 中的历史脏数据可能是一条文档里存了多个取值）
        column_value = retrieval_value.value
        # 统一成字符串列表，兼容一条文档存多个取值的旧数据
        value_items = column_value if isinstance(column_value, list) else [column_value]
        value_items = [str(item) for item in value_items if item is not None]

        # 判断column_id是否在retrieval_columns_map，如果不在，则查询mysql数据
        column_info = retrieval_columns_map.get(column_id)
        if column_info is None:
            column_info = await column_mysql_repository.get_column_info_by_id(column_id)
            # 字段不存在时跳过，避免对 None 取属性
            if column_info is None:
                logger.warning('取值所属字段在元数据库中不存在，已跳过：{}', column_id)
                continue
            retrieval_columns_map[column_id] = column_info
        # 将取值合并进字段的 examples
        # 注意：examples 在库里可能是 NULL（取出来是 None）；
        #      这里复制实体后再写，避免直接改动 state['retrieval_columns'] 里的同一份对象
        existing_examples = [str(item) for item in (column_info.examples or [])]
        new_examples = [item for item in value_items if item not in existing_examples]
        if not new_examples:
            # 取值已全部存在，无需重复合并
            continue
        merged_column = copy(column_info)
        merged_column.examples = existing_examples + new_examples
        retrieval_columns_map[column_id] = merged_column

    # 按照字段所属的表ID进行分组
    # 结构：{表名: [该表下的字段实体, ...]}，字段的 table_id 就是表名
    table_to_columns_map :dict[str,list[ColumnInfoEntity]] = {}
    # 遍历所有字段，按 table_id 归组
    for column in retrieval_columns_map.values():
        # 取出该字段所属的表名
        table_id = column.table_id
        # 该表第一次出现时，先在字典里初始化一个空列表
        if table_id not in table_to_columns_map:
            table_to_columns_map[table_id] = []
        # 把字段加入对应表的列表
        table_to_columns_map[table_id].append(column)

    # 逐张表补全主键 / 外键字段（JOIN 需要用到，但前面召回时不一定能召回到）
    for table_id in table_to_columns_map:
        # 查询表的主外键
        key_columns = await column_mysql_repository.get_key_by_table_id(table_id)
        #获取table_to_columns_map中指定表的所有的字段id
        column_ids = [column.id for column in table_to_columns_map[table_id]]
        # 循环主外键字段信息
        for key_column in key_columns:
            # 判断主外键字段id是否存在，不存在则添加
            if key_column.id not in column_ids:
                table_to_columns_map[table_id].append(key_column)

    # 将table_id -> columns映射转换为list[TableInfoState]
    table_infos: list[TableInfoState] = []
    # 逐张表处理：查询表信息 + 把字段转成状态结构
    for table_id,columns in table_to_columns_map.items():
        # 根据表id查询表的详细信息
        tableInfo:TableInfoEntity = await table_mysql_repository.get_table_info_by_id(table_id)
        # 元数据库里查不到这张表时跳过，避免对 None 取属性
        if tableInfo is None:
            logger.warning('表在元数据库中不存在，已跳过：{}', table_id)
            continue

        # 把每个字段实体转换成“状态结构”，只保留最终需要交给大模型的字段
        columns_state = [
            ColumnInfoState(
                # 字段名
                name=column.name,
                # 字段数据类型
                type=column.type,
                # 字段角色（主键/外键/度量/维度）
                role=column.role,
                # 字段业务描述
                description=column.description,
                # 字段别名列表
                alias=column.alias or [],
                # 字段示例取值（含从 ES 召回的取值）；库里可能为 NULL，用空列表兜底
                examples=column.examples or [],
            )
            # 遍历该表下的所有字段
            for column in columns
        ]

        # 创建表信息的状态对象
        table_state = TableInfoState(
            # 表名
            name = tableInfo.name,
            # 表角色（fact / dim）
            role = tableInfo.role,
            # 表业务描述
            description = tableInfo.description,
            # 该表下的字段列表
            columns=columns_state,
        )
        # 加入最终结果列表
        table_infos.append(table_state)

    # 把每个指标实体转换成“状态结构”，供最终 prompt 使用
    metric_infos :list[MetricInfoState] = [
        MetricInfoState(
            # 指标名，如 GMV
            name=metric.name,
            # 指标描述（含计算口径）
            description=metric.description,
            # 指标关联的字段 id 列表；库里可能为 NULL，用空列表兜底
            retrieval_columns=metric.relevant_columns or [],
            # 指标别名列表；库里可能为 NULL，用空列表兜底
            alias=metric.alias or [],
        )
        # 遍历本次召回的所有指标
        for metric in retrieval_metrics
    ]
    # 取出流式写出器，把合并后的最终结果推给前端
    writer = runtime.stream_writer
    writer({'table_infos':table_infos,'metric_infos':metric_infos})

    # 返回需要写回状态的字段（LangGraph 会把它合并进 AgentState）
    return {'table_infos':table_infos,'metric_infos':metric_infos}







