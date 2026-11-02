# 导入 LangChain 的 ChatOpenAI 封装：只要服务端兼容 OpenAI 的 chat/completions 协议就能用
from langchain_openai import ChatOpenAI

# 导入大模型配置类与应用配置类
from APP.config.APP_config import LLMConfig, app_config


# 根据配置初始化大模型客户端
def initLLM(config: LLMConfig):
    return ChatOpenAI(
        # 模型服务的接口地址（OpenAI 兼容的 base_url）
        base_url=config.base_url,
        # 调用模型所需的密钥
        api_key=config.api_key,
        # 模型名称，例如 deepseek-chat
        model=config.model,
    )

# 模块级全局大模型对象，其它节点直接 import llm 即可使用
# 注意：app_config.llm 依赖 APP/config/APP_config.py 里 APPConfig 的 llm 字段，
#   该字段已随 config/APP_config.yaml 的 llm 段补全，可正常取到 LLMConfig。
llm = initLLM(app_config.llm)
