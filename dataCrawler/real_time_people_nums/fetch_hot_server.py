import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import aiohttp

CRAWLER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CRAWLER_DIR))

import fetch_hot
import writetosql_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def record(total_items: int = 500) -> bool:
    """采集一轮热门数据并写入前端使用的历史表。"""
    if total_items <= 0:
        raise ValueError("total_items 必须大于 0")

    timestamp = int(time.time())
    payload = {
        "timestamp": timestamp,
        "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
    }

    async with aiohttp.ClientSession() as session:
        videos = await fetch_hot.fetch_all_pages(total_items=total_items, ps=min(50, total_items), session=session)
        if not videos:
            logger.error("公开热门接口没有返回数据，本轮不写入数据库")
            return False
        await fetch_hot.add_tags(videos, session=session)
        await fetch_hot.add_real_time_people(videos, session=session)

    payload["data"] = fetch_hot.process_data(videos)
    output_path = CRAWLER_DIR / "real_time_people_nums" / "bilibili_popular_server.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    success = writetosql_server.insert_bilibili_data(data=payload)
    logger.info("本轮完成：获取 %s 条，数据库写入=%s", len(payload["data"]), success)
    return success


async def main(loop: bool = False, interval: int = 3600, total_items: int = 500):
    while True:
        await record(total_items=total_items)
        if not loop:
            return
        logger.info("下一轮将在 %s 秒后开始", interval)
        await asyncio.sleep(interval)


def parse_args():
    parser = argparse.ArgumentParser(description="每小时采集热门视频变化量")
    parser.add_argument("--items", type=int, default=500, help="每轮采集条数")
    parser.add_argument("--interval", type=int, default=3600, help="循环间隔秒数")
    parser.add_argument("--loop", action="store_true", help="持续循环运行")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(loop=args.loop, interval=args.interval, total_items=args.items))
