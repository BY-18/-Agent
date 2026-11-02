# 导入 jieba.analyse：jieba 的统计分析模块，提供基于 TF-IDF / TextRank 的关键词抽取
import jieba.analyse
# 导入 Runtime：LangGraph 注入给节点的运行时对象，可用来写流式输出、读取上下文
from langgraph.runtime import Runtime

# 导入运行时上下文类型
from APP.agent.agent_runtime_context import AgentRuntimeContext
# 导入全局状态类型
from APP.agent.agent_state import AgentState


# 关键词抽取节点：
#   入参 state  ：当前图状态（可读取 question）
#   入参 runtime：运行时对象（可获取 stream_writer、context 等）
#   返回值      ：只包含“需要更新”的字段，LangGraph 会把它合并回状态
async def keywordsExt(state: AgentState, runtime: Runtime[AgentRuntimeContext]):

    # 取出流式写出器：调用它即可把增量内容实时推给前端（配合 stream_mode='custom'）
    writer = runtime.stream_writer
    # 从状态中取出用户原始问题
    question = state["question"]

    # 使用jieba分词
    # uv add jieba
    # 根据自己定义的词性进行分词
    # allow_pos 用来限定只保留哪些词性的词，从而过滤掉无意义的虚词
    allow_pos = (
        "n",    # 名称
        "nr",   # 人名
        "ns",   # 地点
        "nt",   # 机构团体  学校  x公司
        "nz",   # 其他的专业名词  哈希算法  Unicode
        "v",    # 动词
        "vn",   # 名动词
        "a",    # 形容词
        "an",   # 名形词
        "eng",  # 英文
        "i",    # 成语
        "l",    # 常用固定短语
    )
    # 使用jieba的算法进行关键词的提取
    # extract_tags 默认基于 TF-IDF，返回按权重排序的关键词列表
    keywords = jieba.analyse.extract_tags(question, allowPOS=allow_pos)

    # 将原始的查询加入到关键词列表中
    # set 去重后转回 list，避免原句与抽出的词重复；原句也保留，便于全文检索兜底
    keywords = list(set(keywords + [question]))
    # 把最终关键词列表推给前端（流式）
    writer(keywords)
    # 返回需要写回状态的字段：LangGraph 会把 state['keywords'] 更新为该列表
    return {'keywords': keywords}
