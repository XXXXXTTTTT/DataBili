import asyncio
import aiohttp
import json
from typing import List, Dict
import logging
import time
import writetosql
from pathlib import Path
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

headers = {
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
}

# API基础URL
BASE_URL = "https://api.bilibili.com/x/web-interface/popular?"
TAG_URL = "https://api.bilibili.com/x/tag/archive/tags?"  # 假设的标签API地址
TIMEOUT = 10  # 请求超时秒数
MAX_CONCURRENT = 5  # 最大并发数
REQUEST_INTERVAL = 0.7  # 每次请求间隔秒数
RETRY_ATTEMPTS = 5  # 重试次数

async def fetch_page(session: aiohttp.ClientSession, page: int, ps: int = 50, retries: int = RETRY_ATTEMPTS) -> List[Dict]:
    """
    获取单页数据
    """
    params = {'pn': page, 'ps': ps}
    for attempt in range(retries):
        try:
            async with session.get(BASE_URL, params=params, timeout=TIMEOUT, headers=headers) as response:
                if response.status in (403, 412, 429):
                    logger.error(f"Page {page} 被平台拒绝（HTTP {response.status}），停止重试")
                    return []
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == 0 and data.get('data', {}).get('list'):
                        return data['data']['list']
                    else:
                        logger.error(f"Page {page} failed with code {data.get('code')}，停止该页请求")
                        return []
                else:
                    logger.warning(f"Page {page} attempt {attempt + 1} failed with status {response.status}")
        except aiohttp.ClientError as e:
            logger.warning(f"Page {page} attempt {attempt + 1} error: {e}")
        await asyncio.sleep(3 * REQUEST_INTERVAL)
    logger.error(f"Page {page} failed after {retries} attempts")
    return []

async def fetch_all_pages(total_items: int = 500, ps: int = 50) -> List[Dict]:
    """
    获取所有页数据，控制并发速率
    """
    total_pages = (total_items + ps - 1) // ps  # 计算总页数
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)  # 限制最大并发数
    results = []

    async def fetch_with_semaphore(page: int) -> List[Dict]:
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                data = await fetch_page(session, page, ps)
                await asyncio.sleep(REQUEST_INTERVAL)  # 控制请求速率
                return data

    tasks = [fetch_with_semaphore(page) for page in range(1, total_pages + 1)]
    for future in asyncio.as_completed(tasks):
        page_data = await future
        results.extend(page_data)
        logger.info(f"Fetched {len(page_data)} items from page, total: {len(results)}")

    return results[:total_items]  # 确保不超过指定数量

async def fetch_tags(session: aiohttp.ClientSession, aid: str, retries: int = RETRY_ATTEMPTS) -> List[str]:
    """
    异步获取视频标签
    """
    params = {"aid": aid}
    for attempt in range(retries):
        try:
            async with session.get(TAG_URL, params=params, headers=headers, timeout=TIMEOUT) as response:
                if response.status == 200:
                    tag_text = await response.json()
                    if tag_text.get("code", -1) != 0:
                        logger.error(f"Failed to get tags for aid {aid}")
                        return []
                    tags_list = tag_text.get("data", [])
                    tag_name_list = [tag_d.get("tag_name", "") for tag_d in tags_list]
                    return tag_name_list
                else:
                    logger.warning(f"Tag fetch for aid {aid} attempt {attempt + 1} failed with status {response.status}")
        except aiohttp.ClientError as e:
            logger.warning(f"Tag fetch for aid {aid} attempt {attempt + 1} error: {e}")
        await asyncio.sleep(REQUEST_INTERVAL)
    logger.error(f"Tag fetch for aid {aid} failed after {retries} attempts")
    return []

async def add_tags(videos_list: List[Dict]):

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)  # 限制最大并发数

    async def fetch_tags_for_video(i: int, d: Dict):
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                aid = str(d["aid"])  # 确保aid是字符串
                tag_names = await fetch_tags(session, aid)
                d["tags"] = tag_names
                logger.info(f"{i+1}-->successful")
                await asyncio.sleep(REQUEST_INTERVAL)  # 控制请求速率

    tasks = [fetch_tags_for_video(i, d) for i, d in enumerate(videos_list)]
    await asyncio.gather(*tasks)
    
    
async def fetch_online_count(session: aiohttp.ClientSession, bvid: str, cid: str, retries: int = RETRY_ATTEMPTS) -> Dict[str, str]:
    """
    异步获取视频实时在线人数
    """
    url = "https://api.bilibili.com/x/player/online/total"
    params = {"bvid": bvid, "cid": cid}
    
    for attempt in range(retries):
        try:
            async with session.get(url, params=params, headers=headers, timeout=TIMEOUT) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 0 and "data" in data:
                        return {
                            "real_time_all": data["data"].get("total", "0"),
                            "real_time_web": data["data"].get("count", "0")
                        }
                    else:
                        logger.error(f"Failed to get online count for bvid {bvid}, cid {cid}")
                        return {"real_time_all": "0", "real_time_web": "0"}
                else:
                    logger.warning(f"Online count fetch for bvid {bvid} attempt {attempt + 1} failed with status {response.status}")
        except aiohttp.ClientError as e:
            logger.warning(f"Online count fetch for bvid {bvid} attempt {attempt + 1} error: {e}")
        await asyncio.sleep(REQUEST_INTERVAL)
    
    logger.error(f"Online count fetch for bvid {bvid} failed after {retries} attempts")
    return {"real_time_all": "0", "real_time_web": "0"}


async def add_real_time_people(videos_list: List[Dict]):
    """
    为视频列表添加实时在线人数信息
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)  # 限制最大并发数

    async def fetch_online_for_video(i: int, d: Dict):
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                bvid = d.get("bvid", "")
                cid = d.get("cid", "")
                
                if not bvid or not cid:
                    logger.warning(f"Missing bvid or cid for video {i+1}")
                    d["real_time_all"] = "0"
                    d["real_time_web"] = "0"
                    return
                
                online_data = await fetch_online_count(session, bvid, str(cid))
                d.update(online_data)
                logger.info(f"Online count {i+1}-->successful")
                await asyncio.sleep(REQUEST_INTERVAL)  # 控制请求速率

    tasks = [fetch_online_for_video(i, d) for i, d in enumerate(videos_list)]
    await asyncio.gather(*tasks)
    
def process_json_data(data: List[Dict]) -> List[Dict]:
    keys_to_extract = [
        'aid', 'videos', 'tid', 'tname', 'copyright', 'pic', 'title', 'pubdate',
        'ctime', 'desc', 'state', 'duration', 'mission_id', 'pub_location',
        'tnamev2', 'pid_name_v2', 'short_link_v2', 'dynamic', 'bvid', 'cid'  # 添加 bvid 和 cid
    ]
    stat_keys = [
        'view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 
        'now_rank', 'his_rank', 'like', 'dislike', 'vt', 'vv', 'fav_g', 'like_g'
    ]
    result = {}
    for key in keys_to_extract:
        if key in data:
            result[key] = data[key]
    if 'stat' in data:
        for stat_key in stat_keys:
            if stat_key in data['stat']:
                result[f'stat_{stat_key}'] = data['stat'][stat_key]
    if 'owner' in data:
        result['owner_mid'] = data['owner']['mid']
        result['owner_name'] = data['owner']['name']
        result['owner_face'] = data['owner']['face']
    if 'tags' in data:
        result['tags'] = ','.join(data['tags'])
    
    # 添加实时在线人数
    if 'real_time_all' in data:
        result['real_time_all'] = data['real_time_all']
    if 'real_time_web' in data:
        result['real_time_web'] = data['real_time_web']
    
    return result

def process_data(data:List[Dict]) -> List[Dict]:
    res = []
    for d in data:
        res.append(process_json_data(d))
    return res

async def record():
    logger.info("Starting to fetch Bilibili popular videos")
    timestamp = time.time()
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    
    hot_videos_dict = {}
    hot_videos_dict["timestamp"] = timestamp
    hot_videos_dict["formatted_time"] = formatted_time
    
    videos_list = await fetch_all_pages(total_items=500, ps=50)
    await add_tags(videos_list)
    await add_real_time_people(videos_list)  # 添加这一行
    videos_list = process_data(videos_list)
    
    hot_videos_dict["data"] = videos_list
    
    output_path = Path(__file__).resolve().parents[1] / 'bilibili_popular.json'
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(hot_videos_dict, f, ensure_ascii=False, indent=2)
    logger.info(f"Successfully fetched {len(videos_list)} videos")
    
    if os.getenv("CRAWLER_SKIP_DB", "false").lower() == "true":
        logger.info("CRAWLER_SKIP_DB=true，跳过数据库写入")
        return
    success = writetosql.insert_bilibili_data(data=hot_videos_dict)
    if success:
        print("=======success to insert into database=======")
    else:
        print("=======failed to insert into database=======")
    

async def main(loop:bool=False,interval:int=1800):
    await record()
    while loop:
        await asyncio.sleep(interval)
        await record()
        
if __name__ == "__main__":
    asyncio.run(main())
