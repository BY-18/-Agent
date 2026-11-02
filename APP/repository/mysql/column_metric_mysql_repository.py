# 从 dataclasses 导入 asdict：把实体拆成字典，供批量 update 使用
from dataclasses import asdict

# 导入 update 构造函数，用于拼装 UPDATE 语句
from sqlalchemy import update
# 导入异步会话类型，仅用于类型标注
from sqlalchemy.ext.asyncio import AsyncSession

# 导入字段-指标关联关系业务实体
from APP.entity.column_metric_entity import ColumnMetricEntity
# 导入实体 <-> 模型 的转换工具
from APP.mapper.column_metric_mapper import ColumnMetricMapper
# 导入关联关系数据模型
from APP.model.column_metric_model import ColumnMetricModel


# 字段-指标关联关系的 MySQL 数据交互层：封装对 t_metric_column 表的查与批量写
class ColumnMetricMySqlRepository:
    # 构造方法：注入一个数据库会话
    def __init__(self, session: AsyncSession):
        # 设置为私有的session会话
        self.session = session

    # 按“字段 id + 指标 id”复合主键查询关联关系，查不到返回 None
    async def get_column_metric_by_id(self, column_id: str, metric_id: str) -> ColumnMetricEntity | None:
        # 复合主键通过字典指定
        result: ColumnMetricModel = await self.session.get(
            ColumnMetricModel,
            # 字典的 key 必须与模型里的主键属性名一致
            {"column_id": column_id, "metric_id": metric_id}
        )
        # 不存在时返回 None，供上层判断走新增还是更新
        if result is None:
            return None
        # 存在则转换成业务实体返回
        return ColumnMetricMapper.to_entity(result)

    # 批量新增关联关系
    async def batch_insert_data(self, datas: list[ColumnMetricEntity]):
        # 一次性把多个模型对象加入会话，提交时合并为批量 INSERT
        self.session.add_all([ColumnMetricMapper.to_model(data) for data in datas])

    # 批量更新关联关系
    async def batch_update_data(self, datas: list[ColumnMetricEntity]):
        # 构造不带 where 的 UPDATE，按复合主键批量更新
        stmt = update(ColumnMetricModel)
        # 把实体列表转成字典列表，作为 executemany 的参数
        data_map = [asdict(data) for data in datas]
        # 执行批量更新
        await self.session.execute(stmt, data_map)
