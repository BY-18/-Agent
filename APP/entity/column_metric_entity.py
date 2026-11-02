# 使用 pydantic 版本的 dataclass，以便运行时做类型校验
from pydantic.dataclasses import dataclass
# 导入公共基类，提供 del_flag / create_time 等公共审计字段
from APP.entity.common_entity import CommonBaseEntity


# 字段与指标的关联关系实体：对应数据库里的 t_metric_column 关系表
@dataclass
class ColumnMetricEntity(CommonBaseEntity):
    # 字段 id（联合主键之一），形如 fact_order.order_amount
    column_id: str | None = None
    # 指标 id（联合主键之二），形如 GMV
    metric_id: str | None = None
