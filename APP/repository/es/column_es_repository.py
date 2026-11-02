from dataclasses import asdict
# 导入 hashlib：取值过长时用哈希生成 ES 的 _id（ES 限制 _id 最长 512 字节）
import hashlib

from elasticsearch import AsyncElasticsearch

from APP.entity.value_info import ValueInfo


class ColumnEsRepository:
    _index_name = 'column_es_oy'
    _index_mapping = {
        'dynamic': False,
        "properties": {
            "id":{'type':'keyword'},
            "value":{'type':'text',"analyzer": "ik_max_word","search_analyzer": "ik_max_word"},
            "column_id":{'type':'keyword'},
        }
    }
    def __init__(self, client:AsyncElasticsearch):
        self.client = client

    # 创建es索引
    async def createIndex(self):
        if not await self.client.indices.exists(index= self._index_name):
            await self.client.indices.create(
                index = self._index_name,
                mappings= self._index_mapping
            )

    # ES 的 _id 最长 512 字节，取值太长（长中文枚举值）时改用 sha1，避免整批写入被拒
    @staticmethod
    def _build_doc_id(value_id: str) -> str:
        raw = value_id.encode('utf-8')
        if len(raw) <= 512:
            return value_id
        return hashlib.sha1(raw).hexdigest()

    async def insertIndex(self,values:list[ValueInfo],batch_size:int=20):
        for i in range(0,len(values),batch_size):
            batch = values[i:i+batch_size]
            operations = []
            for value in batch:
                # 注意：_id 必须写在 action 元数据里面（{"index": {"_index": ..., "_id": ...}}），
                # 写成 action 的同级键会被 ES 忽略，导致每个文档都用自动 ID，重复执行会写入重复数据
                operations.append(
                    { "index" : { "_index" : self._index_name, "_id" : self._build_doc_id(value.id) } }
                )
                # 添加文档数据
                operations.append(asdict(value))
            await self.client.bulk(operations=operations)
        # 写入后立即刷新，保证紧接着的检索能查到刚写入的取值
        if values:
            await self.client.indices.refresh(index=self._index_name)

    async def search(self,keyword:str,limit:int = 5):
        # 说明：ES 的 min_score 用的是 BM25 原始分数，与 0~1 的相似度不可比，
        #      固定阈值容易把结果全部过滤掉（原代码 min_score=0.5 就是这个隐患），
        #      这里只做相关性排序后取前 limit 条，不再限制分数
        result = await self.client.search(
            index= self._index_name,
            query={
                "match":{
                    "value": keyword
                }
            },
            size=limit,
        )
        # es 返回的固定数据结构，
        return [ValueInfo(**hit['_source']) for hit in result['hits']['hits']]


