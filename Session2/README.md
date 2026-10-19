# Session2 — DynamoDB と Lambda で会員 API の処理を作る

先に [Session0](../Session0/README.md) で教材を入手し、[Session1](../Session1/README.md) で S3 静的サイトを作成してください。このセッションでは、そのサイトから使う会員 API の処理を DynamoDB と Lambda で作成します。Session2 では Lambda 単体のテストまで行い、HTTP API への接続は Session3 で設定します。

## このセッションで作るもの

```text
Lambda（users-function-<名前>）
   │
   └── DynamoDB（users-table-<名前>）
```

## 事前準備

- AWS マネジメントコンソールのリージョンを **アジアパシフィック（東京）ap-northeast-1** にする
- `<名前>` は半角英数字で自分の名前に置き換え、Session2 と Session3 で同じ名前を使う

## 手順

1. [DynamoDB テーブルを作成する](01-dynamodb.md)
2. [Lambda 関数を作成し、コードを設定してテストする](02-lambda.md)
3. Session3 の [HTTP API を作成して接続する](../Session3/README.md) に進む

## このフォルダのファイル

| ファイル | 用途 |
|---|---|
| `01-dynamodb.md` | DynamoDB テーブル作成手順 |
| `02-lambda.md` | Lambda の作成、権限設定、テスト手順 |
| `app.py` | Lambda 関数のコード。コンソール貼り付けまたは PowerShell zip アップロードで使用 |
| `test-events/create-user.json` | 会員登録 Lambda テスト用イベント |
| `test-events/list-users.json` | 会員一覧 Lambda テスト用イベント |

## 命名

| リソース | 名前 |
|---|---|
| DynamoDB テーブル | `users-table-<名前>` |
| Lambda 関数 | `users-function-<名前>` |
| Lambda 実行ロール | 関数作成時に生成されたロール |
