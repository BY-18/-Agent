# 从 dataclasses 导入 asdict：可以把一个 dataclass 实例递归转换成普通字典
from dataclasses import asdict
# 导入字段信息业务实体（业务层使用的对象）
from APP.entity.column_info_entity import ColumnInfoEntity
# 导入字段信息数据模型（数据库 ORM 映射对象）
from APP.model.column_info_model import ColumnInfoModel


# 字段信息实体转换工具：负责“数据库模型”与“业务实体”之间的双向转换
# 好处是业务层不用关心数据库长什么样，实现了两者的解耦
class ColumnInfoMapper:
    '''
    字段信息实体转换工具
    '''

    # 静态方法：Model（数据库行） -> Entity（业务对象）
    @staticmethod
    def to_entity(model: ColumnInfoModel) -> ColumnInfoEntity:
        # 逐个字段搬运，显式列出可以避免把审计字段等无关字段也带过去
        return ColumnInfoEntity(
            # 字段唯一标识
            id=model.id,
            # 字段名
            name=model.name,
            # 字段业务描述
            description=model.description,
            # 字段数据类型
            type=model.type,
            # 字段别名（数据库里是 JSON，读出来已是 list）
            alias=model.alias,
            # 字段示例取值
            examples=model.examples,
            # 字段角色
            role=model.role,
            # 所属表 id
            table_id=model.table_id,
        )

    # 静态方法：Entity（业务对象） -> Model（数据库行）
    @staticmethod
    def to_model(entity: ColumnInfoEntity) -> ColumnInfoModel:
        # asdict 会把 dataclass 拆成字典，再用 ** 解包成 Model 的构造参数
        # 注意：Model 中多出的 qdrant_id 字段不在字典里，会保持为 None
        return ColumnInfoModel(**asdict(entity))
