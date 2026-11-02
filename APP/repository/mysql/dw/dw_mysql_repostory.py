import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# 表名/字段名只允许字母、数字、下划线，且不能以数字开头
_IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _check_identifier(name: str, label: str) -> str:
    """校验表名/字段名是合法标识符，避免把外部输入直接拼进 SQL"""
    if not isinstance(name, str) or not _IDENTIFIER_PATTERN.match(name):
        raise ValueError(f'非法的{label}：{name!r}')
    return name


class DwMysqlRepostory:
    def __init__(self,session:AsyncSession) :
        self.session = session

    async def get_column_type_by_name(self,table_name:str) :
        # 先用白名单校验表名，再用反引号包裹，避免 SQL 注入
        table_name = _check_identifier(table_name, '表名')
        sql = f'show columns from `{table_name}`'
        result = await  self.session.execute(text(sql))
        # 将结果数据转换为字典
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values(self,table_name:str,column_name:str,limit: int = 5) :
        table_name = _check_identifier(table_name, '表名')
        column_name = _check_identifier(column_name, '字段名')
        # limit 必须是正整数，避免把非数字拼进 SQL
        limit = int(limit)
        if limit <= 0:
            raise ValueError(f'limit 必须为正整数：{limit}')
        sql = f'select distinct `{column_name}` from `{table_name}` limit {limit}'
        result = await self.session.execute(text(sql))
        return result.scalars().fetchall()

    async  def execute_sql(self,sql:str):
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]