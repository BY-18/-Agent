import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from APP.agent.agent_llm import llm
from APP.agent.agent_runtime_context import AgentRuntimeContext
from APP.agent.agent_state import AgentState, TableInfoState
from APP.utils.loader_prompt_util import load_prompt_by_path
from APP.utils.log_util import logger


async def filterTable(state:AgentState,runtime: Runtime[AgentRuntimeContext]):

    table_infos = state["table_infos"]
    question  = state['question']

    # 使用大模型进行过滤
    prompt = PromptTemplate(
        template=load_prompt_by_path('filter_table_info'),
        input_variables=['query','table_infos'],
    )

    output = JsonOutputParser()
    chain = prompt | llm | output
    # allow_unicode 保留中文的Unicode 字符
    #sort_keys 是否保持原有的顺序
    result = await chain.ainvoke(
        {
            'query': question,
            'table_infos': yaml.dump(table_infos,allow_unicode=True,sort_keys=False),
        }
    )
    # 大模型应返回 {"表名": ["字段名", ...]}；返回其它结构时不再继续裁剪，避免把候选全删空
    if not isinstance(result, dict):
        logger.warning('过滤结果不是字典，跳过裁剪：{}', result)
        return {'table_infos': table_infos}

    # 模型可能返回带空白或大小写不一致的键，这里统一成去掉空白的字符串键
    selected_map = {str(key).strip(): value for key, value in result.items()}

    # 构造新列表，不原地修改 state 中的对象（LangGraph 不建议在节点里改入参）
    filtered_tables: list[TableInfoState] = []
    for table_info in table_infos:
        # 该表被选中的字段；表未被选中时直接丢弃整张表
        selected_columns = selected_map.get(str(table_info['name']).strip())
        if not selected_columns:
            continue
        # 兼容模型把字段列表返回成单个字符串，或返回 [{"name": "order_amount"}] 这类结构
        if isinstance(selected_columns, str):
            selected_columns = [selected_columns]
        if not isinstance(selected_columns, (list, tuple, set)):
            logger.warning('表 {} 的字段过滤结果结构异常，已跳过：{}',
                           table_info['name'], selected_columns)
            continue
        selected_names = {
            item.get('name') if isinstance(item, dict) else str(item).strip()
            for item in selected_columns
        }
        selected_names.discard(None)
        # 只保留模型选中的字段
        kept_columns = [
            column for column in table_info['columns'] if column['name'] in selected_names
        ]
        # 字段一个都没匹配上时整表丢弃，避免留下没有字段的空表
        if not kept_columns:
            logger.warning('表 {} 没有匹配到任何字段，已跳过', table_info['name'])
            continue
        filtered_tables.append({**table_info, 'columns': kept_columns})

    # 模型把所有表都过滤掉时回退为全量候选，避免把空表结构交给大模型
    if not filtered_tables:
        logger.warning('大模型没有选中任何表，回退为候选表全量：{}',
                       [table_info['name'] for table_info in table_infos])
        return {'table_infos': table_infos}

    logger.info('过滤后的表数据：{}', filtered_tables)

    return {'table_infos':filtered_tables}