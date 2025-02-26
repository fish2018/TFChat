from sanic_ext import openapi

'''
给飞书机器人发送消息，webhook会收到订阅事件post数据
{
    "schema": "2.0",
    "header": {
        "event_id": "1ff6af4bae3d16ff3b398c581bc81470",
        "token": "Q7uwJOqiFbdIbQM40rfqtcMLSlkxtyBq",
        "create_time": "1740482057819",
        "event_type": "im.message.receive_v1",
        "tenant_key": "2e0a973f764f1657",
        "app_id": "cli_a537fd87b07f100d"
    },
    "event": {
        "message": {
            "chat_id": "oc_f1e84d85c0bd1653e434df63589c7792",
            "chat_type": "p2p",
            "content": "{\"text\":\"你好\"}",
            "create_time": "1740482057539",
            "message_id": "om_482a57331e3ad57a3085915f94858aea",
            "message_type": "text",
            "update_time": "1740482057539"
        },
        "sender": {
            "sender_id": {
                "open_id": "ou_3837491bf933d4249e5f1c6bae4dcf4b",
                "union_id": "on_b7176339cdb740298373f8fc4eae7c75",
                "user_id": "8a3ebe1g"
            },
            "sender_type": "user",
            "tenant_key": "2e0a974e764f1657"
        }
    }
}
'''

class HEADER:
    event_id: openapi.String(default="1ff6af4bae3d16ff3b398c581bc81470")
    token: openapi.String(default="Q7uwJOqiFbdIbQM40rfqtcMLSlkxtyBq")
    create_time: openapi.String(default="1740482057819")
    event_type: openapi.String(default="message")
    tenant_key: openapi.String(default="2e0a973f764f1657")
    app_id: openapi.String(default="cli_a537fd87b07f100d")

class MESSAGE:
    chat_id: openapi.String(default="oc_f1e84d85c8bd1653e434df63589c7792")
    chat_type: openapi.String(default="p2p")
    content: openapi.String(default="{\"text\":\"你好\"}")
    create_time: openapi.String(default="1740482057539")
    message_id: openapi.String(default="om_482a57331e3ad57a3085915f94858aea")
    message_type: openapi.String(default="text")
    update_time: openapi.String(default="1740482057539")

class SENDER_ID:
    open_id: openapi.String(default="ou_3837491bf933d4249e5f1c6bae4dcf4b")
    union_id: openapi.String(default="on_b7176339cdb740298373f8fc4eae7c75")
    user_id: openapi.String(default="8a3ebe1g")

class SENDER:
    sender_id: SENDER_ID
    sender_type: openapi.String(default="user")
    tenant_key: openapi.String(default="2e0a974e764f1657")

class EVENT:
    message: MESSAGE
    sender: SENDER

class EVENT_MODEL:
    schema: openapi.String(default="2.0")
    header: HEADER
    event: EVENT





