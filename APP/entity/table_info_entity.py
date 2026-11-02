# 使用 pydantic 版本的 dataclass，以便运行时做类型校验
from pydantic.dataclasses import dataclass

# 导入公共基类，提供 del_flag / create_time 等公共审计字段
from APP.entity.common_entity import CommonBaseEntity


# 表信息业务实体：描述数据仓库中的一张表
@dataclass
class TableInfoEntity(CommonBaseEntity):
    '''
    id  :主键id
    name  :表名称
    role  :表角色   事实表、维度表
    description  :表描述
    '''
    # 表唯一标识，直接复用表名，例如 fact_order
    id: str | None = None
    # 表名，例如 dim_region
    name: str | None = None
    # 表角色：fact（事实表）或 dim（维度表）
    role: str | None = None
    # 表的中文业务描述
    description: str | None = None
