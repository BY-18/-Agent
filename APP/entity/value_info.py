# 从 dataclasses 导入 dataclass 装饰器，用于声明轻量数据结构
from dataclasses import dataclass


# 字段取值实体：表示某个字段的一个“具体取值”，用于写入 Elasticsearch 做精确值检索
# 例如 字段 fact_order.order_amount 的取值 199.00、字段 dim_region.province 的取值 "广东省"
@dataclass
class ValueInfo:
    # 文档唯一标识，格式为“字段id.取值”，例如 fact_order.province.广东省
    id: str
    # 具体的取值（统一转成字符串，方便 ES 索引）
    value: str
    # 该取值所属字段的 id，用于反查字段信息
    column_id: str
