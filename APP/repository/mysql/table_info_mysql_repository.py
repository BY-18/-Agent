# 从 dataclasses 导入 asdict：把实体拆成字典，供批量 update 使用
from dataclasses import asdict

# 导入 update 构造函数，用于拼装 UPDATE 语句
from sqlalchemy import update
# 导入异步会话类型，仅用于类型标注
from sqlalchemy.ext.asyncio import AsyncSession

# 导入表信息业务实体
from APP.entity.table_info_entity import TableInfoEntity
# 导入实体 <-> 模型 的转换工具
from APP.mapper.table_info_mapper import TableInfoMapper
# 导入表信息数据模型
from APP.model.table_info_model import TableInfoModel


# 表信息的 MySQL 数据交互层：封装对 t_table_info 表的增、改、查
class TableInfoMySqlRepository:
    # 构造方法：注入一个数据库会话
    def __init__(self, session: AsyncSession):
        # 设置为私有的session会话
        self.session = session

    # 按主键 id（表名）查询表信息，查不到返回 None
    async def get_table_info_by_id(self, id: str):
        # 根据主键查询单张表
        result: TableInfoModel = await self.session.get(TableInfoModel, id)
        # 不存在时返回 None，供上层判断走新增还是更新
        if result is None:
            return None
        # 存在则转换成业务实体返回
        return TableInfoMapper.to_entity(result)

    # 新增单条表信息（仅加入会话，需上层 commit 才真正落库）
    async def add_table_info(self, table_info: TableInfoEntity):
        await self.session.add(TableInfoMapper.to_model(table_info))

    # 批量新增表信息
    async def batch_add_table_infos(self, table_infos: list[TableInfoEntity]):
        # 一次性把多个模型对象加入会话，提交时合并为批量 INSERT
        self.session.add_all([TableInfoMapper.to_model(table_info) for table_info in table_infos])

    # 更新单条表信息（只更新 name / role / description 三列）
    async def update_table_info(self, table_info: TableInfoEntity):
        stmt = (update(TableInfoModel).where(TableInfoModel.id == table_info.id)
                .values(
                    # 新的表名
                    name=table_info.name,
                    # 新的表角色（fact / dim）
                    role=table_info.role,
                    # 新的表描述
                    description=table_info.description,
                )
                )
        # 执行 UPDATE 语句
        await self.session.execute(stmt)

    # 批量更新表信息
    async def batch_update_table_infos(self, table_infos: list[TableInfoEntity]):
        # 构造不带 where 的 UPDATE，按主键批量更新
        stmt = update(TableInfoModel)
        # 把实体列表转成字典列表，作为 executemany 的参数
        tables = [asdict(table_info) for table_info in table_infos]
        # 执行批量更新
        await self.session.execute(stmt, tables)
