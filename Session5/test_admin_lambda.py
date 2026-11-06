"""管理 API（Session5）の管理者確認のテスト。DynamoDB はモックし、AWS には接続しない。

実行: リポジトリのルートで  python -m unittest Session5/test_admin_lambda.py -v
"""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

_PATH = Path(__file__).resolve().parent / "admin_lambda_function.py"
_spec = importlib.util.spec_from_file_location("session5_admin_lambda_function", _PATH)
alf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(alf)

FORBIDDEN_MESSAGE = "管理者のみ利用できます"


def make_event(route="GET /users", claims=None, path_id=None):
    event = {
        "version": "2.0",
        "routeKey": route,
        "rawPath": "/users" if path_id is None else f"/users/{path_id}",
        "requestContext": {"http": {"method": route.split(" ")[0]}},
        "queryStringParameters": {"limit": "20"},
        "isBase64Encoded": False,
    }
    if path_id is not None:
        event["pathParameters"] = {"id": path_id}
    if claims is not None:
        event["requestContext"]["authorizer"] = {"jwt": {"claims": claims}}
    return event


class RequireAdminTest(unittest.TestCase):
    def setUp(self):
        self.table = mock.Mock()
        self.table.scan.return_value = {"Items": []}
        patcher = mock.patch.object(alf, "get_table", return_value=self.table)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_table_untouched(self):
        self.table.scan.assert_not_called()
        self.table.get_item.assert_not_called()
        self.table.put_item.assert_not_called()
        self.table.delete_item.assert_not_called()

    def test_admin_group_returns_200(self):
        res = alf.lambda_handler(make_event(claims={"cognito:groups": ["admins"]}), None)
        self.assertEqual(res["statusCode"], 200)
        self.table.scan.assert_called_once()

    def test_admin_group_string_form_returns_200(self):
        res = alf.lambda_handler(make_event(claims={"cognito:groups": "[admins]"}), None)
        self.assertEqual(res["statusCode"], 200)

    def test_plain_string_and_comma_forms_return_200(self):
        for value in ("admins", "members,admins", "[members, admins]"):
            with self.subTest(value=value):
                res = alf.lambda_handler(make_event(claims={"cognito:groups": value}), None)
                self.assertEqual(res["statusCode"], 200)

    def test_multiple_groups_string_with_admins_returns_200(self):
        res = alf.lambda_handler(make_event(claims={"cognito:groups": "[members admins]"}), None)
        self.assertEqual(res["statusCode"], 200)

    def test_member_without_admin_group_returns_403(self):
        res = alf.lambda_handler(make_event(claims={"cognito:groups": "[members]"}), None)
        self.assertEqual(res["statusCode"], 403)
        self.assert_table_untouched()

    def test_missing_groups_claim_with_claims_returns_403(self):
        res = alf.lambda_handler(make_event(claims={"email": "a@example.com"}), None)
        self.assertEqual(res["statusCode"], 403)
        self.assert_table_untouched()

    def test_without_claims_still_works(self):
        res = alf.lambda_handler(make_event(), None)
        self.assertEqual(res["statusCode"], 200)
        self.table.scan.assert_called_once()

    def test_empty_claims_treated_as_no_claims(self):
        res = alf.lambda_handler(make_event(claims={}), None)
        self.assertEqual(res["statusCode"], 200)

    def test_superadmins_string_does_not_grant_access(self):
        for value in ("[superadmins]", "superadmins", "[admins2]", "[my-admins]"):
            with self.subTest(value=value):
                res = alf.lambda_handler(make_event(claims={"cognito:groups": value}), None)
                self.assertEqual(res["statusCode"], 403)
        self.assert_table_untouched()

    def test_superadmins_list_does_not_grant_access(self):
        res = alf.lambda_handler(make_event(claims={"cognito:groups": ["superadmins"]}), None)
        self.assertEqual(res["statusCode"], 403)

    def test_unexpected_groups_types_do_not_crash(self):
        for value in (None, "", [], 123, {"a": 1}, [None, 1]):
            with self.subTest(value=value):
                res = alf.lambda_handler(make_event(claims={"cognito:groups": value}), None)
                self.assertEqual(res["statusCode"], 403)

    def test_403_message_is_exact_and_table_untouched(self):
        res = alf.lambda_handler(make_event(claims={"cognito:groups": "[members]"}), None)
        self.assertEqual(json.loads(res["body"]), {"message": FORBIDDEN_MESSAGE})
        self.assert_table_untouched()

    def test_non_admin_delete_returns_403_without_deleting(self):
        event = make_event("DELETE /users/{id}", claims={"cognito:groups": "[members]"}, path_id="u-0001")
        res = alf.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 403)
        self.table.delete_item.assert_not_called()

    def test_admin_unknown_route_returns_404(self):
        res = alf.lambda_handler(make_event("GET /nope", claims={"cognito:groups": ["admins"]}), None)
        self.assertEqual(res["statusCode"], 404)

    def test_non_admin_unknown_route_returns_403(self):
        res = alf.lambda_handler(make_event("GET /nope", claims={"cognito:groups": ["members"]}), None)
        self.assertEqual(res["statusCode"], 403)


if __name__ == "__main__":
    unittest.main()
