# 导入 JSON 输出解析器：把大模型返回的文本解析成 Python 的 list/dict
from langchain_core.output_parsers import JsonOutputParser
# 导入提示词模板：用变量占位符拼出最终提示词
from langchain_core.prompts import PromptTemplate
# 导入 Runtime：LangGraph 注入的运行时对象，可读取上下文、写流式输出
from langgraph.runtime import Runtime

# 导入全局大模型对象（用于扩词）
from APP.agent.agent_llm import llm
# 导入运行时上下文类型（从中取 ES 仓储）
from APP.agent.agent_runtime_context import AgentRuntimeContext
# 导入全局状态类型
from APP.agent.agent_state import AgentState
# 导入字段取值实体类型
from APP.entity.value_info import ValueInfo
# 导入关键词归一函数：把模型返回的扩词结果统一成字符串列表（避免类型不符时拼接报错）
from APP.utils.json_parser_util import normalize_str_list
# 导入提示词加载函数：按文件名读取 prompts 目录下的 .prompt 文件
from APP.utils.loader_prompt_util import load_prompt_by_path
# 导入全局日志对象
from APP.utils.log_util import logger


async  def retrievalValue(state:AgentState,runtime:Runtime[AgentRuntimeContext]):
    '''
        从状态中取出问题、关键词
        扩词
        召回
    '''
    question = state["question"]
    keywords = state["keywords"]

    # 从运行时上下文中获取对象
    column_es_repository = runtime.context['column_es_repository']
    # 使用大模型进行扩词

    # 构造提示词模板：正文来自 prompts/extend_keywords_for_value_recall.prompt
    prompt = PromptTemplate(
        template=load_prompt_by_path('extend_keywords_for_value_recall'),
        # 模板里用到的变量名是 query
        input_variables=['query']
    )

    # 输出解析器：把模型返回的 JSON 文本解析成 Python 列表
    output = JsonOutputParser()
    # 用管道符把“提示词 -> 大模型 -> 解析器”串成一条链
    chain = prompt  | llm | output
    # 异步执行整条链，得到扩充后的关键词列表
    try:
        extended_keywords = normalize_str_list(await chain.ainvoke({'query': question}))
    except Exception as exc:
        # 模型偶发返回非 JSON 时降级：只用 jieba 抽出的关键词继续召回
        logger.warning('取值扩词失败，仅使用原始关键词：{}', exc)
        extended_keywords = []

    # 将扩展的关键词合并原来的keywords（去掉空串与重复项）
    all_keywords = list(dict.fromkeys(normalize_str_list(list(keywords) + extended_keywords)))
    if not all_keywords:
        logger.warning('取值召回没有可用关键词，返回空结果')
        return {'retrieval_values': []}
    # 关键词检索内容
    retrieval_value_map : dict[str, ValueInfo]  = {}
    for keyword in all_keywords:
        # 关键词检索
        values: list[ValueInfo] = await column_es_repository.search(keyword)
        # print('查询的关键字为',keyword)
        # print('查询的关键字结果为：',values)
        # 去重存储
        for value in values:
            value_id = value.id
            if value_id not in retrieval_value_map:
                retrieval_value_map[value_id] = value
    #将字段转换为列表
    retrieval_values = list(retrieval_value_map.values())
    # writer = runtime.stream_writer
    # writer(all_keywords)
    # writer(retrieval_values)
    logger.info('取值召回数据：{}', retrieval_values)
    return {'retrieval_values':retrieval_values, }


