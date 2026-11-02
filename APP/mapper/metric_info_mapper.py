# 从 dataclasses 导入 asdict：可以把一个 dataclass 实例递归转换成普通字典
from dataclasses import asdict

# 导入指标信息业务实体
from APP.entity.metric_info_entity import MetricInfoEntity
# 导入指标信息数据模型
from APP.model.metric_info_model import MetricInfoModel


# 指标信息实体转换工具：负责指标表模型与业务实体之间的双向转换
class MetricInfoMapper:
    '''
    指标信息实体转换工具
    '''

    # 静态方法：Model（数据库行） -> Entity（业务对象）
    @staticmethod
    def to_entity(model: MetricInfoModel) -> MetricInfoEntity:
        return MetricInfoEntity(
            # 指标唯一标识
            id=model.id,
            # 指标名称
            name=model.name,
            # 指标描述（含计算口径）
            description=model.description,
            # 指标别名列表
            alias=model.alias,
            # 指标关联的字段列表
            relevant_columns=model.relevant_columns,
        )

    # 静态方法：Entity（业务对象） -> Model（数据库行）
    @staticmethod
    def to_model(entity: MetricInfoEntity) -> MetricInfoModel:
        # 把实体拆成字典后用 ** 解包，作为 Model 的构造参数
        return MetricInfoModel(**asdict(entity))
