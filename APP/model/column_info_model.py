# 从 sqlalchemy 导入列类型：String 变长字符串、CHAR 定长字符串、Text 长文本、JSON 结构化数据
from sqlalchemy import String, CHAR, Text, JSON
# 导入 Mapped 与 mapped_column，用于类型注解式声明列
from sqlalchemy.orm import Mapped, mapped_column

# 导入公共基类，继承它即可获得软删除标记与创建/修改审计字段
from APP.model.common_base import CommonBase


# 字段信息数据模型：映射元数据库里的 t_column_info 表
class ColumnInfoModel(CommonBase):
    # 指定对应的数据库表名
    __tablename__ = 't_column_info'
    # 主键：字段唯一标识，格式“表名.字段名”，最大 32 字符
    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment='主键id')
    # 字段名称，最大 64 字符
    name: Mapped[str] = mapped_column(String(64), comment='名称')
    # 字段角色：主键/外键/度量值/维度值
    role: Mapped[str] = mapped_column(String(32), comment='列类型(primary_key,foreign_key,measure,dimension)')
    # 字段业务描述，用 Text（不限制长度）
    description: Mapped[str] = mapped_column(Text, comment='描述')
    # 字段示例取值，以 JSON 数组形式存储
    examples: Mapped[str] = mapped_column(JSON, comment='数据示例')
    # 字段在数据仓库中的数据类型，如 decimal(10,2)
    type: Mapped[str] = mapped_column(String(64), comment='数据类型')
    # 字段别名，以 JSON 数组形式存储
    alias: Mapped[str] = mapped_column(JSON, comment='别名')
    # 所属表 id（即表名），用于建立字段与表的关联
    table_id: Mapped[str] = mapped_column(String(32), comment='表id')
    # 预留字段：记录该字段在 Qdrant 中对应的数据点 id（当前业务代码未写入）
    qdrant_id: Mapped[str] = mapped_column(String(32), comment='Qdrant数据点id')
