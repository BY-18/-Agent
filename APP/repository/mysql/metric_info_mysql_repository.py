# 从 dataclasses 导入 asdict：把实体拆成字典，供批量 update 使用
from dataclasses import asdict

# 导入 update 构造函数，用于拼装 UPDATE 语句
from sqlalchemy import update
# 导入异步会话类型，仅用于类型标注
from sqlalchemy.ext.asyncio import AsyncSession

# 导入指标信息业务实体
from APP.entity.metric_info_entity import MetricInfoEntity
# 导入实体 <-> 模型 的转换工具
from APP.mapper.metric_info_mapper import MetricInfoMapper
# 导入指标信息数据模型
from APP.model.metric_info_model import MetricInfoModel


# 指标信息的 MySQL 数据交互层：封装对 t_metric_info 表的查与批量写
class MetricInfoMySqlRepository:
    # 构造方法：注入一个数据库会话
    def __init__(self, session: AsyncSession):
        # 设置为私有的session会话
        self.session = session

    # 按主键 id（指标名）查询指标信息，查不到返回 None
    async def get_metric_info_by_id(self, id: str):
        # 根据主键查询单个指标
        result: MetricInfoModel = await self.session.get(MetricInfoModel, id)
        # 不存在时返回 None，供上层判断走新增还是更新
        if result is None:
            return None
        # 存在则转换成业务实体返回
        return MetricInfoMapper.to_entity(result)

    # 批量新增指标信息
    async def batch_insert_data(self, datas: list[MetricInfoEntity]):
        # 一次性把多个模型对象加入会话，提交时合并为批量 INSERT
        self.session.add_all([MetricInfoMapper.to_model(data) for data in datas])

    # 批量更新指标信息
    async def batch_update_data(self, datas: list[MetricInfoEntity]):
        # 构造不带 where 的 UPDATE，按主键批量更新
        stmt = update(MetricInfoModel)
        # 把实体列表转成字典列表，作为 executemany 的参数
        data_map = [asdict(data) for data in datas]
        # 执行批量更新
        await self.session.execute(stmt, data_map)
