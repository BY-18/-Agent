# 导入 JSON 输出解析器：把大模型返回的文本解析成 Python 的 list/dict
from langchain_core.output_parsers import JsonOutputParser
# 导入提示词模板：用变量占位符拼出最终提示词
from langchain_core.prompts import PromptTemplate
# 导入 Runtime：LangGraph 注入的运行时对象，可读取上下文、写流式输出
from langgraph.runtime import Runtime

# 导入全局大模型对象（用于扩词）
from APP.agent.agent_llm import llm
# 导入运行时上下文类型（从中取 embedding 客户端与向量库仓储）
from APP.agent.agent_runtime_context import AgentRuntimeContext
# 导入全局状态类型
from APP.agent.agent_state import AgentState
# 导入字段信息实体类型
from APP.entity.column_info_entity import ColumnInfoEntity
# 导入关键词归一函数：把模型返回的扩词结果统一成字符串列表（避免类型不符时拼接报错）
from APP.utils.json_parser_util import normalize_str_list
# 导入提示词加载函数：按文件名读取 prompts 目录下的 .prompt 文件
from APP.utils.loader_prompt_util import load_prompt_by_path
# 导入全局日志对象
from APP.utils.log_util import logger


async  def retrievalColumns(state:AgentState,runtime:Runtime[AgentRuntimeContext]):
    '''
        从状态中取出问题、关键词
        扩词
        召回
    '''
    question = state["question"]
    keywords = state["keywords"]

    # 从运行时上下文中获取对象
    embedding_client  = runtime.context["embedding_client"]
    column_qdrant_repository = runtime.context["column_qdrant_repository"]

    # 使用大模型进行扩词

    # 构造提示词模板：模板正文来自 prompts/extend_keywords_for_column_recall.prompt
    prompt = PromptTemplate(
        template=load_prompt_by_path('extend_keywords_for_column_recall'),
        # 模板里用到的变量名是 query（下面 ainvoke 时传入 question）
        input_variables=['query']
    )

    # 输出解析器：把模型返回的 JSON 文本解析成 Python 列表
    output = JsonOutputParser()
    # 用 LCEL 的管道符把“提示词 -> 大模型 -> 解析器”串成一条链
    chain = prompt  | llm | output
    # 异步执行整条链，得到模型扩充出来的关键词列表
    try:
        extended_keywords = normalize_str_list(await chain.ainvoke({'query': question}))
    except Exception as exc:
        # 模型偶发返回非 JSON 时降级：只用 jieba 抽出的关键词继续召回
        logger.warning('字段扩词失败，仅使用原始关键词：{}', exc)
        extended_keywords = []
    # 将扩展的关键词合并原来的keywords（去掉空串与重复项）
    all_keywords = list(dict.fromkeys(normalize_str_list(list(keywords) + extended_keywords)))
    if not all_keywords:
        logger.warning('字段召回没有可用关键词，返回空结果')
        return {'retrieval_columns': []}
    # 向量数据库检索内容
    retrieval_columns_map : dict[str, ColumnInfoEntity]  = {}
    for keyword in all_keywords:
        # 向量化keyword
        embeddings = await embedding_client.aembed_query(keyword)
        # 检索
        payloads: list[ColumnInfoEntity] = await column_qdrant_repository.search(embeddings)
        # 去重存储
        for payload in payloads:
            column_id = payload.id
            if column_id not in retrieval_columns_map:
                retrieval_columns_map[column_id] = payload
        # 将字段转换为列表
    retrieval_columns = list(retrieval_columns_map.values())

    logger.info('字段召回数据：{}', retrieval_columns)
    return {'retrieval_columns': retrieval_columns, }



