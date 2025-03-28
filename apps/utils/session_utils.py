#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from apps.utils.redis_utils import redis_client
from datetime import datetime


async def get_or_create_session(user_id):
    timestamp = await redis_client.get(user_id)

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        await redis_client.set(user_id, timestamp, ex=600)  # Expires in 600 seconds
    else:
        timestamp = timestamp.decode('utf-8')

    session_id = f"{user_id}_{timestamp}"
    return session_id


# Async test function
async def test():
    async with redis_client:
        user_id = "user123"
        print("首次交互:", await get_or_create_session(user_id))
        print("后续交互（未过期）:", await get_or_create_session(user_id))
        # 过期删除key
        await redis_client.delete(user_id)
        print("后续交互（已过期）:", await get_or_create_session(user_id))


# Run the async code
if __name__ == "__main__":
    import asyncio
    asyncio.run(test())