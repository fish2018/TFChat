# -*- coding=utf-8
from config.settings import Config
from apps.utils.feishu_utils import update_card_content, disable_streaming_mode
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.common_client import CommonClient
from qcloud_cos import CosConfig, CosS3Client
from tencentcloud.common import credential
from httpx_sse import aconnect_sse
from sanic.log import logger
import asyncio
import httpx
import json
import io

# 异步获取 COS 临时凭证，用于文件或图片上传。
async def get_cos_temp_credentials(file_type: str, is_public: bool = False, type_key: str = "realtime"):
    """
    异步获取 COS 临时凭证，用于文件或图片上传。

    Args:
        bot_biz_id (str): 应用ID
        file_type (str): 文件类型，例如 'pdf', 'png' 等
        is_public (bool): 是否公开访问，图片通常为 True，文件为 False
        type_key (str): 存储类型，'offline' 表示离线文件，'realtime' 表示实时文件

    Returns:
        dict: 包含 bucket, region, upload_path 和临时凭证的字典
    """
    try:
        # 初始化腾讯云凭证和客户端
        cred = credential.Credential(Config.TENCENT_SECRET_ID, Config.TENCENT_SECRET_KEY)
        client = CommonClient("lke", "2023-11-30", cred, Config.TENCENT_REGION)

        # 构造请求参数
        params = {
            "BotBizId": Config.BOT_BIZ_ID,
            "FileType": file_type,
            "IsPublic": is_public,
            "TypeKey": type_key
        }

        # 调用 DescribeStorageCredential 接口
        resp = client.call_json("DescribeStorageCredential", params)

        # 解析响应
        response = resp["Response"]
        credentials = response["Credentials"]

        return {
            "bucket": response["Bucket"],
            "region": response["Region"],
            "upload_path": response["UploadPath"],
            "tmp_secret_id": credentials["TmpSecretId"],
            "tmp_secret_key": credentials["TmpSecretKey"],
            "token": credentials["Token"]
        }
    except TencentCloudSDKException as e:
        logger.error(f"获取 COS 临时凭证失败: {e}")
        raise Exception(f"获取 COS 临时凭证失败: {str(e)}")

# 异步上传文件到腾讯云 COS
async def upload_to_cos_async(binary_data: bytes, bucket: str, key: str, region: str, secret_id: str, secret_key: str, token: str) -> str:
    """异步上传文件到腾讯云 COS"""
    def sync_upload():
        """同步上传函数，运行在线程池中"""
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)
        client = CosS3Client(config)
        stream = io.BytesIO(binary_data)
        client.put_object(Bucket=bucket, Key=key, Body=stream)
        cos_url = f"https://{bucket}.cos.{region}.myqcloud.com/{key}"
        logger.info(f"Successfully uploaded to COS: {cos_url}")
        return cos_url

    try:
        # 在线程池中运行同步上传任务
        cos_url = await asyncio.to_thread(sync_upload)
        return cos_url
    except Exception as e:
        logger.error(f"Error uploading to COS: {e}")
        raise





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
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            async with aconnect_sse(
                    client,
                    "POST",
                    Config.TENCENT_AI_URL,
                    json=data,
                    headers={"Accept": "text/event-stream"}
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    try:
                        data = json.loads(sse.data)
                        # logger.info(f'sse.event: {sse.event} {data}')
                        if sse.event == "reply":
                            payload = data["payload"]
                            # if payload.get("is_final"):
                            reply_content = payload["content"]
                            is_final = payload.get("is_final", False)
                            if payload.get("is_from_self"):
                                print(f"\r[用户提问] is_final: {is_final} {reply_content}\n")
                            else:
                                print(f"\r[Bot回复] is_final: {is_final} {reply_content}\n")
                                try:
                                    if reply_content.startswith('{"data":"'):
                                        content = json.loads(reply_content).get("data")
                                    else:
                                        content = reply_content
                                    await update_card_content(card_id, element_id, content, sequence)
                                    sequence += 1
                                    if is_final:
                                        break
                                except Exception as e:
                                    logger.error(f'json.loads失败 reply_content: {reply_content}')
                        # elif sse.event == "token_stat":
                        #     # 显示处理进度
                        #     status = data["payload"].get("status_summary_title", "")
                        #     if status:
                        #         logger.info(f"\r[状态] {status}...")
                    except json.JSONDecodeError:
                        print("\n[解析错误] 接收到的数据:", sse.data)
                    except Exception as e:
                        print(f"\n[处理错误] {str(e)}")
                # 关闭流式更新
                await disable_streaming_mode(card_id, sequence)
    except httpx.HTTPStatusError as e:
        print(f"\n[HTTP错误] {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"\n[系统错误] {str(e)}")
