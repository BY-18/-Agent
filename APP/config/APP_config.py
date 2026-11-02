# 从 dataclasses 导入 dataclass 装饰器，用于把类声明成“数据结构”
from dataclasses import dataclass
# 导入 Path：用于跨平台拼接文件路径
from pathlib import Path

# 导入通用的配置加载函数（YAML -> dataclass）
from APP.utils.load_config_util import load_config


# 所有“网络服务”配置的公共基类：只包含主机地址与端口
@dataclass
class BaseConfig:
    # 服务主机地址，例如 172.16.50.95
    host: str
    # 服务端口号，例如 3306
    port: int


# MySQL 数据库配置，在基类基础上增加账号、密码、库名
@dataclass
class DBConfig(BaseConfig):
    # 数据库用户名
    user: str
    # 数据库密码
    password: str
    # 数据库名称（元数据库 meta / 数据仓库 dw）
    database: str


# Qdrant 向量数据库配置：只需要 host 和 port，故直接继承基类
@dataclass
class QdrantConfig(BaseConfig):
    # pass 表示不再新增字段，直接复用父类的 host、port
    pass


# Embedding 向量化服务配置
@dataclass
class EmbeddingConfig(BaseConfig):
    # 向量维度（必须与向量库集合的维度一致，如 1024）
    embedding_size: int


# Elasticsearch 配置：同样只需要 host 和 port
@dataclass
class ESConfig(BaseConfig):
    # 不新增字段，复用父类
    pass


# 大模型（LLM）配置：本项目用 OpenAI 兼容协议调用
@dataclass
class LLMConfig:
    # 模型服务的接口地址（OpenAI 兼容的 base_url）
    base_url: str
    # 调用模型所需的 api key
    api_key: str
    # 模型名称，例如 gpt-4o-mini、deepseek-chat
    model: str


# 应用顶层配置：把各种组件配置聚合到一个对象里
@dataclass
class APPConfig:
    # 元数据库（存放表/字段/指标元数据）的连接配置
    db_meta: DBConfig
    # 数据仓库（存放业务事实/维度数据）的连接配置
    db_dw: DBConfig
    # 向量数据库 Qdrant 的连接配置
    qdrant: QdrantConfig
    # 向量化服务（Embedding）的连接配置
    embedding: EmbeddingConfig
    # 全文检索 Elasticsearch 的连接配置
    es: ESConfig
    # 大模型（LLM）配置：与 config/APP_config.yaml 里的 llm 段一一对应
    # 注意：该字段必须声明，否则 OmegaConf 结构化校验会因 YAML 多出 llm 键而报 ConfigKeyError
    llm: LLMConfig


# 加载配置文件 , 将配置文件的信息解析到 APPConfig 对象中
# __file__ 是当前文件路径，parents[2] 表示向上退 3 层目录（APP/config/APP_config.py -> 项目根目录）
file_path = Path(__file__).parents[2] / 'config' / 'APP_config.yaml'
# 模块级全局变量：项目其它模块 import app_config 即可拿到解析好的配置对象
app_config: APPConfig = load_config(file_path, APPConfig)
