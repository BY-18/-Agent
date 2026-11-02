# 从 sqlalchemy 导入列类型 String、CHAR（本文件中 CHAR 未实际使用，保留原样）
from sqlalchemy import String, CHAR
# 导入 Mapped 与 mapped_column，用于类型注解式声明列
from sqlalchemy.orm import Mapped, mapped_column
# 导入公共基类，继承它即可获得软删除标记与创建/修改审计字段
from APP.model.common_base import CommonBase


# 字段与指标的关联关系数据模型：映射 t_metric_column 关系表（多对多中间表）
class ColumnMetricModel(CommonBase):
    # 指定对应的数据库表名
    __tablename__ = 't_metric_column'
    # 联合主键之一：字段 id，如 fact_order.order_amount
    column_id: Mapped[str] = mapped_column(String(32), primary_key=True, comment='字段id')
    # 联合主键之二：指标 id，如 GMV
    metric_id: Mapped[str] = mapped_column(String(64), primary_key=True, comment='指标id')
