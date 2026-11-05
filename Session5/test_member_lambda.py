"""会員 API（Session5）の本人確認のテスト。DynamoDB はモックし、AWS には接続しない。

実行: リポジトリのルートで  python -m unittest Session5/test_member_lambda.py -v
"""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

_PATH = Path(__file__).resolve().parent / "lambda_function.py"
_spec = importlib.util.spec_from_file_location("session5_lambda_function", _PATH)
lf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lf)

FORBIDDEN_MESSAGE = "ログインした本人の ID・メールアドレスで登録してください"


def make_event(body_overrides=None, claims=None):
    body = {
        "id": "sample-0001",
        "name": "山田 太郎",
        "email": "sample@example.com",
        "age": 30,
        "address": "東京都千代田区1-1-1",
        "tel": "09012345678",
    }
    body.update(body_overrides or {})
    event = {
        "version": "2.0",
        "routeKey": "POST /",
        "requestContext": {"http": {"method": "POST", "path": "/"}},
        "body": json.dumps(body, ensure_ascii=False),
        "isBase64Encoded": False,
    }
    if claims is not None:
        event["requestContext"]["authorizer"] = {"jwt": {"claims": claims}}
    return event


CLAIMS = {"cognito:username": "sample-0001", "email": "sample@example.com"}


class CreateUserOwnerCheckTest(unittest.TestCase):
    def setUp(self):
        self.table = mock.Mock()
        patcher = mock.patch.object(lf, "get_table", return_value=self.table)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_with_matching_claims_returns_201(self):
        res = lf.lambda_handler(make_event(claims=CLAIMS), None)
        self.assertEqual(res["statusCode"], 201)
        self.table.put_item.assert_called_once()

    def test_create_with_other_id_returns_403(self):
        res = lf.lambda_handler(make_event({"id": "sample-9999"}, claims=CLAIMS), None)
        self.assertEqual(res["statusCode"], 403)

    def test_create_with_other_email_returns_403(self):
        res = lf.lambda_handler(make_event({"email": "other@example.com"}, claims=CLAIMS), None)
        self.assertEqual(res["statusCode"], 403)

    def test_create_without_claims_still_returns_201(self):
        res = lf.lambda_handler(make_event(), None)
        self.assertEqual(res["statusCode"], 201)
        self.table.put_item.assert_called_once()

    def test_403_message_is_exact_and_table_untouched(self):
        res = lf.lambda_handler(make_event({"id": "sample-9999"}, claims=CLAIMS), None)
        self.assertEqual(json.loads(res["body"]), {"message": FORBIDDEN_MESSAGE})
        self.table.put_item.assert_not_called()


if __name__ == "__main__":
    unittest.main()
