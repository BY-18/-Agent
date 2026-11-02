# 从 dataclasses 导入 dataclass 与 field：
#   dataclass 把类声明成数据结构，field 用于指定默认值工厂（default_factory）
from dataclasses import dataclass, field
# 导入 datetime 类型，用于标注时间字段
from datetime import datetime


# 所有业务实体的公共基类：统一携带审计字段（软删除标记、创建/修改人与时间）
# 子类继承它之后，就自动拥有了这 5 个字段，无需重复声明
@dataclass
class CommonBaseEntity:
    # 软删除标记：'0' 表示未删除，'1' 表示已删除（默认未删除）
    del_flag: str | None = '0'
    # 创建时间：default_factory 表示每次实例化时都重新调用 datetime.now() 取当前时间
    create_time: datetime | None = field(default_factory=datetime.now)
    # 创建人（默认空，由业务代码填充）
    create_by: str | None = None
    # 修改时间：实例化时也取当前时间
    update_time: datetime | None = field(default_factory=datetime.now)
    # 修改人（默认空，由业务代码填充）
    update_by: str | None = None
