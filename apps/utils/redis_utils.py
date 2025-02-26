# _*_ coding:utf-8 _*_
from config.settings import Config
import redis.asyncio as redis

REDIS_URL = f"redis://{Config.R_HOST}:{Config.R_PORT}/{Config.R_DB}"
redis_client = redis.from_url(REDIS_URL)