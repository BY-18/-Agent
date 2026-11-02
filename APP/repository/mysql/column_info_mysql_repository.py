# 从 dataclasses 导入 asdict：把实体拆成字典，供批量 update 使用
from dataclasses import asdict

# 导入 update 构造函数（拼装 UPDATE 语句）与 text（把原生 SQL 字符串包装成可执行语句）
from sqlalchemy import update, text
# 导入异步会话类型，仅用于类型标注
from sqlalchemy.ext.asyncio import AsyncSession

# 导入字段信息业务实体
from APP.entity.column_info_entity import ColumnInfoEntity
# 导入实体 <-> 模型 的转换工具
from APP.mapper.column_info_mapper import ColumnInfoMapper
# 导入字段信息数据模型（映射 t_column_info 表）
from APP.model.column_info_model import ColumnInfoModel
# 导入 JSON 字段解析工具：把数据库里存成字符串的 alias / examples 还原成 list
from APP.utils.json_parser_util import parse_json_field


# 字段信息的 MySQL 数据交互层：封装对 t_column_info 表的查、增、批量改
class ColumnInfoMySqlRepository:
    # 构造方法：注入一个数据库会话
    def __init__(self,session:AsyncSession):
        #设置为私有的session会话
        self.session = session

    # 按主键 id（格式“表名.字段名”）查询字段信息，查不到返回 None
    async def get_column_info_by_id(self,id:str):
        # session.get 按主键取单行，第一个参数是模型类，第二个参数是主键值
        result :ColumnInfoModel = await  self.session.get(ColumnInfoModel,id)
        # 不存在时返回 None，供上层判断走新增还是更新
        if result is None:
            return None
        # 存在则把数据库模型转换成业务实体返回
        return ColumnInfoMapper.to_entity(result)

    # 新增单条字段信息（仅加入会话，需上层 commit 才真正落库）
    async def add_column_info(self,column_info:ColumnInfoEntity):
        await self.session.add(ColumnInfoMapper.to_model(column_info))

    # 批量新增字段信息
    async def batch_add_column_infos(self,column_infos:list[ColumnInfoEntity]):
        # add_all 一次性把多个模型对象加入会话，提交时合并为批量 INSERT
        self.session.add_all([ColumnInfoMapper.to_model(column_info) for column_info in column_infos])

    # 更新单条字段信息（只更新 name / role / description 三列）
    async def update_column_info(self,column_info:ColumnInfoEntity):
        # where 按主键定位，values 指定要修改的列
        stmt = (update(ColumnInfoModel).where(ColumnInfoModel.id == column_info.id)
                .values(
                    # 新的字段名
                    name=column_info.name,
                    # 新的字段角色（主键/外键/度量/维度）
                    role=column_info.role,
                    # 新的字段描述
                    description=column_info.description,
                )
        )
        # 执行 UPDATE 语句
        await  self.session.execute(stmt)

    # 批量更新字段信息
    async def batch_update_column_infos(self,column_infos:list[ColumnInfoEntity]):
        # 构造不带 where 的 UPDATE，SQLAlchemy 会按主键逐条匹配并更新（executemany）
        stmt = update(ColumnInfoModel)
        # 把实体列表转成字典列表，作为 executemany 的参数
        column = [asdict(column_info) for column_info in column_infos]
        # for column_info in column_infos:
        await  self.session.execute(stmt, column)

    # 查询某张表的所有主键 / 外键字段
    # 用途：生成 SQL 时，JOIN 需要知道表之间靠哪些字段关联，所以主外键要额外补全
    async  def get_key_by_table_id(self,table_id:str)->list[ColumnInfoEntity]:
        # 原生 SQL：按表名筛出 role 为主键或外键的字段
        sql ="""
        select * from t_column_info
        where table_id = :table_id
        and role in ('primary_key','foreign_key')
        """
        # 用命名参数 :table_id 传值，避免 SQL 注入
        result = await self.session.execute(text(sql),{"table_id":table_id})
        # mappings() 让每行可以按列名访问，fetchall() 取出全部结果
        rows = result.mappings().fetchall()
        # 收集转换后的实体
        entities = []
        # 逐行处理
        for row in rows:
            # 把结果行（RowMapping）转成普通字典，便于 ** 解包
            data = dict(row)
            # alias 在库里是 JSON 字符串，需要先解析成 list
            data["alias"] = parse_json_field(data.get("alias"))
            # examples 同理，解析成 list
            data["examples"] = parse_json_field(data.get("examples"))
            # 用 ** 解包构造业务实体并加入结果列表
            entities.append(ColumnInfoEntity(**data))
        # 返回该表的主外键字段列表
        return entities

