import argparse
import asyncio
import json
from typing import Any

import aiohttp

BASE_URL = "https://api.bilibili.com/x/web-interface/popular"


async def check_public_api(timeout_seconds: int = 10) -> dict[str, Any]:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                BASE_URL,
                params={"pn": 1, "ps": 1},
                headers={"User-Agent": "DataBili-healthcheck/1.0"},
            ) as response:
                payload = await response.json(content_type=None)
                api_code = payload.get("code") if isinstance(payload, dict) else None
                return {
                    "ok": response.status == 200 and api_code == 0,
                    "http_status": response.status,
                    "api_code": api_code,
                    "message": payload.get("message", "") if isinstance(payload, dict) else "响应不是 JSON 对象",
                }
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        return {"ok": False, "http_status": None, "api_code": None, "message": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 B 站公开热门视频接口可达性")
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()
    result = asyncio.run(check_public_api(args.timeout))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
