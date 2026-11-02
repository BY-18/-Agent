# 从 dataclasses 导入 field：用于给 dataclass 字段设置默认值等额外信息
from dataclasses import field

# 注意：这里用的是 pydantic 的 dataclass（而不是标准库的）
# 它比标准库版本多了“运行时类型校验”，配置文件里的值类型不对会直接报错
from pydantic.dataclasses import dataclass


# 字段（列）配置：对应元数据 YAML 里 columns 下的一个元素
@dataclass
class ColumnConfig:
    # 字段名，例如 order_amount
    name: str
    # 字段角色，例如 primary_key / foreign_key / measure / dimension
    role: str
    # 字段的中文业务描述，会用于向量化与全文检索
    description: str
    # 字段别名列表，例如 [销售额, 订单金额, 收入]
    alias: list[str]
    # 是否把该字段的“具体取值”同步到 Elasticsearch，用于精确值检索
    sync: bool


# 表配置：对应元数据 YAML 里 tables 下的一个元素
@dataclass
class TableConfig:
    # 表名，例如 fact_order
    name: str
    # 表角色，例如 fact（事实表）/ dim（维度表）
    role: str
    # 表的中文业务描述
    description: str
    # 该表下的所有字段配置列表
    columns: list[ColumnConfig]


# 指标配置：对应元数据 YAML 里 metrics 下的一个元素
@dataclass
class MetricConfig:
    # 指标名，例如 GMV、AOV
    name: str
    # 指标的业务描述（计算口径说明）
    description: str
    # 该指标关联的字段列表，元素形如 'fact_order.order_amount'
    relevant_columns: list[str]
    # 指标别名列表，例如 [成交总额, 订单总额]
    alias: list[str]


# 元数据配置总入口：一个 YAML 文件里同时描述 tables 和 metrics
@dataclass
class MetaConfig:
    # 表配置列表；允许不配置（默认 None）
    tables: list[TableConfig] | None = field(default=None)
    # 指标配置列表；允许不配置（默认 None）
    metrics: list[MetricConfig] | None = field(default=None)
