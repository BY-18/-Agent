# 从 dataclasses 导入 asdict：把实体转成字典，作为 Qdrant 的 payload
from dataclasses import asdict
# 导入 Qdrant 异步客户端类型，仅用于类型标注
from qdrant_client import AsyncQdrantClient
# 导入 Qdrant 的数据模型：距离算法、向量参数、数据点结构
from qdrant_client.http.models import Distance, VectorParams, PointStruct
# 导入指标信息业务实体
from APP.entity.metric_info_entity import MetricInfoEntity


# 指标信息的 Qdrant 数据交互层：负责创建集合并批量写入指标向量
class MetricQdrantRepository:
    # 集合名称（与字段集合区分开，指标单独存一个集合）
    _collection_name = 'metric_qdrant_oy'

    # 构造方法：
    #   client —— Qdrant 异步客户端
    #   size   —— 向量维度，必须与 embedding 模型输出维度一致（默认 1024）
    def __init__(self, client: AsyncQdrantClient, size: int = 1024):
        # 保存客户端
        self._client = client
        # 保存向量维度
        self._size = size

    # 创建集合（如果不存在）
    async def create_collection(self):
        # 先判断集合是否存在，避免重复创建报错（幂等）
        if not await self._client.collection_exists(self._collection_name):
            await self._client.create_collection(
                self._collection_name,  # 集合名
                # 向量参数：维度 size，距离算法 DOT（内积）
                vectors_config=VectorParams(size=self._size, distance=Distance.DOT)
            )

    # 批量插入或更新指标向量数据点（upsert）
    #   ids / embeddings / payloads 三个列表按位置一一对应
    async def insert_and_update(self, ids: list[str], embeddings: list[list[float]],
                                payloads: list[MetricInfoEntity], batch_size: int = 20):
        # 把三个列表按位置打包成 [(id, 向量, payload), ...]
        zipped = list(zip(ids, embeddings, payloads))
        # 分批处理数据
        for i in range(0, len(zipped), batch_size):
            # 取出当前批次
            batch = zipped[i:i + batch_size]
            # payload 参数为字典，所以需要将payload转asdict(payload)
            # 把每个三元组转成 Qdrant 的 PointStruct 对象
            batch_points = [PointStruct(id=id, vector=embedding, payload=asdict(payload))
                            for id, embedding, payload in batch]
            # 批量 upsert 到指定集合
            await self._client.upsert(collection_name=self._collection_name, points=batch_points)

    # 按向量相似度检索指标
    #   embedding       —— 待检索文本的向量（与写入时使用同一个 embedding 模型）
    #   score_threshold —— 相似度下限，过滤弱相关结果
    #                     向量已归一化，DOT 等价于余弦相似度；实测相关查询 top1 在 0.64~1.0，
    #                     无关查询在 0.38 以下，故默认取 0.6
    #   limit           —— 最多返回的点数
    # 返回值：召回的业务指标实体列表
    async def search(self, embedding: list[float], score_threshold: float = 0.6, limit: int = 5) -> list[
        MetricInfoEntity]:
        # query_points 是 Qdrant 的“检索/近邻查询”接口
        result = await self._client.query_points(
            # 在哪个集合里检索（指标集合）
            collection_name=self._collection_name,
            # 查询向量
            query=embedding,
            # 相似度阈值
            score_threshold=score_threshold,
            # 返回条数上限
            limit=limit
        )
        # 把命中点的 payload 用 ** 解包还原成 MetricInfoEntity 实体返回
        return [MetricInfoEntity(**point.payload) for point in result.points]