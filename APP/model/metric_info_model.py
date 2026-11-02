# 从 sqlalchemy 导入列类型：String 变长字符串、CHAR 定长字符串、Text 长文本、JSON 结构化数据
from sqlalchemy import String, CHAR, Text, JSON
# 导入 Mapped 与 mapped_column，用于类型注解式声明列
from sqlalchemy.orm import Mapped, mapped_column
# 导入公共基类，继承它即可获得软删除标记与创建/修改审计字段
from APP.model.common_base import CommonBase


# 指标信息数据模型：映射元数据库里的 t_metric_info 表
class MetricInfoModel(CommonBase):
    # 指定对应的数据库表名
    __tablename__ = 't_metric_info'
    # 主键：指标唯一标识，直接用指标名，最大 32 字符
    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment='主键id')
    # 指标名称，最大 64 字符
    name: Mapped[str] = mapped_column(String(64), comment='名称')
    # 指标描述（含计算口径），用 Text（不限制长度）
    description: Mapped[str] = mapped_column(Text, comment='描述')
    # 指标别名，以 JSON 数组形式存储
    alias: Mapped[str] = mapped_column(JSON, comment='别名')
    # 指标关联的字段列表，以 JSON 数组形式存储
    relevant_columns: Mapped[str] = mapped_column(JSON, comment='关联关系')
