from apps.utils.handle_utils import handle_feishu_message
from sanic import Blueprint,response
from .models import EVENT_MODEL
from sanic_ext import openapi
import asyncio
from sanic.log import logger

# 定义蓝图和路由前缀
chat = Blueprint("chat", url_prefix='/chat')

@chat.route('/feishu_webhook', methods=["POST"])
@openapi.summary("飞书事件订阅webhook")
@openapi.body({"application/json": EVENT_MODEL}, description="飞书事件订阅webhook", required=True)
async def feishu_webhook(request):
    try:
        data = request.json
        challenge = data.get("challenge")
        asyncio.create_task(handle_feishu_message(data))
        return response.json({"code": 0, "msg": "success", "challenge": challenge, "data": data})
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return response.json({"code": 500, "msg": "internal server error"}, status=500)
