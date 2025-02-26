# -*- coding: utf-8 -*-
from config import cf
from config.base import BaseConfig

class Config(BaseConfig):
    # REDIS
    # REDIS_CON = cf.REDIS_CON
    R_HOST = cf.R_HOST
    R_PORT = cf.R_PORT
    R_DB = cf.R_DB
    R_PWD = cf.R_PWD

    # 腾讯 AI 接口配置
    TENCENT_AI_URL = cf.TENCENT_AI_URL
    BOT_APP_KEY = cf.BOT_APP_KEY
    STREAMING_THROTTLE = cf.STREAMING_THROTTLE

    # 飞书 API 配置
    FEISHU_API_URL = cf.FEISHU_API_URL
    FEISHU_CARD_UPDATE_URL = cf.FEISHU_CARD_UPDATE_URL
    FEISHU_APP_ID = cf.FEISHU_APP_ID
    FEISHU_APP_SECRET = cf.FEISHU_APP_SECRET

    # Redis 中存储 token 的键名
    FEISHU_TOKEN_KEY = cf.FEISHU_TOKEN_KEY
    FEISHU_TOKEN_EXPIRE_KEY = cf.FEISHU_TOKEN_EXPIRE_KEY
