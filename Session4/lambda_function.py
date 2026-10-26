"""会員管理API（管理者用）

Session3 で登録された会員を、一覧・取得・更新・削除します。
API Gateway HTTP API（ペイロード形式 2.0）から呼ばれ、routeKey で処理を振り分けます。
この API には認証がありません。URL を知っている人は誰でも呼べるため、研修の間だけ使います。
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

TABLE_NAME = os.environ["TABLE_NAME"]
FIELDS = ["id", "name", "email", "age", "address", "tel"]
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEL_PATTERN = re.compile(r"^\d+$")

table = boto3.resource("dynamodb").Table(TABLE_NAME)


class ApiError(Exception):
    """想定内のエラー。ステータスコードと、画面に出すメッセージを持つ。"""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


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


def list_users(query):
    """会員の一覧を返す。件数が多いときは nextToken で次のページを取る。"""
    try:
        limit = int(query.get("limit", 20))
    except ValueError:
        raise ApiError(400, "limit は整数で指定してください")
    if not 1 <= limit <= 100:
        raise ApiError(400, "limit は 1〜100 の範囲で指定してください")

    params = {"Limit": limit}
    token = query.get("nextToken")
    if token:
        try:
            params["ExclusiveStartKey"] = json.loads(base64.urlsafe_b64decode(token.encode("ascii")))
        except (ValueError, UnicodeError):
            raise ApiError(400, "nextToken の形式が正しくありません")

    result = table.scan(**params)
    last_key = result.get("LastEvaluatedKey")
    next_token = None
    if last_key:
        next_token = base64.urlsafe_b64encode(json.dumps(last_key).encode("utf-8")).decode("ascii")
    users = [to_api(item) for item in result.get("Items", [])]
    return respond(200, {"users": users, "nextToken": next_token})


def get_user(user_id):
    item = table.get_item(Key={"id": user_id}).get("Item")
    if not item:
        raise ApiError(404, "会員が見つかりません")
    return respond(200, to_api(item))


def update_user(user_id, event):
    user = parse_user(read_json(event))
    if user["id"] != user_id:
        raise ApiError(400, "パスの ID と本文の ID が一致しません")
    try:
        # 存在する会員だけを更新する（なければ新規に作ってしまわない）
        table.put_item(Item=user, ConditionExpression="attribute_exists(id)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ApiError(404, "会員が見つかりません")
        raise
    return respond(200, {"message": "更新が完了しました", "user": user})


def delete_user(user_id):
    try:
        table.delete_item(Key={"id": user_id}, ConditionExpression="attribute_exists(id)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ApiError(404, "会員が見つかりません")
        raise
    return respond(204)


ROUTES = {
    "GET /users": lambda event, params: list_users(event.get("queryStringParameters") or {}),
    "GET /users/{id}": lambda event, params: get_user(params["id"]),
    "PUT /users/{id}": lambda event, params: update_user(params["id"], event),
    "DELETE /users/{id}": lambda event, params: delete_user(params["id"]),
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
