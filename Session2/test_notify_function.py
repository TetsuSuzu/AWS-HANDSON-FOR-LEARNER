"""notify_function.py のテスト（AWS には接続しません）

リポジトリのルートで次のコマンドを実行します。
    python -B -m unittest Session2/test_notify_function.py -v
"""

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

# lambda_function.py と名前がぶつからないよう、ファイルパスから固有の名前で読み込む
_PATH = Path(__file__).resolve().parent / "notify_function.py"
_spec = importlib.util.spec_from_file_location("session2_notify_function", _PATH)
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)

SENDER = "sender@example.com"
EMAIL = "taro@example.com"
SUBJECT = "【View AWS勉強会サイト】会員登録が完了しました"
BODY = (
    "山田太郎 様\n"
    "\n"
    "View AWS勉強会サイトへの会員登録が完了しました。\n"
    "ご登録ありがとうございます。\n"
    "\n"
    "このメールは自動送信です。心当たりがない場合は、このメールを破棄してください。"
)


def make_record(event_name="INSERT", email=EMAIL, name="山田太郎", user_id="u-0001"):
    image = {"id": {"S": user_id}, "age": {"N": "30"}}
    if name is not None:
        image["name"] = {"S": name}
    if email is not None:
        image["email"] = {"S": email}
    return {
        "eventName": event_name,
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"id": {"S": user_id}}, "NewImage": image},
    }


def make_event(*records):
    return {"Records": list(records)}


class NotifyFunctionTest(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"SENDER": SENDER}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("MAIL_MODE", None)
        self.ses = MagicMock()
        self.ses.send_email.return_value = {"MessageId": "msg-123"}
        p = patch.object(nf, "get_ses_client", return_value=self.ses)
        self.get_client = p.start()
        self.addCleanup(p.stop)

    def test_insert_sends_mail(self):
        result = nf.lambda_handler(make_event(make_record()), None)
        self.ses.send_email.assert_called_once_with(
            Source=SENDER,
            Destination={"ToAddresses": [EMAIL]},
            Message={
                "Subject": {"Data": SUBJECT, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": BODY, "Charset": "UTF-8"}},
            },
        )
        self.assertEqual(result, {"sent": 1, "skipped": 0})

    def test_build_message(self):
        self.assertEqual(nf.build_message("山田太郎"), (SUBJECT, BODY))

    def test_modify_is_ignored(self):
        nf.lambda_handler(make_event(make_record("MODIFY")), None)
        self.ses.send_email.assert_not_called()

    def test_remove_is_ignored(self):
        nf.lambda_handler(make_event(make_record("REMOVE")), None)
        self.ses.send_email.assert_not_called()

    def test_missing_email_is_skipped(self):
        with self.assertLogs(level="WARNING") as cm:
            result = nf.lambda_handler(make_event(make_record(email=None)), None)
        self.assertNotIn("@", chr(10).join(cm.output))
        self.ses.send_email.assert_not_called()
        self.assertEqual(result, {"sent": 0, "skipped": 1})

    def test_empty_email_is_skipped(self):
        with self.assertLogs(level="WARNING") as cm:
            result = nf.lambda_handler(make_event(make_record(email="")), None)
        self.assertNotIn("@", chr(10).join(cm.output))
        self.ses.send_email.assert_not_called()
        self.assertEqual(result, {"sent": 0, "skipped": 1})

    def test_log_mode_does_not_call_ses(self):
        with patch.dict(os.environ, {"MAIL_MODE": "log"}):
            with self.assertLogs(level="INFO") as cm:
                result = nf.lambda_handler(make_event(make_record()), None)
        self.get_client.assert_not_called()
        self.ses.send_email.assert_not_called()
        self.assertIn(SUBJECT, "\n".join(cm.output))
        self.assertEqual(result, {"sent": 1, "skipped": 0})

    def test_log_mode_does_not_require_sender(self):
        env = {k: v for k, v in os.environ.items() if k != "SENDER"}
        env["MAIL_MODE"] = "log"
        with patch.dict(os.environ, env, clear=True):
            with self.assertLogs(level="INFO"):
                nf.lambda_handler(make_event(make_record()), None)

    def test_invalid_mail_mode_raises(self):
        with patch.dict(os.environ, {"MAIL_MODE": "bogus"}):
            with self.assertRaises(RuntimeError):
                nf.lambda_handler(make_event(make_record()), None)
        self.ses.send_email.assert_not_called()

    def test_missing_sender_raises(self):
        env = {k: v for k, v in os.environ.items() if k != "SENDER"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError):
                nf.lambda_handler(make_event(make_record()), None)
        self.ses.send_email.assert_not_called()

    def test_ses_client_error_is_reraised(self):
        self.ses.send_email.side_effect = ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "rejected"}}, "SendEmail"
        )
        with self.assertLogs(level="ERROR") as cm:
            with self.assertRaises(ClientError):
                nf.lambda_handler(make_event(make_record()), None)
        joined = "\n".join(cm.output)
        self.assertIn("MessageRejected", joined)
        self.assertNotIn(EMAIL, joined)

    def test_multiple_records(self):
        event = make_event(
            make_record(email="a@example.com", user_id="u-1"),
            make_record("MODIFY", email="b@example.com", user_id="u-2"),
            make_record(email="c@example.com", user_id="u-3"),
        )
        result = nf.lambda_handler(event, None)
        self.assertEqual(self.ses.send_email.call_count, 2)
        sent_to = [c.kwargs["Destination"]["ToAddresses"][0] for c in self.ses.send_email.call_args_list]
        self.assertEqual(sent_to, ["a@example.com", "c@example.com"])
        self.assertEqual(result["sent"], 2)

    def test_ses_mode_logs_do_not_contain_email(self):
        with self.assertLogs(level="INFO") as cm:
            nf.lambda_handler(make_event(make_record(), make_record(email=None)), None)
        joined = "\n".join(cm.output)
        self.assertNotIn(EMAIL, joined)
        self.assertIn("msg-123", joined)


if __name__ == "__main__":
    unittest.main()
