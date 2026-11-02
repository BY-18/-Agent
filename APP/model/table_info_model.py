# 从 sqlalchemy 导入列类型 String、CHAR（本文件中 CHAR 未实际使用，保留原样）
from sqlalchemy import String, CHAR
# 导入 Mapped 与 mapped_column，用于类型注解式声明列
from sqlalchemy.orm import Mapped, mapped_column

# 导入公共基类，继承它即可获得软删除标记与创建/修改审计字段
from APP.model.common_base import CommonBase


# 表信息数据模型：映射元数据库里的 t_table_info 表
class TableInfoModel(CommonBase):
    # 指定对应的数据库表名
    __tablename__ = 't_table_info'
    # 主键：表唯一标识，直接用表名，最大 32 字符
    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment='主键id')
    # 表名称，最大 64 字符
    name: Mapped[str] = mapped_column(String(64), comment='名称')
    # 表角色：dim 维度表 / fact 事实表
    role: Mapped[str] = mapped_column(String(64), comment='角色 0:维度表  1 事实表 ')
    # 表的中文业务描述，最大 255 字符
    description: Mapped[str] = mapped_column(String(255), comment='描述')
