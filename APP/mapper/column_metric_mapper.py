# 从 dataclasses 导入 asdict：可以把一个 dataclass 实例递归转换成普通字典
from dataclasses import asdict

# 导入字段-指标关联关系业务实体
from APP.entity.column_metric_entity import ColumnMetricEntity
# 导入字段-指标关联关系数据模型
from APP.model.column_metric_model import ColumnMetricModel


# 字段与指标关联关系实体转换工具：负责关系表模型与业务实体之间的双向转换
class ColumnMetricMapper:
    '''
    字段与指标关联关系实体转换工具
    '''

    # 静态方法：Model（数据库行） -> Entity（业务对象）
    @staticmethod
    def to_entity(model: ColumnMetricModel) -> ColumnMetricEntity:
        return ColumnMetricEntity(
            # 字段 id
            column_id=model.column_id,
            # 指标 id
            metric_id=model.metric_id,
        )

    # 静态方法：Entity（业务对象） -> Model（数据库行）
    @staticmethod
    def to_model(entity: ColumnMetricEntity) -> ColumnMetricModel:
        # 把实体拆成字典后用 ** 解包，作为 Model 的构造参数
        return ColumnMetricModel(**asdict(entity))
