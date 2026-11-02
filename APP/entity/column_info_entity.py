# 导入 Any：用于标注 examples 里可以是任意类型的取值
from typing import Any

# 使用 pydantic 版本的 dataclass，以便运行时做类型校验
from pydantic.dataclasses import dataclass
# 导入公共基类，提供 del_flag / create_time 等公共审计字段
from APP.entity.common_entity import CommonBaseEntity


# 字段信息业务实体：贯穿“配置 -> 实体 -> 数据模型 -> 向量/搜索引擎”的核心对象
@dataclass
class ColumnInfoEntity(CommonBaseEntity):
    '''
    id  :主键id（表名.字段名）
    name  :字段名称
    role  :字段角色 主键 / 外键 / 度量值 / 维度值
    description  :字段业务描述
    '''
    # 字段唯一标识，格式为“表名.字段名”，例如 fact_order.order_amount
    id: str | None = None
    # 字段名，例如 order_amount
    name: str | None = None
    # 字段角色：primary_key / foreign_key / measure / dimension
    role: str | None = None
    # 字段的业务描述（中文），会被向量化用于语义召回
    description: str | None = None
    # 字段在数据仓库中的数据类型，例如 decimal(10,2)
    type: str | None = None
    # 字段别名列表，例如 ["销售额", "订单金额", "收入"]
    alias: list[str] | None = None
    # 所属表的表名（同时充当外键 table_id），例如 fact_order
    table_id: str | None = None
    # 字段的示例取值列表（从数据仓库抽样得到），供大模型理解数据分布
    examples: list[Any] | None = None
