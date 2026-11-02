import asyncio

from langgraph.graph import StateGraph

from APP.agent.agent_runtime_context import AgentRuntimeContext
from APP.agent.agent_state import AgentState
from APP.agent.node.column_call import retrievalColumns
from APP.agent.node.filter_table import filterTable
from APP.agent.node.keywords_ext import keywordsExt
from APP.agent.node.merge_retrieved import mergeRetrieval
from APP.agent.node.metric_call import retrievalMetric
from APP.agent.node.generate_sql import generateSQL
from APP.agent.node.execute_sql import executeSQL
from APP.agent.node.filter_metric import filterMetric
from APP.agent.node.value_call import retrievalValue
from APP.client.custom_embedding_client import CustomEmbeddingClient
from APP.client.custom_es_client import CustomESClient
from APP.client.custom_qdrant_client import CustomQdrantClient
from APP.client.mysql_client import CustomMySqlClient
from APP.config.APP_config import app_config
from APP.repository.es.column_es_repository import ColumnEsRepository
from APP.repository.mysql.column_info_mysql_repository import ColumnInfoMySqlRepository
from APP.repository.mysql.table_info_mysql_repository import TableInfoMySqlRepository
from APP.repository.qdrant.column_qdrant_repository import ColumnQdrantRepository
from APP.repository.qdrant.metric_qdrant_repository import MetricQdrantRepository
from APP.repository.mysql.dw.dw_mysql_repostory import DwMysqlRepostory
from APP.utils.log_util import logger

graph = StateGraph(state_schema=AgentState,context_schema=AgentRuntimeContext)
# 添加节点
graph.add_node('keywords_ext',keywordsExt)
graph.add_node('retrievalColumns',retrievalColumns)
graph.add_node('retrievalMetric',retrievalMetric)
graph.add_node('retrievalValue',retrievalValue)
graph.add_node('mergeRetrieval',mergeRetrieval)
graph.add_node('filterTable',filterTable)
graph.add_node('filterMetric',filterMetric)
graph.add_node('generateSQL',generateSQL)
graph.add_node('executeSQL',executeSQL)
# 添加边
# 并行处理
graph.add_edge('keywords_ext','retrievalColumns')
graph.add_edge('keywords_ext','retrievalMetric')
graph.add_edge('keywords_ext','retrievalValue')

# 合并处理
graph.add_edge('retrievalColumns','mergeRetrieval')
graph.add_edge('retrievalMetric','mergeRetrieval')
graph.add_edge('retrievalValue','mergeRetrieval')
graph.add_edge('mergeRetrieval','filterTable')
graph.add_edge('mergeRetrieval','filterMetric')
graph.add_edge('filterMetric','generateSQL')
graph.add_edge('filterTable','generateSQL')
graph.add_edge('generateSQL','executeSQL')


# 设置入口
graph.set_entry_point('keywords_ext')

# 编译
app = graph.compile()


async def run(question: str):
    """
    执行一次完整问答流程（召回 -> 过滤 -> 生成并执行 SQL）。
    返回数据仓库的查询结果；流程结束后统一释放 ES / Qdrant / MySQL 连接。
    """
    # 实例化向量模型客户端
    embedding_client = CustomEmbeddingClient(app_config.embedding).get_client()

    # 实例化 ColumnQdrantRepository / MetricQdrantRepository（共用一个客户端）
    qdrant_client = CustomQdrantClient(app_config.qdrant)
    qdrant = qdrant_client.get_client()
    column_qdrant_repository = ColumnQdrantRepository(qdrant)
    metric_qdrant_repository = MetricQdrantRepository(qdrant)

    # 实例化 ES 客户端与仓储
    es_client = CustomESClient(app_config.es).get_client()
    column_es_repository = ColumnEsRepository(es_client)

    # 实例化元数据库 / 数据仓库的 MySQL 客户端
    meta_mysql_client = CustomMySqlClient(app_config.db_meta)
    session_factory = meta_mysql_client.get_session_factory()
    dw_mysql_client = CustomMySqlClient(app_config.db_dw)
    dw_session_factory = dw_mysql_client.get_session_factory()

    try:
        async with session_factory() as meta_session, dw_session_factory() as dw_session:
            column_mysql_repository = ColumnInfoMySqlRepository(meta_session)
            table_mysql_repository = TableInfoMySqlRepository(meta_session)
            dw_mysql_repository = DwMysqlRepostory(dw_session)

            # 将各仓储与客户端放入运行时上下文，供各节点读取
            context = AgentRuntimeContext(
                embedding_client=embedding_client,
                column_qdrant_repository=column_qdrant_repository,
                metric_qdrant_repository=metric_qdrant_repository,
                column_es_repository=column_es_repository,
                column_mysql_repository=column_mysql_repository,
                table_mysql_repository=table_mysql_repository,
                dw_mysql_repository=dw_mysql_repository,
            )

            # 流式执行（stream_mode='custom'，由节点里的 writer 推送中间结果）
            result = None
            async for chunk in app.astream(
                input={'question': question},
                context=context,
                stream_mode='custom',
            ):
                logger.info('流式输出：{}', chunk)
                if isinstance(chunk, dict) and 'data' in chunk:
                    result = chunk['data']
            return result
    finally:
        # 释放 HTTP 连接与数据库连接池，避免脚本结束后资源悬挂
        await es_client.close()
        await qdrant.close()
        await meta_mysql_client.dispose()
        await dw_mysql_client.dispose()


async def test():
    rows = await run('给我查询去年各地区第一季度的销售额')
    logger.info('查询结果：{}', rows)


if __name__ == '__main__':
    asyncio.run(test())
