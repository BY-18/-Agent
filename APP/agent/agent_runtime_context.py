from typing import TypedDict

from APP.client.custom_embedding_client import CustomEmbeddingClient
from APP.repository.es.column_es_repository import ColumnEsRepository
from APP.repository.mysql.column_info_mysql_repository import ColumnInfoMySqlRepository
from APP.repository.mysql.dw.dw_mysql_repostory import DwMysqlRepostory
from APP.repository.mysql.table_info_mysql_repository import TableInfoMySqlRepository
from APP.repository.qdrant.column_qdrant_repository import ColumnQdrantRepository
from APP.repository.qdrant.metric_qdrant_repository import MetricQdrantRepository


class AgentRuntimeContext(TypedDict):
    embedding_client : CustomEmbeddingClient
    column_qdrant_repository: ColumnQdrantRepository
    metric_qdrant_repository: MetricQdrantRepository
    column_es_repository: ColumnEsRepository

    column_mysql_repository:ColumnInfoMySqlRepository
    table_mysql_repository: TableInfoMySqlRepository

    dw_mysql_repository: DwMysqlRepostory