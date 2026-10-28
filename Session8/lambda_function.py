"""会員API（Aurora PostgreSQL 版）

API Gateway HTTP API（ペイロード形式 2.0）から呼ばれ、routeKey で処理を振り分けます。
Session2 の DynamoDB 版（app.py）と同じ API の形で、保存先だけを Aurora に替えています。
SQL は RDS Data API（HTTPS）で実行するため、Lambda を VPC に入れる必要はありません。
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

CLUSTER_ARN = os.environ["CLUSTER_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DB_NAME = os.environ.get("DB_NAME", "kakeibo")
FIELDS = ["id", "name", "email", "age", "address", "tel"]
SELECT_COLUMNS = "SELECT id, name, email, age, address, tel FROM users"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEL_PATTERN = re.compile(r"^\d+$")

_client = None


class ApiError(Exception):
    """想定内のエラー。ステータスコードと、画面に出すメッセージを持つ。"""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def get_client():
    # 初回のみ作成し、同じ実行環境の次の呼び出しでは使い回す
    global _client
    if _client is None:
        _client = boto3.client("rds-data")
    return _client


def to_param(name, value):
    """SQL に渡す値を、Data API の形に変える。文字・整数・NULL の型を正しく伝える。"""
    if value is None:
        field = {"isNull": True}
    elif isinstance(value, int) and not isinstance(value, bool):
        field = {"longValue": value}
    else:
        field = {"stringValue": str(value)}
    return {"name": name, "value": field}


def from_field(field):
    """結果の 1 マスを、Python の値に戻す。"""
    if field.get("isNull"):
        return None
    for key in ("stringValue", "longValue", "doubleValue", "booleanValue"):
        if key in field:
            return field[key]
    return None


def run_sql(sql, **params):
    """SQL を実行し、(行のリスト, 変わった行数) を返す。"""
    result = get_client().execute_statement(
        resourceArn=CLUSTER_ARN,
        secretArn=SECRET_ARN,
        database=DB_NAME,
        sql=sql,
        parameters=[to_param(name, value) for name, value in params.items()],
        includeResultMetadata=True,
    )
    columns = [column["name"] for column in result.get("columnMetadata", [])]
    rows = [
        {column: from_field(field) for column, field in zip(columns, record)}
        for record in result.get("records", [])
    ]
    return rows, result.get("numberOfRecordsUpdated", 0)


def respond(status, body=None):
    if status == 204:
        return {"statusCode": 204}
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


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


def encode_next_token(last_id):
    return base64.urlsafe_b64encode(last_id.encode("utf-8")).decode("ascii")


def decode_next_token(token):
    try:
        return base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
    except (ValueError, UnicodeError):
        raise ApiError(400, "nextToken の形式が正しくありません")


def create_user(event):
    user = parse_user(read_json(event))
    # 同じ ID かメールアドレスがあれば何もしない。重複は DB の主キーと UNIQUE 制約が防ぐ
    _, changed = run_sql(
        "INSERT INTO users (id, name, email, age, address, tel) "
        "VALUES (:id, :name, :email, :age, :address, :tel) ON CONFLICT DO NOTHING",
        **user,
    )
    if changed == 0:
        raise ApiError(409, "この ID またはメールアドレスは登録されています")
    return respond(201, {"message": "登録が完了しました", "user": user})


def get_user(user_id):
    rows, _ = run_sql(SELECT_COLUMNS + " WHERE id = :id", id=user_id)
    if not rows:
        raise ApiError(404, "会員が見つかりません")
    return respond(200, rows[0])


def list_users(query):
    try:
        limit = int(query.get("limit", 20))
    except ValueError:
        raise ApiError(400, "limit は整数で指定してください")
    if not 1 <= limit <= 100:
        raise ApiError(400, "limit は 1〜100 の範囲で指定してください")

    # 1 件多く取り、続きがあるかを判定する
    token = query.get("nextToken")
    if token:
        after = decode_next_token(token)
        rows, _ = run_sql(
            SELECT_COLUMNS + " WHERE id > :after ORDER BY id LIMIT :limit",
            after=after,
            limit=limit + 1,
        )
    else:
        rows, _ = run_sql(SELECT_COLUMNS + " ORDER BY id LIMIT :limit", limit=limit + 1)

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_token = encode_next_token(rows[-1]["id"]) if has_more else None
    return respond(200, {"users": rows, "nextToken": next_token})


def update_user(user_id, event):
    user = parse_user(read_json(event))
    if user["id"] != user_id:
        raise ApiError(400, "パスの ID と本文の ID が一致しません")
    try:
        _, changed = run_sql(
            "UPDATE users SET name = :name, email = :email, age = :age, "
            "address = :address, tel = :tel WHERE id = :id",
            **user,
        )
    except ClientError as e:
        # メールアドレスの UNIQUE 制約違反。DB のエラー文に含まれる文言で判定する
        if "duplicate key" in e.response["Error"].get("Message", ""):
            raise ApiError(409, "このメールアドレスは別の会員が使っています")
        raise
    if changed == 0:
        raise ApiError(404, "会員が見つかりません")
    return respond(200, {"message": "更新が完了しました", "user": user})


def delete_user(user_id):
    _, changed = run_sql("DELETE FROM users WHERE id = :id", id=user_id)
    if changed == 0:
        raise ApiError(404, "会員が見つかりません")
    return respond(204)


ROUTES = {
    # 会員登録は、API の URL そのもの（パスなし）に POST する
    "POST /": lambda event, params: create_user(event),
    "GET /users": lambda event, params: list_users(event.get("queryStringParameters") or {}),
    "GET /users/{id}": lambda event, params: get_user(params["id"]),
    "PUT /users/{id}": lambda event, params: update_user(params["id"], event),
    "DELETE /users/{id}": lambda event, params: delete_user(params["id"]),
}


def handler(event, context):
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
