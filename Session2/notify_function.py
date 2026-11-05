"""会員登録完了メール送信（DynamoDB ストリームから呼ばれる Lambda）

会員テーブルに新しい会員が登録（INSERT）されると、DynamoDB ストリームがこの関数を呼び出します。
関数は登録された会員のメールアドレス宛てに、Amazon SES で御礼メールを送ります。

環境変数
  SENDER      送信元メールアドレス（SES で検証済みのもの）。MAIL_MODE が ses のとき必須
  MAIL_MODE   ses（既定）: SES でメールを送る / log: メールは送らず、件名と本文をログに出す
  SES_REGION  SES を使うリージョン（既定: ap-northeast-1）
"""

import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VALID_MODES = ("ses", "log")
DEFAULT_REGION = "ap-northeast-1"

SUBJECT = "【View AWS勉強会サイト】会員登録が完了しました"


def get_ses_client():
    # 呼ばれたときに作成する（import しただけでは AWS に接続しない）
    region = os.environ.get("SES_REGION", DEFAULT_REGION)
    return boto3.client("ses", region_name=region)


def read_config():
    """環境変数を読み、設定に誤りがあれば分かりやすいエラーにする。"""
    mode = os.environ.get("MAIL_MODE", "ses")
    if mode not in VALID_MODES:
        raise RuntimeError(f"MAIL_MODE は ses か log を指定してください（現在: {mode}）")
    sender = os.environ.get("SENDER", "")
    if mode == "ses" and not sender:
        raise RuntimeError("環境変数 SENDER（SES で検証済みの送信元アドレス）が設定されていません")
    return mode, sender


def get_string(image, key):
    """DynamoDB JSON（例: {"S": "abc"}）から文字列を取り出す。無ければ空文字。"""
    return image.get(key, {}).get("S", "")


def build_message(name):
    """メールの件名と本文（テキスト）を作る。"""
    body = (
        f"{name} 様\n"
        "\n"
        "View AWS勉強会サイトへの会員登録が完了しました。\n"
        "ご登録ありがとうございます。\n"
        "\n"
        "このメールは自動送信です。心当たりがない場合は、このメールを破棄してください。"
    )
    return SUBJECT, body


def send_mail(email, subject, body, sender):
    """SES でメールを送り、MessageId を返す。失敗したときはエラーコードだけ記録して再送出する。"""
    try:
        response = get_ses_client().send_email(
            Source=sender,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
    except ClientError as e:
        # 個人情報を残さないため、メールアドレスはログに出さない
        logger.error("SES の送信に失敗しました code=%s", e.response["Error"]["Code"])
        raise  # 再送出して、Lambda の再試行設定に任せる
    return response["MessageId"]


def lambda_handler(event, context):
    mode, sender = read_config()
    sent = 0
    skipped = 0

    for record in event.get("Records", []):
        # マッピングのフィルターでも INSERT だけに絞るが、念のためここでも確認する
        if record.get("eventName") != "INSERT":
            continue

        image = record.get("dynamodb", {}).get("NewImage", {})
        user_id = get_string(image, "id") or "(id なし)"
        email = get_string(image, "email")
        name = get_string(image, "name")

        if not email:
            # 再試行しても直らないので、警告だけ残して次へ進む（メールアドレスは無いので出さない）
            logger.warning("メールアドレスがないため送信をスキップしました id=%s", user_id)
            skipped += 1
            continue

        subject, body = build_message(name)

        if mode == "log":
            # 注意: log モードは氏名などの個人情報をログに出す。メールを使えない場合の代替用
            logger.info("[MAIL_MODE=log] 送信先 id=%s 件名=%s\n%s", user_id, subject, body)
        else:
            message_id = send_mail(email, subject, body, sender)
            logger.info("メールを送信しました id=%s MessageId=%s", user_id, message_id)
        sent += 1

    return {"sent": sent, "skipped": skipped}
