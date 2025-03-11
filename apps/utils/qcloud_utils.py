# -*- coding=utf-8
from config.settings import Config
from apps.utils.feishu_utils import update_card_content, disable_streaming_mode
from sanic.log import logger
from collections import deque
import httpx
import json

# 调用腾讯云大模型知识引擎-应用接口-对话端接口(HTTP SSE)，并流式更新飞书消息卡片
async def call_tencent_ai_and_update_card(sender_id, card_id, element_id, content):
    data = {
        "content": content,
        "bot_app_key": Config.BOT_APP_KEY,
        "visitor_biz_id": sender_id,
        "session_id": sender_id,
        "streaming_throttle": Config.STREAMING_THROTTLE,
    }
    sequence = 1
    buffer = deque(maxlen=20)  # 使用 deque 作为缓冲区，最大长度为 20
    try:
        async with httpx.AsyncClient() as client:
            # 使用流式请求
            async with client.stream(
                "POST",
                Config.TENCENT_AI_URL,
                json=data,
                headers={"Accept": "text/event-stream"},
                timeout=20,  
            ) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to call Tencent AI API: {response.status_code}")
                    return

                # 手动处理流式响应
                async for chunk in response.aiter_text():
                    buffer.append(chunk)
                    # 如果缓冲区满了，则更新卡片
                    if len(buffer) == buffer.maxlen:
                        res = "".join(buffer)
                        data_start = res.find("data:") + len("data:")
                        data_end = res.find("\n\n", data_start)  # 查找下一个空行
                        if data_end == -1:
                            continue  # 如果未找到完整数据，继续等待
                        # 提取 data 部分
                        data_str = res[data_start:data_end].strip()
                        # 解析 data 部分为 JSON
                        event_data = json.loads(data_str)
                        event_type = event_data.get("type")
                        # 处理不同类型的事件
                        if event_type == "reply":
                            payload = event_data.get("payload", {})
                            if payload["is_llm_generated"]:
                                await update_card_content(card_id, element_id, payload["content"], sequence)
                        sequence += 1
                        buffer.clear()  # 清空缓冲区

                # 处理缓冲区中剩余的内容
                if buffer:
                    # 查找最后一个 "data:" 的位置
                    res = "".join(buffer)
                    data_start = res.rfind("data:") + len("data:")
                    data_end = res.find("\n\n", data_start)  # 查找下一个空行
                    if data_end == -1:
                        data_end = len(buffer)  # 如果没有找到空行，则取到字符串末尾
                    # 提取 data 部分
                    data_str = res[data_start:data_end].strip()
                    # 解析 data 部分为 JSON
                    event_data = json.loads(data_str)
                    event_type = event_data.get("type")
                    # 检查是否是最终内容
                    if event_type == "reply":
                        payload = event_data.get("payload", {})
                        logger.info(f'is_final: {payload.get("is_final", False)}  \n content: {payload["content"]}')
                        await update_card_content(card_id, element_id, payload["content"], sequence)
                        sequence += 1

                # 关闭流式更新
                await disable_streaming_mode(card_id, sequence)
    except Exception as e:
        logger.error(f"Error calling Tencent AI API: {e}")
