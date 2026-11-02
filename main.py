"""项目命令行入口。

用法：
    python main.py init                 # 依据 config/meta_config.yaml 重建元数据知识库
    python main.py ask "你的问题"        # 对大模型生成并执行一次 SQL 查询
"""
import argparse
import asyncio

from APP.agent.agent_graph import run
from APP.script.meta_init import async_main as build_meta


def parse_args():
    parser = argparse.ArgumentParser(description='Text2SQL 命令行入口')
    sub_parsers = parser.add_subparsers(dest='command', required=True)

    sub_parsers.add_parser('init', help='重建元数据知识库（MySQL / Qdrant / Elasticsearch）')

    ask_parser = sub_parsers.add_parser('ask', help='用自然语言提问并执行生成的 SQL')
    ask_parser.add_argument('question', help='自然语言问题，例如：查询去年各地区第一季度的销售额')
    return parser.parse_args()


async def main_async(args):
    if args.command == 'init':
        await build_meta()
    else:
        result = await run(args.question)
        print(result)


def main():
    args = parse_args()
    try:
        asyncio.run(main_async(args))
    except Exception as exc:
        # 节点内部抛出的异常在这里统一兜底，避免直接抛出整段 traceback 给使用者
        print(f'执行失败：{type(exc).__name__}: {exc}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
