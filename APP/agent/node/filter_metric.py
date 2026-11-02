import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from APP.agent.agent_llm import llm
from APP.agent.agent_runtime_context import AgentRuntimeContext
from APP.agent.agent_state import AgentState, MetricInfoState
from APP.utils.loader_prompt_util import load_prompt_by_path
from APP.utils.log_util import logger


async def filterMetric(state:AgentState,runtime: Runtime[AgentRuntimeContext]):

    metric_infos = state["metric_infos"]
    question  = state['question']

    # 使用大模型进行过滤
    prompt = PromptTemplate(
        template=load_prompt_by_path('filter_metric_info'),
        input_variables=['query','metric_infos'],
    )

    output = JsonOutputParser()
    chain = prompt | llm | output
    # allow_unicode 保留中文的Unicode 字符
    #sort_keys 是否保持原有的顺序
    result = await chain.ainvoke(
        {
            'query': question,
            'metric_infos': yaml.dump(metric_infos,allow_unicode=True,sort_keys=False),
        }
    )
    # 大模型应返回指标名数组；返回其它结构时不做裁剪，避免把候选全删空
    if not isinstance(result, list):
        logger.warning('过滤结果不是列表，跳过裁剪：{}', result)
        return {'metric_infos': metric_infos}

    # 构造新列表，不原地修改 state 中的对象（LangGraph 不建议在节点里改入参）
    # 兼容模型返回 [{"name": "GMV"}] 这种带结构的写法，结构不符的项直接忽略
    selected_metric_names = set()
    for item in result:
        if isinstance(item, dict):
            name = item.get('name')
        else:
            name = str(item).strip()
        if isinstance(name, str) and name:
            selected_metric_names.add(name.strip())

    filtered_metrics: list[MetricInfoState] = [
        metric_info for metric_info in metric_infos
        if metric_info['name'] in selected_metric_names
    ]

    logger.info('过滤后的指标数据：{}', filtered_metrics)

    return {'metric_infos':filtered_metrics}