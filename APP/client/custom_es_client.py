# 导入 Elasticsearch 官方异步客户端
from elasticsearch import AsyncElasticsearch

# 导入 ES 连接配置类（只含 host、port）
from APP.config.APP_config import ESConfig


# Elasticsearch 客户端封装：负责根据配置生成 ES 服务地址并创建异步客户端
class CustomESClient:
    # 构造方法：保存配置并拼装服务地址
    def __init__(self, config: ESConfig):
        # 保存 ES 配置（host、port）
        self._config = config
        # 根据配置生成 http 地址
        self._url = self._get_url()

    # 拼装 ES 的 REST 服务地址
    def _get_url(self):
        # 格式：http://主机:端口，例如 http://172.16.50.95:9200
        return f"http://{self._config.host}:{self._config.port}"

    # 创建异步 ES 客户端（同时挂到 self.client 上，调用方可直接复用以关闭连接）
    def get_client(self) -> AsyncElasticsearch:
        # 注意：第一个参数是“节点地址列表”，所以这里用 [self._url] 包成列表
        self.client = AsyncElasticsearch([self._url])
        return self.client
