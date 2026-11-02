# 从 sqlalchemy 异步扩展导入：
#   create_async_engine —— 创建异步数据库引擎
#   async_sessionmaker  —— 创建“会话工厂”，用它可以批量生成 AsyncSession 会话
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# 导入 quote_plus：用户名/密码里可能出现 @ : / 等字符，必须做 URL 编码，否则连接串会被拼坏
from urllib.parse import quote_plus

# 导入数据库连接配置类
from APP.config.APP_config import DBConfig


# MySQL 异步客户端封装：负责根据配置拼出连接串、创建引擎与会话工厂
class CustomMySqlClient:
    # 构造方法：保存配置，并预先算出连接串
    def __init__(self, config: DBConfig):
        # 把外部传入的数据库配置保存起来
        self._config = config
        # 调用 _get_url() 生成连接串（该方法定义在下方，方法名带下划线表示“内部使用”）
        self._url = self._get_url()

    # 拼装 SQLAlchemy 的异步 MySQL 连接串
    def _get_url(self):
        # 格式：方言+驱动://用户名:密码@主机:端口/库名
        # 注意：驱动名必须写成 mysql+asyncmy（中间不能有空格），否则 SQLAlchemy 无法解析方言
        user = quote_plus(self._config.user)
        password = quote_plus(self._config.password)
        return f"mysql+asyncmy://{user}:{password}@{self._config.host}:{self._config.port}/{self._config.database}"

    # 创建异步引擎，并基于它创建会话工厂，供业务层批量获取会话
    # 方法名统一为 get_session_factory（对外公开），调用处见 agent_graph.py、meta_service.py
    def get_session_factory(self):
        # 已经创建过就直接复用，避免同一配置重复建连接池
        if hasattr(self, 'sessionFactory'):
            return self.sessionFactory

        # 创建异步数据库引擎（相当于连接池的管理者），并保存为实例属性，
        # 否则引擎只被局部变量引用、外部无法 dispose，重复调用会泄漏连接池
        self.async_engine = create_async_engine(
            self._url,               # 数据库连接串
            pool_size=10,            # 连接池中常驻连接数
            max_overflow=20,         # 连接池满后允许临时超出的连接数（峰值可达 30）
            pool_recycle=3600,       # 连接回收时间（秒），避免 MySQL 主动断开空闲连接
        )

        # 创建会话工厂并保存为实例属性，后续用 sessionFactory() 即可得到新会话
        self.sessionFactory = async_sessionmaker(
            self.async_engine,       # 绑定上面的引擎
            expire_on_commit=False,  # 提交后不使对象过期，避免提交后访问属性再次触发查询
        )
        return self.sessionFactory

    # 关闭连接池：进程/脚本结束时必须调用，否则连接不会被释放
    async def dispose(self):
        if hasattr(self, 'async_engine'):
            await self.async_engine.dispose()
