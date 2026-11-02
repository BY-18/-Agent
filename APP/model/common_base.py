# 从 sqlalchemy 导入列类型：String 变长字符串、CHAR 定长字符串、DateTime 日期时间
from datetime import datetime
from sqlalchemy import String, CHAR, DateTime
# 导入 SQLAlchemy 2.0 的 ORM 基类与列声明工具：
#   DeclarativeBase —— 声明式映射的基类
#   Mapped        —— 类型注解式的字段声明
#   mapped_column —— 把一个属性映射成数据库中的列
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# 所有数据模型（表映射类）的公共基类：
#   继承 DeclarativeBase 后，本类及其子类都会被 SQLAlchemy 识别为 ORM 映射类；
#   子类只需声明 __tablename__ 和自身字段，审计字段在这里统一声明，实现复用
class CommonBase(DeclarativeBase):
    # 软删除标记，定长 1 位字符
    del_flag: Mapped[str] = mapped_column(CHAR(1), comment='是否删除 0 未删除  1 已删除')
    # 创建时间
    create_time: Mapped[datetime] = mapped_column(DateTime, comment='创建时间')
    # 创建者账号（最长 64 字符）
    create_by: Mapped[str] = mapped_column(String(64), comment='创建者')
    # 最后修改时间
    update_time: Mapped[datetime] = mapped_column(DateTime, comment='修改时间')
    # 最后修改者账号（最长 64 字符）
    update_by: Mapped[str] = mapped_column(String(64), comment='修改者')
