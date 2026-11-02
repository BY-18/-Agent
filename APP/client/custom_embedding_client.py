# 导入 LangChain 提供的 OpenAI 向量化（Embedding）客户端
# 只要服务端兼容 OpenAI 的 /v1/embeddings 接口，就能直接复用这个类
from langchain_openai import OpenAIEmbeddings

# 导入向量化服务的配置类（host、port、embedding_size）
from APP.config.APP_config import EmbeddingConfig


# 向量化（embedding）客户端封装
class CustomEmbeddingClient:
    '''
    向量化（embedding）客户端封装，兼容 OpenAI 接口协议
    '''

    # 构造方法：保存配置并拼装服务地址
    def __init__(self, config: EmbeddingConfig):
        # 保存向量化服务配置
        self._config = config
        # 根据配置生成 OpenAI 兼容的接口地址
        self._url = self._get_url()

    # 拼装 OpenAI 兼容的 v1 接口地址（Embeddings 接口路径会自动拼接为 /embeddings）
    def _get_url(self):
        # 格式：http://主机:端口/v1，例如 http://172.16.50.95:8081/v1
        return f"http://{self._config.host}:{self._config.port}/v1"

    # 创建向量化客户端
    def get_client(self) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            # 指向本地/内网的 OpenAI 兼容服务
            base_url=self._url,
            # 该服务不校验密钥，这里给个占位符即可
            api_key='unused',
            # 关闭“先计算 token 长度再决定是否切分文本”的逻辑，
            # 避免本地服务不支持 tiktoken 编码时抛错
            check_embedding_ctx_length=False,
        )
