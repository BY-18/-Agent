# 导入 Qdrant 官方异步客户端
from qdrant_client import AsyncQdrantClient

# 导入 Qdrant 的连接配置类（只含 host、port）
from APP.config.APP_config import QdrantConfig


# Qdrant 向量数据库客户端封装
class CustomQdrantClient:
    '''
    Qdrant 客户端封装
    '''

    # 构造方法：保存配置并拼装服务地址
    def __init__(self, config: QdrantConfig):
        # 保存外部传入的配置
        self._config = config
        # 根据配置生成 http 地址
        self._url = self._get_url()

    # 拼装 Qdrant 的 REST 服务地址
    def _get_url(self):
        # 格式：http://主机:端口，例如 http://172.16.50.95:6333
        return f"http://{self._config.host}:{self._config.port}"

    # 创建异步客户端，并把客户端实例挂到 self.client 上供外部复用时使用
    def get_client(self) -> AsyncQdrantClient:
        # 创建异步客户端，并保存一份引用，便于外部使用和关闭
        self.client = AsyncQdrantClient(url=self._url)
        # 返回客户端实例
        return self.client
