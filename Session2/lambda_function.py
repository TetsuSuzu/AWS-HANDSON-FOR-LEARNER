"""会員API（docs/api-spec.md の仕様どおりに実装）

API Gateway HTTP API（ペイロード形式 2.0）から呼ばれ、routeKey で処理を振り分けます。
"""

import base64
import json
import logging
import os
import re

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "users")
FIELDS = ["id", "name", "email", "age", "address", "tel"]
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEL_PATTERN = re.compile(r"^\d+$")

_table = None


class ApiError(Exception):
    """想定内のエラー。ステータスコードと、画面に出すメッセージを持つ。"""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def get_table():
    # 初回のみ作成し、同じ実行環境の次の呼び出しでは使い回す
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _table


def respond(status, body=None):
    if status == 204:
        return {"statusCode": 204}
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def to_api(item):
    """DynamoDB の項目を API の形に変える（age は Decimal で返るため int にする）"""
    user = {f: item[f] for f in FIELDS}
    user["age"] = int(item["age"])
    return user


def read_json(event):
    body = event.get("body")
    if not body:
        raise ApiError(400, "リクエストボディがありません")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise ApiError(400, "JSON の形式が正しくありません")


def parse_user(raw):
    """リクエストの JSON を検証し、保存できる dict にして返す。"""
    if not isinstance(raw, dict):
        raise ApiError(400, "リクエストの形式が正しくありません")

    missing = [f for f in FIELDS if raw.get(f) in (None, "")]
    if missing:
        raise ApiError(400, "必須項目が不足しています: " + ", ".join(missing))

    for field in ["id", "name", "email", "address", "tel"]:
        if not isinstance(raw[field], str):
            raise ApiError(400, f"{field} は文字列で指定してください")

    age = raw["age"]
    if isinstance(age, bool) or not isinstance(age, int) or age < 0:
        raise ApiError(400, "年齢は0以上の整数で指定してください")

    if not EMAIL_PATTERN.match(raw["email"]):
        raise ApiError(400, "メールアドレスの形式が正しくありません")

    if not TEL_PATTERN.match(raw["tel"]):
        raise ApiError(400, "電話番号は数字のみで指定してください")

    return {f: raw[f] for f in FIELDS}


def encode_next_token(last_key):
    raw = json.dumps(last_key).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_next_token(token):
    try:
        return json.loads(base64.urlsafe_b64decode(token.encode("ascii")))
    except (ValueError, UnicodeError):
        raise ApiError(400, "nextToken の形式が正しくありません")


def create_user(event):
    user = parse_user(read_json(event))
    try:
        get_table().put_item(
            Item=user,
            ConditionExpression="attribute_not_exists(id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ApiError(409, "この ID はすでに登録されています")
        raise
    return respond(201, {"message": "登録が完了しました", "user": user})


def get_user(user_id):
    item = get_table().get_item(Key={"id": user_id}).get("Item")
    if not item:
        raise ApiError(404, "会員が見つかりません")
    return respond(200, to_api(item))


def list_users(query):
    try:
        limit = int(query.get("limit", 20))
    except ValueError:
        raise ApiError(400, "limit は整数で指定してください")
    if not 1 <= limit <= 100:
        raise ApiError(400, "limit は 1〜100 の範囲で指定してください")

    params = {"Limit": limit}
    token = query.get("nextToken")
    if token:
        params["ExclusiveStartKey"] = decode_next_token(token)

    result = get_table().scan(**params)
    last_key = result.get("LastEvaluatedKey")
    next_token = encode_next_token(last_key) if last_key else None
    users = [to_api(item) for item in result.get("Items", [])]
    return respond(200, {"users": users, "nextToken": next_token})


def update_user(user_id, event):
    user = parse_user(read_json(event))
    if user["id"] != user_id:
        raise ApiError(400, "パスの ID と本文の ID が一致しません")
    try:
        get_table().put_item(
            Item=user,
            ConditionExpression="attribute_exists(id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ApiError(404, "会員が見つかりません")
        raise
    return respond(200, {"message": "更新が完了しました", "user": user})


def delete_user(user_id):
    try:
        get_table().delete_item(
            Key={"id": user_id},
            ConditionExpression="attribute_exists(id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ApiError(404, "会員が見つかりません")
        raise
    return respond(204)


ROUTES = {
    # 会員登録は、API の URL そのもの（パスなし）に POST する
    "POST /": lambda event, params: create_user(event),
    "POST /v1/users": lambda event, params: create_user(event),
    "GET /v1/users/{id}": lambda event, params: get_user(params["id"]),
    "GET /v1/users": lambda event, params: list_users(event.get("queryStringParameters") or {}),
    "PUT /v1/users/{id}": lambda event, params: update_user(params["id"], event),
    "DELETE /v1/users/{id}": lambda event, params: delete_user(params["id"]),
}


def lambda_handler(event, context):
    route = event.get("routeKey", "")
    params = event.get("pathParameters") or {}
    try:
        action = ROUTES.get(route)
        if action is None:
            raise ApiError(404, "見つかりません")
        return action(event, params)
    except ApiError as e:
        return respond(e.status, {"message": e.message})
    except Exception:
        # 内部の詳細は返さず、CloudWatch Logs に残す
        logger.exception("unexpected error route=%s", route)
        return respond(500, {"message": "サーバー内部でエラーが発生しました"})
