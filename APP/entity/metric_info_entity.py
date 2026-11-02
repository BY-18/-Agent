# 使用 pydantic 版本的 dataclass，以便运行时做类型校验
from pydantic.dataclasses import dataclass
# 导入公共基类，提供 del_flag / create_time 等公共审计字段
from APP.entity.common_entity import CommonBaseEntity


# 指标信息业务实体：描述一个业务指标（如 GMV = 所有订单成交金额之和）
@dataclass
class MetricInfoEntity(CommonBaseEntity):
    # 指标唯一标识，直接用指标名，例如 GMV
    id: str | None = None
    # 指标名称，例如 GMV / AOV
    name: str | None = None
    # 指标的业务描述（含计算口径），会被向量化用于语义召回
    description: str | None = None
    # 指标别名列表，例如 ["成交总额", "订单总额"]
    alias: list[str] | None = None
    # 该指标关联的字段列表，元素形如 'fact_order.order_amount'
    relevant_columns: list[str] | None = None
