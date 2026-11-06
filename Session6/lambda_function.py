import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name="ap-northeast-1")
# 使うモデルは Lambda の環境変数 MODEL_ID で指定する（コードを変えずに差し替えられる）
MODEL_ID = os.environ["MODEL_ID"]
MAX_PROMPT_LENGTH = 1000


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return respond(400, {"message": "JSON の形式が正しくありません"})

    prompt = body.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return respond(400, {"message": "料理の希望を入力してください"})
    if len(prompt) > MAX_PROMPT_LENGTH:
        return respond(400, {"message": "入力は1000文字以内にしてください"})

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "system": (
            "あなたは日本の旅行と郷土料理に詳しいアドバイザーです。"
            "ユーザーの希望に合わせて、旅行先で楽しめる料理を日本語で提案してください。"
            "簡潔に、料理名とおすすめの理由を説明してください。"
            "マークダウンの記号（#、*、| の表、--- など）は使わず、普通の文章で答えてください。"
        ),
        "messages": [{"role": "user", "content": prompt.strip()}],
        "temperature": 0.4,
    }

    try:
        response = bedrock.invoke_model(
            body=json.dumps(request_body),
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        answer = result["content"][0]["text"]
        return respond(200, {"answer": answer})
    except (ClientError, KeyError, IndexError, json.JSONDecodeError):
        logger.exception("Bedrock recommendation failed")
        return respond(502, {"message": "おすすめを取得できませんでした。時間をおいて再度お試しください"})
