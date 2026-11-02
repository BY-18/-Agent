from datetime import datetime

import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from APP.agent.agent_llm import llm
from APP.agent.agent_runtime_context import AgentRuntimeContext
from APP.agent.agent_state import AgentState
from APP.utils.loader_prompt_util import load_prompt_by_path
from APP.utils.log_util import logger


async def generateSQL(state:AgentState,runtime: Runtime[AgentRuntimeContext]):

    metric_infos = state["metric_infos"]
    table_infos = state["table_infos"]
    question  = state['question']
    # 当前日期：提示词里用它来推算“去年 / 最近三个月”这类相对时间
    current_date = datetime.now().strftime('%Y-%m-%d')

    # 使用大模型生成 SQL
    prompt = PromptTemplate(
        template=load_prompt_by_path('generate_sql'),
        input_variables=['query','metric_infos','table_infos','date_info'],
    )

    output = StrOutputParser()
    chain = prompt | llm | output
    # allow_unicode 保留中文的Unicode 字符
    #sort_keys 是否保持原有的顺序
    sql = await chain.ainvoke(
        {
            'query': question,
            'metric_infos': yaml.dump(metric_infos,allow_unicode=True,sort_keys=False),
            'table_infos': yaml.dump(table_infos,allow_unicode=True,sort_keys=False),
            'date_info': current_date,
        }
    )



    logger.info('生成的sql语句为：{}', sql)

    return {'generate_sql':sql}