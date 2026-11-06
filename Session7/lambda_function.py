import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Bedrock の呼び出し（Converse API は tool_use に対応している）
bedrock = boto3.client("bedrock-runtime", region_name="ap-northeast-1")

# 環境変数で指定する（コードを書き換えずに設定を変えられる）
MODEL_ID = os.environ["MODEL_ID"]

# 作成者のマップから作った店リスト（この Lambda と同じフォルダの shops.txt）
SHOPS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shops.txt")
MAP_NAME = "ランチマップ（作成者の Google マイマップ）"

MAX_PROMPT_LENGTH = 1000
MAX_TOOL_ROUNDS = 3  # AI がツールを繰り返し使える上限。無限に呼び続けないための安全策

SYSTEM_PROMPT = (
    "あなたは日本の食事と飲食店に詳しいアドバイザーです。"
    "店リストの店は、すべて東京駅八重洲口・京橋駅付近の店です。"
    "店を提案するときは、必ず get_map_shops ツールで店リストを読み、そのリストにある店だけを挙げてください。"
    "店の住所や所要時間は店リストにないので、書かないでください。"
    "リストにない店名や住所は書かないでください。"
    "回答の最後に、参考にしたマップの名前を書いてください。"
    "マークダウンの記号（#、*、| の表、--- など）は使わず、普通の文章で簡潔に日本語で答えてください。"
)

# AI に渡すツールの定義。AI はこの説明を読んで、店リストを読むかを自分で判断する
TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_map_shops",
                "description": "作成者のマップ「ランチマップ」に載っている店の一覧を読みます。カテゴリ（とんかつ、洋食、カレーなど）と店名、ひとことメモが含まれます。",
                "inputSchema": {"json": {"type": "object", "properties": {}}},
            }
        }
    ]
}


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def read_shops():
    """店リストのテキストを読み、コメント行（# で始まる行）と空行を除いて返す。"""
    with open(SHOPS_PATH, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return lines


def run_tool(tool_use):
    """AI が要求したツールを実行し、結果を Converse API の形で返す。"""
    if tool_use["name"] != "get_map_shops":
        return {"toolResult": {"toolUseId": tool_use["toolUseId"], "status": "error",
                               "content": [{"text": "未知のツールです"}]}}
    try:
        shops = read_shops()
    except OSError:
        logger.exception("shops.txt の読み込みに失敗しました")
        return {"toolResult": {"toolUseId": tool_use["toolUseId"], "status": "error",
                               "content": [{"text": "店リストを読み込めませんでした"}]}}
    return {"toolResult": {"toolUseId": tool_use["toolUseId"],
                           "content": [{"json": {"map": MAP_NAME, "shops": shops}}]}}


def ask_with_tools(prompt, used_tools):
    """AI に質問し、必要なら店リストのツールを使いながら回答を作る。"""
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    for _ in range(MAX_TOOL_ROUNDS + 1):
        response = bedrock.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={"maxTokens": 2000, "temperature": 0.4},
        )
        output_message = response["output"]["message"]
        messages.append(output_message)

        # ツールが不要になったら（stopReason が end_turn）、文章を取り出して終わる
        if response.get("stopReason") != "tool_use":
            return "".join(block["text"] for block in output_message["content"] if "text" in block)

        # AI がツールを求めたときは、実行して結果を返し、続きを答えさせる
        tool_results = []
        for block in output_message["content"]:
            if "toolUse" in block:
                tool_results.append(run_tool(block["toolUse"]))
                used_tools.append(block["toolUse"]["name"])
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("ツールの呼び出し回数が上限に達しました")


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

    used_tools = []
    try:
        answer = ask_with_tools(prompt.strip(), used_tools)
    except (ClientError, KeyError, IndexError, RuntimeError):
        logger.exception("shop recommendation failed")
        return respond(502, {"message": "おすすめを取得できませんでした。時間をおいて再度お試しください"})

    # 参考にしたマップを返す（ツールを使わなかった場合は空）
    sources = [{"map": MAP_NAME}] if "get_map_shops" in used_tools else []
    return respond(200, {"answer": answer, "sources": sources})
