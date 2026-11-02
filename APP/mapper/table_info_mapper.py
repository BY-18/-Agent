# 从 dataclasses 导入 asdict：可以把一个 dataclass 实例递归转换成普通字典
from dataclasses import asdict

# 导入表信息业务实体
from APP.entity.table_info_entity import TableInfoEntity
# 导入表信息数据模型
from APP.model.table_info_model import TableInfoModel


# 表信息实体转换工具：负责表模型与业务实体之间的双向转换
class TableInfoMapper:
    '''
    表信息实体转换工具
    '''

    # 静态方法：Model（数据库行） -> Entity（业务对象）
    @staticmethod
    def to_entity(model: TableInfoModel) -> TableInfoEntity:
        return TableInfoEntity(
            # 表唯一标识（表名）
            id=model.id,
            # 表名称
            name=model.name,
            # 表业务描述
            description=model.description,
            # 表角色（fact / dim）
            role=model.role,
        )

    # 静态方法：Entity（业务对象） -> Model（数据库行）
    @staticmethod
    def to_model(entity: TableInfoEntity) -> TableInfoModel:
        # 把实体拆成字典后用 ** 解包，作为 Model 的构造参数
        return TableInfoModel(**asdict(entity))
