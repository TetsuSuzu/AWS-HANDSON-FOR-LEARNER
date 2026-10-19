import json
import logging
import os
import urllib.parse
import urllib.request

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Bedrock の呼び出し（Converse API は tool_use に対応している）
bedrock = boto3.client("bedrock-runtime", region_name="ap-northeast-1")

# 環境変数で指定する（コードを書き換えずに設定を変えられる）
MODEL_ID = os.environ["MODEL_ID"]
SEARCH_API_KEY = os.environ["BRAVE_API_KEY"]

SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
MAX_PROMPT_LENGTH = 1000
MAX_TOOL_ROUNDS = 3  # AI が検索を繰り返せる上限。無限に検索し続けないための安全策

SYSTEM_PROMPT = (
    "あなたは日本の旅行と飲食店に詳しいアドバイザーです。"
    "店名、住所、営業時間などの具体的な情報は、推測で書かず、web_search で確かめてから答えてください。"
    "検索は必要な分だけ行い、多くても 2 回までにしてください。"
    "回答の最後に、参考にした情報源の URL を一覧で示してください。"
    "簡潔に日本語で答えてください。"
)

# AI に渡すツールの定義。AI はこの説明を読んで、検索が必要かを自分で判断する
TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "web_search",
                "description": "インターネットで公開情報を検索します。店舗の住所、営業時間、口コミサイトの評価など、確かめたい情報に使います。",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "検索キーワード（日本語）"}
                        },
                        "required": ["query"],
                    }
                },
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


def web_search(query):
    """Brave Search API で検索し、結果の一部（タイトル・URL・要約）を返す。"""
    params = urllib.parse.urlencode({"q": query, "count": 5})
    request = urllib.request.Request(
        f"{SEARCH_URL}?{params}",
        headers={"Accept": "application/json", "X-Subscription-Token": SEARCH_API_KEY},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read())
    results = data.get("web", {}).get("results", [])
    return [
        {"title": item.get("title", ""), "url": item.get("url", ""), "description": item.get("description", "")}
        for item in results[:5]
    ]


def run_tool(tool_use):
    """AI が要求したツールを実行し、結果を Converse API の形で返す。"""
    if tool_use["name"] != "web_search":
        return {"toolResult": {"toolUseId": tool_use["toolUseId"], "status": "error",
                               "content": [{"text": "未知のツールです"}]}}
    query = tool_use.get("input", {}).get("query", "")
    try:
        results = web_search(query)
    except Exception:
        # 検索に失敗しても、AI には「失敗した」と伝えて続きを答えさせる
        logger.exception("web search failed query=%s", query)
        return {"toolResult": {"toolUseId": tool_use["toolUseId"], "status": "error",
                               "content": [{"text": "検索に失敗しました"}]}}
    return {"toolResult": {"toolUseId": tool_use["toolUseId"],
                           "content": [{"json": {"results": results}}]}}


def ask_with_tools(prompt, sources):
    """AI に質問し、必要なら検索ツールを使いながら回答を作る。"""
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

        # 検索が不要になったら（stopReason が end_turn）、文章を取り出して終わる
        if response.get("stopReason") != "tool_use":
            return "".join(block["text"] for block in output_message["content"] if "text" in block)

        # AI が検索を求めたときは、検索を実行して結果を返し、続きを答えさせる
        tool_results = []
        for block in output_message["content"]:
            if "toolUse" in block:
                result = run_tool(block["toolUse"])
                tool_results.append(result)
                for item in result["toolResult"].get("content", []):
                    for search_result in item.get("json", {}).get("results", []):
                        sources.append(search_result)
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("検索の回数が上限に達しました")


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

    sources = []
    try:
        answer = ask_with_tools(prompt.strip(), sources)
    except (ClientError, KeyError, IndexError, RuntimeError, json.JSONDecodeError):
        logger.exception("search recommendation failed")
        return respond(502, {"message": "おすすめを取得できませんでした。時間をおいて再度お試しください"})

    # 同じ URL が何度も出ないように、重複を取り除いて返す
    unique_sources = list({item["url"]: item for item in sources if item.get("url")}.values())
    return respond(200, {"answer": answer, "sources": unique_sources})
