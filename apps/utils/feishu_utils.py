#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from config.settings import Config
from apps.utils.redis_utils import redis_client
from sanic.log import logger
from asyncio import Lock
import uuid
import httpx
import time
import json


# Token 管理器
class TokenManager:
    def __init__(self):
        self.local_token = None  # 本地缓存的 Token
        self.local_expires_at = 0  # 本地缓存的 Token 过期时间
        self.lock = Lock()  # 异步锁

    async def get_feishu_access_token(self):
        """
        获取飞书 API 的访问令牌。
        如果本地缓存有效，则直接返回；否则从 Redis 或飞书 API 获取并缓存。
        """
        # 检查本地缓存是否有效
        if self.local_token and time.time() < self.local_expires_at - 60:  # 提前60秒刷新
            return self.local_token

        # 加锁，避免并发刷新
        async with self.lock:
            # 再次检查，防止其他协程已经刷新
            if self.local_token and time.time() < self.local_expires_at - 60:
                return self.local_token

            # 从 Redis 获取缓存的 Token 和过期时间
            cached_token = await redis_client.get(Config.FEISHU_TOKEN_KEY)
            cached_expire = await redis_client.get(Config.FEISHU_TOKEN_EXPIRE_KEY)

            if cached_token and cached_expire:
                cached_token = cached_token.decode("utf-8")
                cached_expire = float(cached_expire.decode("utf-8"))
                # 检查 Redis 中的 Token 是否有效
                if time.time() < cached_expire - 60:  # 提前60秒刷新
                    self.local_token = cached_token
                    self.local_expires_at = cached_expire
                    return cached_token

            # 如果 Redis 中没有有效的 Token，则从飞书 API 获取
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
            data = {"app_id": Config.FEISHU_APP_ID, "app_secret": Config.FEISHU_APP_SECRET}
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json=data)
                    if resp.status_code == 200:
                        token_data = resp.json()
                        token = token_data.get("tenant_access_token")
                        expire = token_data.get("expire", 0)  # 获取过期时间（秒）
                        if token and expire > 60:
                            # 计算过期时间戳
                            expires_at = time.time() + expire
                            # 缓存到 Redis
                            await redis_client.set(Config.FEISHU_TOKEN_KEY, token, ex=expire - 60)
                            await redis_client.set(Config.FEISHU_TOKEN_EXPIRE_KEY, expires_at, ex=expire - 60)
                            # 更新本地缓存
                            self.local_token = token
                            self.local_expires_at = expires_at
                            return token
                        else:
                            logger.error("Invalid token data received from Feishu API")
                            return None
                    else:
                        logger.error(f"Failed to get Feishu access token: {resp.status_code}, {resp.text}")
                        return None
            except Exception as e:
                logger.error(f"Error while fetching Feishu access token: {e}")
                return None

# 初始化 TokenManager
token_manager = TokenManager()


# 初始化消息卡片2.0(不直接发送)
async def send_initial_card():
    """
    调用飞书 API 创建卡片实体，并返回生成的 card_id
    """
    access_token = await token_manager.get_feishu_access_token()
    if not access_token:
        return None

    # 卡片数据
    card_data = {
        "type": "card_json",
        "data": json.dumps({
            "schema": "2.0",
            "header": {
                "title": {
                    "content": "AI 助手",
                    "tag": "plain_text"
                }
            },
            "config": {
                "streaming_mode": True,  # 启用流式模式,
                "summary": {
                    "content": "[正在处理中...]"  # 卡片在生成内容时展示的摘要。
                },
                "streaming_config": {
                    # 流式更新频率，单位：ms
                    "print_frequency_ms": {
                        "default": 50
                    },
                    # 流式更新步长，单位：字符数
                    "print_step": {
                        "default": 20
                    },
                    # 流式更新策略，枚举值，可取：fast / delay
                    "print_strategy": "fast"
                }
            },
            "body": {
                "elements": [
                    {
                        "tag": "markdown",
                        "content": "正在思考中...",
                        "element_id": "markdown_1"  # 设置唯一的 element_id
                    }
                ]
            }
        })
    }

    # 请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        async with httpx.AsyncClient() as client:
            # 调用创建卡片实体接口
            resp = await client.post(
                "https://open.feishu.cn/open-apis/cardkit/v1/cards/",
                headers=headers,
                json=card_data
            )
            if resp.status_code == 200:
                # 提取 card_id
                card_id = resp.json().get("data", {}).get("card_id")
                if card_id:
                    # 确保 card_id 不超过 20 字符
                    return str(card_id)[:20]
                else:
                    logger.error("Failed to get card_id from response")
                    return None
            else:
                logger.error(f"Failed to create card: {resp.status_code}, {resp.text}")
                return None
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        return None

# 发送卡片消息
async def send_card_message(receive_id, card_id):
    """
    调用飞书 API 发送卡片消息
    :param receive_id: 接收消息的用户或群组 ID（必须是当前应用的 open_id）
    :param card_id: 卡片实体 ID
    """
    access_token = await token_manager.get_feishu_access_token()
    if not access_token:
        return None

    # 请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    # 请求体
    payload = {
        "receive_id": receive_id,
        "msg_type": "interactive",
        "content": json.dumps({
            "type": "card",
            "data": {
                "card_id": card_id
            }
        })
    }

    try:
        async with httpx.AsyncClient() as client:
            # 调用飞书 API 发送消息
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
                headers=headers,
                json=payload
            )
            if resp.status_code == 200:
                message_id = resp.json().get("data", {}).get("message_id")
                if message_id:
                    return message_id
                else:
                    logger.error("Failed to get message_id from response")
                    return None
            else:
                logger.error(f"Failed to send card message: {resp.status_code}, {resp.text}")
                return None
    except Exception as e:
        logger.error(f"Error sending card message: {e}")
        return None

# 流式更新卡片内容
async def update_card_content(card_id, element_id, content, sequence=1):
    """
    更新卡片内容
    :param card_id: 卡片 ID
    :param element_id: 元素 ID
    :param content: 更新的文本内容（必须是字符串）
    :param sequence: 序列号，用于控制更新顺序
    """
    access_token = await token_manager.get_feishu_access_token()
    if not access_token:
        return False

    # 请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    # 请求体
    payload = {
        "content": content,  # 必须是字符串
        "sequence": sequence,
        "uuid": str(uuid.uuid4())  # 动态生成唯一的 UUID
    }

    try:
        async with httpx.AsyncClient() as client:
            # 调用更新卡片内容接口
            resp = await client.put(
                f"https://open.feishu.cn/open-apis/cardkit/v1/cards/{card_id}/elements/{element_id}/content",
                headers=headers,
                json=payload
            )
            if resp.status_code == 200:
                return True
            else:
                logger.error(f"Failed to update card content: {resp.status_code}, {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Error updating card content: {e}")
        return False

# 关闭消息卡片流式更新
async def disable_streaming_mode(card_id, sequence):
    """
    异步关闭卡片的 streaming_mode
    :param card_id: 卡片 ID
    :return: 是否成功关闭
    """
    access_token = await token_manager.get_feishu_access_token()
    if not access_token:
        return False

    # 请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    # 请求体：关闭 streaming_mode
    payload = {
        "sequence": sequence,
        "settings": "{\"config\":{\"streaming_mode\":false,\"summary\": {\"content\": \"[回答完毕]\"}}}",
        "uuid": str(uuid.uuid4())  # 动态生成唯一的 UUID
    }

    try:
        async with httpx.AsyncClient() as client:
            # 调用更新卡片设置接口
            resp = await client.patch(
                f"https://open.feishu.cn/open-apis/cardkit/v1/cards/{card_id}/settings",
                headers=headers,
                json=payload
            )
            if resp.status_code == 200:
                return True
            else:
                logger.error(f"Failed to disable streaming mode: {resp.status_code}, {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Error disabling streaming mode: {e}")
        return False

