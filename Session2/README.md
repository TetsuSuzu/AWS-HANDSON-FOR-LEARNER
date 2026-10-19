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

## コードの読み方（app.py・初心者向け）

`app.py` は、API から呼ばれて会員データを DynamoDB に保存・取得・削除する Python のプログラムです。全体は次の順番で動きます。

1. API Gateway から要求が届く（例: `POST /v1/users`）
2. Lambda が `handler` を呼ぶ
3. `handler` が `ROUTES` の表で、要求に対応する処理を選ぶ
4. 選ばれた処理（`create_user` など）が、DynamoDB を読み書きする
5. 結果を `respond` で作り、API に返す

### 用語の説明

| 用語 | 意味 |
|---|---|
| Python | プログラムを書く言語の一つです。文の終わりにセミコロンを付けず、字下げ（インデント）で処理のまとまりを表します |
| `import` | ほかのプログラムの道具を借りる命令です。例: `import json` は、JSON を扱う道具を使えるようにします |
| `def` | 関数（処理のまとまり）を作る言葉です。define（定義する）の略です。`def create_user(event):` のように書きます |
| `class` | 自分用のデータの種類を作る言葉です。このファイルでは、エラーの種類を作るために使っています |
| `try` / `except` | `try` は「試す」、`except` は「エラーを受け止める」という意味です。JavaScript の `try` / `catch` と同じ役割です |
| 辞書（dict） | `{"キー": 値}` の形で、名前と中身を対にして入れるデータです。JSON とよく似ています |
| `None` | 「何もない」を表す値です。JavaScript の `null` と同じ役割です |
| `event` | API Gateway から届く、要求の中身です。`body`（送られたデータ）や `routeKey`（メソッドとパス）が入っています |
| `context` | Lambda の実行情報です。このプログラムでは使っていません |
| `handler` | Lambda が最初に呼ぶ関数です。Lambda の画面の「ハンドラー」に、`lambda_function.handler` などと書いて教えます |
| `routeKey` | `POST /v1/users` のような、「メソッドとパスの組み合わせ」です |
| `os.environ` | Lambda の環境変数（外から渡す設定）を読むための場所です。`TABLE_NAME` を読んでいます |
| 正規表現（`re`） | 文字の形のルールを書く方法です。`EMAIL_PATTERN` は、メールアドレスの形かどうかを調べるルールです |
| DynamoDB | AWS のデータベースです。`users-table-<名前>` という表に会員を保存します |
| `boto3` | Python から AWS を操作するための道具箱です |

### 主な部分の説明

- **`TABLE_NAME`**: 読み書きするテーブル名です。環境変数で設定し、なければ `users` を使います。
- **`FIELDS`**: 会員データの項目名の一覧（リスト）です。`[ ]` で書き、`,` で区切ります。
- **`_table` と `get_table()`**: テーブルへの接続を、最初の 1 回だけ作って使い回します。
- **`respond(status, body)`**: API に返す結果を作ります。`statusCode` が結果の番号、`body` が中身の JSON の文字です。
- **`parse_user(raw)`**: 送られてきたデータを検査します。必須項目がない、年齢が数字でない、メールアドレスの形が正しくない、などを見つけたら `ApiError` を発生させます。
- **`create_user(event)`**: 会員を登録します。`put_item` は「保存」、`ConditionExpression="attribute_not_exists(id)"` は「同じ ID がまだないときだけ保存する」という条件です。
- **`get_user(user_id)`**: 1 件取得します（`get_item`）。
- **`list_users(query)`**: 全件を取得します（`scan`）。一度に取る件数は `limit` で決め、`nextToken` で次のページを取ります。
- **`update_user(user_id, event)`**: 会員の内容を書き換えます（`put_item`）。
- **`delete_user(user_id)`**: 会員を削除します（`delete_item`）。
- **`ROUTES`**: `"POST /v1/users"` という文字と、呼び出す関数の対応表です。
- **`handler(event, context)`**: 要求の `routeKey` を `ROUTES` で探し、対応する処理を実行します。`except ApiError` は想定内のエラー、`except Exception` は想定外のエラーです。想定外のエラーは詳細を返さず、CloudWatch Logs に記録します。

### 返す番号（statusCode）の意味

| 番号 | 意味 |
|---|---|
| 200 | 成功（取得・更新） |
| 201 | 成功（新しく作った） |
| 204 | 成功（本文なし。削除） |
| 400 | 送られたデータが正しくない |
| 404 | 対象の会員が見つからない |
| 409 | 同じ ID がすでにある |
| 500 | サーバー内部のエラー |

### テストイベント（test-events フォルダ）

テストイベントは、API Gateway が送ってくるはずの要求を、手で作った例です。Lambda の画面で「テスト」を押すときに使います。

- `routeKey`: どの処理を呼ぶかを決めます（例: `POST /v1/users`）。
- `body`: 送るデータです。JSON を文字にした中に、もう一度 JSON が入っているため、`\"` のように `\` で引用符を書いています。
- `queryStringParameters`: URL の `?limit=20` のような部分です。

---

## 命名

| リソース | 名前 |
|---|---|
| DynamoDB テーブル | `users-table-<名前>` |
| Lambda 関数 | `users-function-<名前>` |
| Lambda 実行ロール | 関数作成時に生成されたロール |
