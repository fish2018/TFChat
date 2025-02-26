#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from apps.utils.feishu_utils import send_initial_card, send_card_message
from apps.utils.qcloud_utils import call_tencent_ai_and_update_card
from sanic.log import logger
import json

# 解析飞书 Webhook 请求数据
def parse_feishu_webhook(data):
    try:
        # 检查是否是订阅事件验证
        if "challenge" in data:
            return {"challenge": data["challenge"]}

        # 解析消息事件
        event = data.get("event", {})
        message = event.get("message", {})
        content = json.loads(message.get("content", "{}"))

        # 获取消息内容
        text = content.get("text", "")
        sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id")

        # 如果是卡片消息，解析卡片内容
        if "card" in content:
            card = content["card"]
            card_id = card.get("card_id")
            element_id = card.get("element_id")
            return {
                "text": text,
                "sender_id": sender_id,
                "card_id": card_id,
                "element_id": element_id,
            }

        return {
            "text": text,
            "sender_id": sender_id,
        }
    except Exception as e:
        logger.error(f"Error parsing webhook data: {e}")
        return None

# 处理飞书的消息
async def handle_feishu_message(message):
    parsed_data = parse_feishu_webhook(message)
    if not parsed_data:
        return

    sender_id = parsed_data["sender_id"]
    user_input = parsed_data["text"]

    # 初始化卡片
    card_id = await send_initial_card()
    if not card_id:
        logger.error("Failed to create initial card")
        return
    # 发送卡片消息
    message_id = await send_card_message(sender_id, card_id)
    if not message_id:
        logger.error("Failed to send card message")
        return

    # 调用腾讯 AI 接口并流式更新卡片
    await call_tencent_ai_and_update_card(sender_id, card_id, "markdown_1", user_input)