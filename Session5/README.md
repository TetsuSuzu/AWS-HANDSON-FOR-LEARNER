# Session5 — Amazon Bedrock で旅行先の料理をおすすめする

> このセッションのコードは [gist](https://gist.github.com/TetsuSuzu/db058114db872972033f5bef4b347108) にあります。使うファイルを開き、中身をコピーして使えます。

利用者の希望を HTTP API と Lambda 経由で Amazon Bedrock に送り、生成 AI から日本語の料理提案を受け取ります。

## 構成

```text
Session1 のブラウザー
   │ POST（API の URL そのもの。パスなし）
   ▼
API Gateway HTTP API（ap-northeast-1）
   │
   ▼
Lambda（Bedrock 呼び出し）
   │
   ▼
Amazon Bedrock Runtime（Claude Sonnet 4.6）
```

## 事前準備

- [Session1](../Session1/README.md)〜[Session4](../Session4/README.md) を完了する
- Session1 の S3 ウェブサイト URL を控える。`http://` から始まるオリジン全体を控える
- AWS アカウントで `ap-northeast-1`（東京）の Amazon Bedrock と Claude Sonnet 4.6 推論プロファイルが利用できることを確認する。モデルの利用可否・アクセス申請はアカウントやリージョンにより異なる
- Session5 の API Gateway と Lambda は、Session2・Session3 と同じ `ap-northeast-1`（東京）に作成する

> **料金と公開範囲**: Lambda から Bedrock を呼ぶたびにモデル利用料が発生します。短いテスト入力で試し、完了後は作成した API と Lambda を削除してください。API に認証はありません。API URL を知る人は利用できるため、URL を公開サイトや不特定多数へ配布しないでください。

## コードの読み方（lambda_function.py）

`lambda_function.py` は、料理の希望を受け取り、Amazon Bedrock（生成 AI）に質問して、おすすめの答えを返す Python のプログラムです。

### 用語の説明

| 用語 | 意味 |
|---|---|
| `import` | ほかのプログラムの道具を借りる命令です。`json`（JSON を扱う）、`logging`（ログを残す）、`boto3`（AWS を操作する道具箱）を読み込んでいます |
| `boto3` | Python から AWS を操作するための道具箱です |
| Bedrock | AWS が提供する生成 AI のサービスです。文章で質問すると、文章で答えてくれます |
| モデル | 生成 AI の本体です。`MODEL_ID` で、どのモデルを使うかを指定します |
| プロンプト | AI に送る質問や指示の文章です。この教材では、ユーザーが入力した希望がプロンプトになります |
| `logger` | 実行中の記録（ログ）を残す道具です。エラーの原因を調べるときに、CloudWatch Logs で見られます |
| `ClientError` | AWS の呼び出しで起きたエラーの種類です |
| 関数（`def`） | 処理のまとまりに名前を付けたものです。`def respond(...)` は、結果の形を作る関数です |

### 1 行ずつの説明（主な部分）

- `bedrock = boto3.client("bedrock-runtime", region_name="ap-northeast-1")`
  - Bedrock と通信するための接続を作ります。`region_name` は、Bedrock を使う AWS のリージョン（場所）です。
- `MODEL_ID = os.environ["MODEL_ID"]`
  - 使う AI モデルの名前です。値は、コードではなく Lambda の環境変数から読みます。そのため、モデルを変えるときはコードを書き換えず、環境変数の値だけを変えます。
- `MAX_PROMPT_LENGTH = 1000`
  - 入力できる文字数の上限です。長すぎる入力は、ここで弾きます。
- `def lambda_handler(event, context):`
  - Lambda が最初に呼ぶ関数です。`event` は API からの要求、`context` は Lambda の実行情報です。
- `body = json.loads(event.get("body") or "{}")`
  - 送られてきたデータ（JSON の文字）を、Python のデータに変換します。`or "{}"` は、データがないときは空の辞書を使うという意味です。
- `prompt = body.get("prompt")`
  - データの中から、`prompt` の項目（ユーザーの希望）を取り出します。
- `if not isinstance(prompt, str) or not prompt.strip(): ...`
  - 「文字であること」「空でないこと」を確かめます。違えば、400（入力が正しくない）を返します。
- `request_body = {...}`
  - AI に送るデータを作ります。
  - `system`: AI の役割を決める指示です（「旅行と郷土料理に詳しいアドバイザー」）。
  - `messages`: ユーザーの質問です。
  - `max_tokens`: 返事の長さの上限です。トークンは、AI が文章を扱うときの最小の単位です。
  - `temperature`: 返事のゆらぎを決めます。0 に近いほど決まった答えになり、高いほど多様になります。
- `response = bedrock.invoke_model(...)`
  - Bedrock のモデルを呼び出して、返事を待ちます。
- `result = json.loads(response["body"].read())`
  - 返事を読み取り、Python のデータに変換します。
- `answer = result["content"][0]["text"]`
  - 返事の中から、文章の部分を取り出します。`[0]` は、最初の返事という意味です。
- `return respond(200, {"answer": answer})`
  - 成功したときは、200 と `answer` を返します。
- `except (ClientError, KeyError, ...):`
  - 途中でエラーが起きたら、エラーを記録して、502（外部の処理が失敗した）を返します。

### テストイベント（test-event.json）

テストイベントは、API Gateway が送ってくるはずの要求を、手で作った例です。Lambda の画面で「テスト」を押すときに使います。

- `routeKey`: `POST /` を指定し、このプログラムを呼び出します。
- `body`: 希望の文章です。JSON の文字の中にもう一度 JSON が入っているため、`\"` のように書いています。

---

## 1. Lambda 関数を作成する

1. AWS コンソールのリージョンを **アジアパシフィック（東京） `ap-northeast-1`** に切り替える
2. **Lambda** → **関数の作成** → **一から作成** を選ぶ
3. 次の設定で作成する

   | 項目 | 値 |
   |---|---|
   | 関数名 | `travel-recommendation-<名前>` |
   | ランタイム | Python 3.12 |
   | アーキテクチャ | x86_64 |
   | 実行ロール | 基本的な Lambda のアクセス権限で新しいロールを作成 |

4. 関数の **コード** タブで `lambda_function.py` の初期コードをすべて削除し、このフォルダの `lambda_function.py` の内容を貼り付ける
5. **Deploy（デプロイ）** をクリックする。ハンドラーは `lambda_function.lambda_handler` にする
6. **設定** → **一般設定** → **編集** でタイムアウトを **1 分** にする

### 環境変数 MODEL_ID を設定する

このプログラムは、使う AI モデルを環境変数 `MODEL_ID` から読みます。設定しないと、Lambda は起動時にエラー（`KeyError: 'MODEL_ID'`）になります。

1. Lambda の画面で **設定** タブ → **環境変数** → **編集**
2. **環境変数を追加** をクリックし、次を入力する

   | キー | 値 |
   |---|---|
   | `MODEL_ID` | `global.anthropic.claude-sonnet-4-6` |

3. **保存**

> **モデルを変えたいとき**: コードは変えず、この値だけを変えて保存します。変える前に、東京リージョン（`ap-northeast-1`）の Bedrock でそのモデルが使えるかを確認してください。

## 2. Lambda 実行ロールに Bedrock 権限を付ける

1. Lambda の **設定** → **アクセス権限** を開き、実行ロール名をクリックする
2. IAM ロールで **許可を追加** → **インラインポリシーを作成** → **JSON** を選ぶ
3. 次のポリシーを貼り付ける

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "bedrock:InvokeModel",
         "Resource": [
           "arn:aws:bedrock:*:<アカウントID>:inference-profile/global.anthropic.claude-sonnet-4-6",
           "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6"
         ]
       }
     ]
   }
   ```

4. ARN 中の `<アカウントID>` を自分の AWS アカウント ID に置き換え、ポリシー名を `bedrock-invoke-model-<名前>` として作成する

> このポリシーは Claude Sonnet 4.6 のグローバル推論プロファイルと、クロスリージョン先の同モデル呼び出しに限定します。推論プロファイルを使う場合は、プロファイル ARN と利用先の foundation model ARN の両方が必要です。Bedrock 側のモデル利用条件も満たしている必要があります。

## 3. Lambda 単体でテストする

1. **テスト** → **新しいイベントを作成** を選択する
2. イベント名を `recommendation-test` にし、`test-event.json` の内容を貼り付けて保存する
3. **テスト** を実行する
4. `statusCode` が `200` で、本文の `answer` に日本語の提案があれば成功

入力が不正な場合は 400、Bedrock 呼び出しで失敗した場合は 502 が返ります。失敗時は Lambda の **モニタリング** → **CloudWatch Logs** で詳細を確認してください。

## 4. HTTP API を作成する

1. リージョンが `ap-northeast-1` のまま **API Gateway** を開く
2. **API を作成** → **HTTP API** → **構築** を選ぶ
3. 統合に Lambda の `travel-recommendation-<名前>` を選択し、API 名を `travel-recommendation-api-<名前>` にして作成する
4. ルートに `POST /`（パスなし）を追加し、統合先が上記 Lambda であることを確認する
5. ステージ名は `dev`（初期値の `$default` から書き換える）、自動デプロイを有効にして作成する
6. ステージ `dev` の URL（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev`）を控える。末尾の `/` は付けない

## 5. API の CORS を設定する

1. API Gateway で `travel-recommendation-api-<名前>` を開き **CORS** を選ぶ
2. 次の値を設定する

   | 項目 | 値 |
   |---|---|
   | 許可されたオリジン | 実際にサイトを開く URL のオリジン。S3 ウェブサイトは `http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com` |
   | 許可されたメソッド | `POST`, `OPTIONS` |
   | 許可されたヘッダー | `content-type` |
   | 認証情報 | 無効 |

3. 保存する。`dev` ステージの自動デプロイが有効なら設定は自動反映される

ブラウザーで確認するときは実際の公開元 URL とスキームを許可します。ワイルドカード `*` は使わず、必要なオリジンだけを許可してください。HTTP API 側で CORS を設定するため、Lambda 側では CORS ヘッダーを追加しません。

## 6. API の URL で動作を確かめる

この API の URL は、PowerShell などから直接呼び出して確かめます。Session1 のサイトのおすすめ欄は、Session6 の API を使います（Session6 で設定します）。

1. API Gateway の `travel-recommendation-api-<名前>` のステージ `dev` の URL（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev`）を控える。末尾に `/` は付けない
2. PowerShell で、次のように呼び出す

   ```powershell
   $api = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev"
   $body = '{"prompt":"長野でそばを食べたい"}'
   $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
   (Invoke-RestMethod -Method Post -Uri $api -ContentType "application/json; charset=utf-8" -Body $bytes).answer
   ```

3. Bedrock からの日本語回答が表示されれば成功です

> `config.js` の API URL はブラウザーから見える公開情報です。API キーや AWS 認証情報を JavaScript に書かないでください。この教材の API は認証されていないため、実験用の範囲で使ってください。

## 確認ポイント

- [ ] Lambda のテストで `statusCode: 200` が返る
- [ ] HTTP API に `POST /`（パスなし）がある
- [ ] サイトのオリジンが API CORS で許可されている
- [ ] PowerShell で、日本語のおすすめを取得できる

## 片付け

1. API Gateway の `travel-recommendation-api-<名前>` を削除する
2. Lambda の `travel-recommendation-<名前>` を削除する
3. IAM に作成された実行ロールを削除する（他の関数で共有していないことを確認）

Bedrock への呼び出しは従量課金です。使い終わったら API を削除し、不要な呼び出しが続かないようにしてください。

Bedrock API は認証されないため、CORS と API URL を公開範囲に注意して管理してください。
