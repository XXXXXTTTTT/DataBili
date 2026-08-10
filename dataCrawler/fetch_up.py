import asyncio
import random
import json
import pymysql
from bilibili_api import user, video, Credential, request_settings
from bilibili_api.exceptions import ApiException
import tqdm
import os
from pathlib import Path
from config import credential_values, database_config
from up_state import classify_exception, is_retry_allowed, record_crawl_state


# ============ 全局配置 ==============
TIMEOUT = 10               # 每个请求的超时时间（秒）
MAX_CONCURRENT = 1         # 获取视频详情的最大并发数
REQUEST_INTERVAL = (120, 150) # 每个UID之间请求的 sleep 范围（秒）
INTERVAL = 5  # 每次视频请求间隔秒数
RETRY_ATTEMPTS = 5         # 每个请求最大重试次数
FORCE_SLEEP_EVERY = 5     # 每处理多少个UID就强制长休息
FORCE_SLEEP_DURATION = 60  # 强制休息的时间（秒）
MIN_FOLLOWERS = 2000       # 最小粉丝数过滤阈值
USE_CREDENTIAL, SESSDATA, BILI_JCT = credential_values()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Referer": "https://www.bilibili.com",
    "Origin": "https://www.bilibili.com",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
}


# request_settings.set_proxy("http://your-proxy.com")


#登入
if USE_CREDENTIAL and (not SESSDATA or not BILI_JCT):
    raise RuntimeError("BILI_USE_CREDENTIAL=true 时必须同时配置 BILI_SESSDATA 和 BILI_BILI_JCT")
credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT) if USE_CREDENTIAL else None

# 数据库配置

#远端
db_config = database_config()

# 数据库插入函数
def insert_into_mysql(data: dict):
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    sql = """
    INSERT INTO up_profile (
        uid, name, avatar_url, followers, total_videos, total_view, total_like, total_coin,
        total_favorite, total_share, total_comment, total_danmaku, total_duration,
        total_chargers, total_videos_count
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        avatar_url = VALUES(avatar_url),
        followers = VALUES(followers),
        total_videos = VALUES(total_videos),
        total_view = VALUES(total_view),
        total_like = VALUES(total_like),
        total_coin = VALUES(total_coin),
        total_favorite = VALUES(total_favorite),
        total_share = VALUES(total_share),
        total_comment = VALUES(total_comment),
        total_danmaku = VALUES(total_danmaku),
        total_duration = VALUES(total_duration),
        total_chargers = VALUES(total_chargers),
        total_videos_count = VALUES(total_videos_count)
    """

    cursor.execute(sql, (
        data.get("uid"),
        data.get("name", ""),
        data.get("avatar_url", ""),
        data.get("followers", 0),
        data.get("total_videos", 0),
        data.get("total_view", 0),
        data.get("total_like", 0),
        data.get("total_coin", 0),
        data.get("total_favorite", 0),
        data.get("total_share", 0),
        data.get("total_comment", 0),
        data.get("total_danmaku", 0),
        data.get("total_duration", 0),
        data.get("total_chargers", 0),
        data.get("total_videos_count", 0)
    ))

    connection.commit()
    cursor.close()
    connection.close()


def insert_partial_profile(data: dict):
    """仅更新已确认的基础资料，避免将缺失统计写成零。"""
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO up_profile (uid, name, avatar_url, followers)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name), avatar_url = VALUES(avatar_url),
                    followers = VALUES(followers)
                """,
                (data["uid"], data.get("name", ""), data.get("avatar_url", ""), data.get("followers")),
            )
        connection.commit()
    finally:
        connection.close()

# 生成随机 UID
#8263502
def generate_random_uid():
    #(min, max)
    return random.randint(1000000, 800000000)

#从.txt文件中批量爬取Up数据
def load_uids_from_txt(path: str):
    with open(path, "r", encoding="utf-8") as f:
        line = f.readline().strip()
        uids = [int(uid.strip()) for uid in line.split(",") if uid.strip().isdigit()]
    return uids


def get_api_error_code(exception: Exception):
    """统一读取 bilibili-api-python 的 API code 或 HTTP status。"""
    status = getattr(exception, "status", None)
    if status is not None:
        return status
    return getattr(exception, "code", None)

async def batch_crawl_from_uid_file(file_path):
    uids = load_uids_from_txt(file_path)
    print(f"📦 共读取 {len(uids)} 个 UID")

    for idx, uid in enumerate(uids):
        print(f"\n[{idx+1}/{len(uids)}] 处理 UID: {uid}")

        if not is_retry_allowed(uid):
            print(f"[冷却] UID {uid} 尚未到允许重试时间，跳过")
            continue

        while True:  # 重试循环
            try:
                data = await fetch_user_info(uid)
                if data:
                    print(f"✅ 成功抓取 UID: {uid}，粉丝数: {data['followers']}")
                    if data.get("_status") == "partial":
                        insert_partial_profile(data)
                    else:
                        insert_into_mysql(data)
                else:
                    print(f"⚠️ 跳过 UID: {uid}(无效、粉丝少、视频过多或无视频)")
                break
            except Exception as e:
                print(f"❌ UID失败: {uid} 失败，错误: {e}")
                break

                

        # 👇 请求间隔（随机抖动）
        delay = random.uniform(*REQUEST_INTERVAL)
        print(f"⏱️ 等待 {delay:.2f} 秒")
        await asyncio.sleep(delay)

        # 每 N 个强制暂停
        if (idx + 1) % FORCE_SLEEP_EVERY == 0:
            print(f"💤 强制休息 {FORCE_SLEEP_DURATION} 秒，防风控")
            await asyncio.sleep(FORCE_SLEEP_DURATION)


# 拉取视频列表
async def fetch_all_videos(u: user.User):
    MAX_VIDEOS = 5000  # 设置最大视频数量限制
    page = 1
    videos = []
    while True:
        result = await u.get_videos(pn=page, ps=20, order=user.VideoOrder.PUBDATE)
        await asyncio.sleep(INTERVAL)
        video_list = result.get('list', {}).get('vlist', [])
        if not video_list:
            break
        videos.extend(video_list)
        
        # 检查是否超过最大限制
        if len(videos) > MAX_VIDEOS:
            print(f"警告: 用户 {u.uid} 投稿视频超过 {MAX_VIDEOS} 条，停止爬取")
            return None  # 超过限制返回None
        
        page += 1
        

        
    return [v.get("bvid", "") for v in videos]

#并发获取视频数据
async def get_video_stats_concurrent(video_ids):
    stats = {
        "total_videos": len(video_ids),
        "total_view": 0,
        "total_like": 0,
        "total_coin": 0,
        "total_favorite": 0,
        "total_share": 0,
        "total_comment": 0,
        "total_danmaku": 0,
        "total_duration": 0,
        "total_chargers": 0,
        "total_videos_count": 0,
        "errors": []
    }

    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def fetch_one(vid):
        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with sem:
                    v = video.Video(bvid=vid, credential=credential)
                    info = await asyncio.wait_for(v.get_info(), timeout=TIMEOUT)
                    stat = info.get("stat", {})
                    return {
                        "view": stat.get("view", 0),
                        "like": stat.get("like", 0),
                        "coin": stat.get("coin", 0),
                        "favorite": stat.get("favorite", 0),
                        "share": stat.get("share", 0),
                        "comment": stat.get("reply", 0),
                        "danmaku": stat.get("danmaku", 0),
                        "duration": info.get("duration", 0),
                        "videos_count": info.get("videos", 0)
                    }
            except Exception as e:
                await asyncio.sleep(1 + attempt)
        stats["errors"].append({"bvid": vid, "error": "重试失败"})
        return {}

    tasks = [fetch_one(vid) for vid in video_ids]
    results = await asyncio.gather(*tasks)

    for r in results:
        stats["total_view"] += r.get("view", 0)
        stats["total_like"] += r.get("like", 0)
        stats["total_coin"] += r.get("coin", 0)
        stats["total_favorite"] += r.get("favorite", 0)
        stats["total_share"] += r.get("share", 0)
        stats["total_comment"] += r.get("comment", 0)
        stats["total_danmaku"] += r.get("danmaku", 0)
        stats["total_duration"] += r.get("duration", 0)
        stats["total_videos_count"] += r.get("videos_count", 0)

    return stats

#获取用户索引
async def fetch_user_info(uid: int):
    from bilibili_api import user

    u = user.User(uid=uid, credential=credential)
    res = {}
    while True: 
        try:
            relation = await u.get_relation_info()
            info = await u.get_user_info()
            followers = relation.get("follower", 0)

            if followers < MIN_FOLLOWERS:
                return None

            res["uid"] = uid
            res["followers"] = followers
            res["name"] = info.get("name", "")
            res["avatar_url"] = info.get("face", "")

            try:
                bvids = await fetch_all_videos(u)
            except Exception as exc:
                status, error_code = classify_exception(exc)
                if status == "risk_blocked":
                    record_crawl_state(uid, status, "bilibili_api", error_code, str(exc))
                    res["_status"] = "partial"
                    print(f"[风控] UID {uid} 视频列表被拒绝（HTTP {error_code}），保留基础资料")
                    return res
                raise
            if not bvids:
                record_crawl_state(uid, "partial", "bilibili_api", None, "视频列表为空")
                return None
            stats = await get_video_stats_concurrent(bvids)
            res.update(stats)
            record_crawl_state(uid, "success", "bilibili_api")
            return res
        except ApiException as api_exc:  # 专门捕获API异常
            error_code = get_api_error_code(api_exc)
            error_message = getattr(api_exc, "msg", str(api_exc))
            if error_code == -404:
                print(f"[跳过] UID {uid} 不存在(404错误),跳过处理")
                return None  # 直接返回None跳过用户
            elif error_code in (403, 412, 429):
                record_crawl_state(uid, "risk_blocked", "bilibili_api", error_code, error_message)
                raise RuntimeError(f"UID {uid} 请求被平台拒绝（HTTP {error_code}），已停止，不执行绕过") from api_exc
            else:
                record_crawl_state(uid, "provider_error", "bilibili_api", error_code, error_message)
                print(f"[API错误] UID {uid} 获取失败: 代码{error_code}, 信息: {error_message}")
                raise RuntimeError(f"API 请求失败，code={error_code}") from api_exc
        except Exception as e:
            status, error_code = classify_exception(e)
            record_crawl_state(uid, status, "bilibili_api", error_code, str(e))
            print(f"[错误] UID {uid} 获取失败: {e}")
            raise RuntimeError("获取用户信息失败，已停止重试") from e



if __name__ == '__main__':
    asyncio.run(batch_crawl_from_uid_file(str(Path(__file__).resolve().parent / "upUid2.txt")))
    # asyncio.run(random_crawler_loop())
