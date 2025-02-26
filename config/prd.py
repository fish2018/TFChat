# -*- coding: utf-8 -*-

class Config:
    """生产环境配置"""
    # REDIS
    # REDIS_CON = "redis://127.0.0.1:6379/0"
    R_HOST = "127.0.0.1"
    R_PORT = "6379"
    R_DB = 0
    R_PWD = ''

    # 腾讯 AI 接口配置
    TENCENT_AI_URL = "https://wss.lke.cloud.tencent.com/v1/qbot/chat/sse"
    BOT_APP_KEY = "xxx"
    STREAMING_THROTTLE = 1

    # 飞书 API 配置
    FEISHU_API_URL = "https://open.feishu.cn/open-apis/message/v4/send/"
    FEISHU_CARD_UPDATE_URL = "https://open.feishu.cn/open-apis/cardkit/v1/cards/{card_id}/elements/{element_id}/content"
    FEISHU_APP_ID = "xxx"
    FEISHU_APP_SECRET = "xxx"

    # Redis 中存储 token 的键名
    FEISHU_TOKEN_KEY = "feishu_tenant_access_token"
    FEISHU_TOKEN_EXPIRE_KEY = "feishu_token_expire"
