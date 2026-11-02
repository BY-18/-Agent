import re

from langgraph.runtime import Runtime

from APP.agent.agent_runtime_context import AgentRuntimeContext
from APP.agent.agent_state import AgentState
from APP.utils.log_util import logger

# 匹配 markdown 代码围栏（```sql、``` 等），模型输出经常带上
_FENCE_PATTERN = re.compile(r'```[a-zA-Z+]*')

# 只读查询允许的语句前缀
_ALLOWED_PREFIX = ('select', 'with')

# 写操作与危险语法黑名单：命中即拒绝执行
# 说明：这里匹配的是“去掉注释和字符串字面量后的语句骨架”，
#      所以 'update_time' 这类字段名不会被误判（\b 与下划线之间不构成词边界）
_FORBIDDEN_PATTERN = re.compile(
    r'\b(insert|update|delete|drop|alter|create|truncate|rename|replace|grant|revoke|call|handler)\b'
    r'|\binto\s+(out|dump)file\b'
    r'|\bfor\s+update\b'
    r'|\block\s+in\s+share\s+mode\b',
    re.IGNORECASE,
)


def _scan(sql: str, keep_literals: bool, stop_at_semicolon: bool) -> str:
    """
    单遍扫描 SQL 文本：
        keep_literals     —— True 保留字符串字面量；False 把字面量内容抹掉，只留语句骨架
        stop_at_semicolon —— True 遇到引号外的第一个分号就停止（只取第一条语句）
    同时会去掉 -- / # 行注释和 /* */ 块注释。
    """
    out: list[str] = []
    i, n = 0, len(sql)
    quote = ''

    while i < n:
        ch = sql[i]

        # 处于字符串内部：只在遇到同类引号时结束
        if quote:
            if ch == quote:
                # '' 是 SQL 里的转义写法，跳过这两个字符但保留引号
                if quote == "'" and i + 1 < n and sql[i + 1] == "'":
                    if keep_literals:
                        out.append("''")
                    i += 2
                    continue
                quote = ''
                if keep_literals:
                    out.append(ch)
                i += 1
                continue
            if keep_literals:
                out.append(ch)
            i += 1
            continue

        # 字符串开始（' " 以及 MySQL 的反引号标识符）
        if ch in ("'", '"', '`'):
            quote = ch
            if keep_literals:
                out.append(ch)
            i += 1
            continue

        # -- 行注释
        if ch == '-' and i + 1 < n and sql[i + 1] == '-':
            i += 2
            while i < n and sql[i] != '\n':
                i += 1
            continue

        # # 行注释（MySQL 支持）
        if ch == '#':
            while i < n and sql[i] != '\n':
                i += 1
            continue

        # /* */ 块注释
        if ch == '/' and i + 1 < n and sql[i + 1] == '*':
            i += 2
            while i + 1 < n and not (sql[i] == '*' and sql[i + 1] == '/'):
                i += 1
            i += 2
            continue

        # 第一条语句结束
        if stop_at_semicolon and ch == ';':
            break

        out.append(ch)
        i += 1

    return ''.join(out)


def clean_sql(sql: str) -> str:
    """
    清洗大模型返回的 SQL：
        1. 去掉 markdown 代码围栏
        2. 去掉注释
        3. 只保留第一条语句（引号内的分号不会被误切）
        4. 去掉首尾空白和结尾分号
    """
    # 模型可能返回 None，统一转成字符串
    text = (sql or '').strip()
    # 去掉 ```sql / ``` 这类围栏标记
    text = _FENCE_PATTERN.sub('', text).strip()
    # 去注释 + 截取第一条语句
    text = _scan(text, keep_literals=True, stop_at_semicolon=True)
    return text.strip().rstrip(';').strip()


def ensure_readonly_sql(sql: str) -> None:
    """校验 SQL 是单条只读查询，不满足时直接抛异常"""
    # 只保留语句骨架，避免字符串/注释里的关键字造成误判
    skeleton = _scan(sql, keep_literals=False, stop_at_semicolon=True).strip().lower()
    if not skeleton.startswith(_ALLOWED_PREFIX):
        raise ValueError(f'生成的语句不是查询语句，已拒绝执行：{sql[:120]}')

    matched = _FORBIDDEN_PATTERN.search(skeleton)
    if matched:
        raise ValueError(
            f'SQL 中包含写操作或危险语法“{matched.group(0)}”，已拒绝执行：{sql[:120]}'
        )


async def executeSQL(state:AgentState,runtime: Runtime[AgentRuntimeContext]):

    generate_sql  = state['generate_sql']
    # 从上下文中获取数据仓库交互层对象dw_mysql_repository
    dw_mysql_repository = runtime.context['dw_mysql_repository']

    # 清洗模型输出，去掉代码围栏与多余语句
    sql = clean_sql(generate_sql)
    if not sql:
        raise ValueError('大模型没有返回可执行的 SQL')

    # 只允许单条查询语句，避免模型生成写操作把数仓数据改坏
    ensure_readonly_sql(sql)

    logger.info('实际执行的sql语句为：{}', sql)
    result = await  dw_mysql_repository.execute_sql(sql)
    writer = runtime.stream_writer
    writer({'data':result})
    return {'result':result}
