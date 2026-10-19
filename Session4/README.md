# Session4 — Amazon Bedrock で旅行先の料理をおすすめする

Session1 のサイトに入力された希望を HTTP API と Lambda 経由で Amazon Bedrock に送り、生成 AI から日本語の料理提案を受け取ります。

## 構成

```text
Session1 のブラウザー
   │ POST /v1/recommendations
   ▼
API Gateway HTTP API（us-east-1）
   │
   ▼
Lambda（Bedrock 呼び出し）
   │
   ▼
Amazon Bedrock Runtime（Claude Sonnet 4.6）
```

## 事前準備

- [Session1](../Session1/README.md)〜[Session3](../Session3/README.md) を完了する
- Session1 の CloudFront または Amplify のサイト URL を控える。S3 ウェブサイト URL を使う場合は `http://` から始まるオリジン全体を控える
- AWS アカウントで `us-east-1` の Amazon Bedrock と Claude Sonnet 4.6 推論プロファイルが利用できることを確認する。モデルの利用可否・アクセス申請はアカウントやリージョンにより異なる
- Session4 の API Gateway と Lambda は Bedrock Runtime と同じ `us-east-1` に作成する

> **料金と公開範囲**: Lambda から Bedrock を呼ぶたびにモデル利用料が発生します。短いテスト入力で試し、完了後は作成した API と Lambda を削除してください。API に認証はありません。API URL を知る人は利用できるため、URL を公開サイトや不特定多数へ配布しないでください。

## 1. Lambda 関数を作成する

1. AWS コンソールのリージョンを **米国東部（バージニア北部） `us-east-1`** に切り替える
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

1. リージョンが `us-east-1` のまま **API Gateway** を開く
2. **API を作成** → **HTTP API** → **構築** を選ぶ
3. 統合に Lambda の `travel-recommendation-<名前>` を選択し、API 名を `travel-recommendation-api-<名前>` にして作成する
4. ルートに `POST /v1/recommendations` を追加し、統合先が上記 Lambda であることを確認する
5. ステージは `$default`、自動デプロイを有効にして作成する
6. API の詳細に表示される URL（例: `https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com`）を控える。末尾の `/` は付けない

## 5. API の CORS を設定する

1. API Gateway で `travel-recommendation-api-<名前>` を開き **CORS** を選ぶ
2. 次の値を設定する

   | 項目 | 値 |
   |---|---|
   | 許可されたオリジン | 実際にサイトを開く URL のオリジン。CloudFront は `https://<CloudFront ドメイン>`、Amplify はデプロイされたブランチ URL、S3 ウェブサイトは `http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com` |
   | 許可されたメソッド | `POST`, `OPTIONS` |
   | 許可されたヘッダー | `content-type` |
   | 認証情報 | 無効 |

3. 保存する。`$default` ステージの自動デプロイが有効なら設定は自動反映される

ブラウザーで確認するときは実際の公開元 URL とスキームを許可します。ワイルドカード `*` は使わず、必要なオリジンだけを許可してください。HTTP API 側で CORS を設定するため、Lambda 側では CORS ヘッダーを追加しません。

## 6. Session1 のサイトに API URL を設定する

1. `Session1/config.js` を編集し、Session3 で設定した `API_ENDPOINT` を残したまま、次の行を追加する

   ```javascript
   window.BEDROCK_API_ENDPOINT = "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com";
   ```

2. S3 へ公開している場合は `Session1/index.html`、`Session1/app.js`、`config.js`、`styles.css`、`photo1.png`、`photo2.png` をバケット直下に再アップロードする。CloudFront を使う場合は `/*` を Invalidation する
3. Amplify を使う場合は環境変数 `BEDROCK_API_ENDPOINT` に API URL を追加して再デプロイする
4. Session1 のサイトを HTTPS（CloudFront または Amplify）で開き、おすすめ欄に「長野でそばを食べたい」などと入力してボタンを押す
5. Bedrock からの日本語回答が画面に表示されれば成功

> `config.js` の API URL はブラウザーから見える公開情報です。API キーや AWS 認証情報を JavaScript に書かないでください。この教材の API は認証されていないため、実験用の範囲で使ってください。

## 確認ポイント

- [ ] Lambda のテストで `statusCode: 200` が返る
- [ ] HTTP API に `POST /v1/recommendations` がある
- [ ] サイトのオリジンが API CORS で許可されている
- [ ] Session1 のサイトから日本語のおすすめを取得できる

## 片付け

1. API Gateway の `travel-recommendation-api-<名前>` を削除する
2. Lambda の `travel-recommendation-<名前>` を削除する
3. IAM に作成された実行ロールを削除する（他の関数で共有していないことを確認）

Bedrock への呼び出しは従量課金です。使い終わったら API を削除し、不要な呼び出しが続かないようにしてください。

Bedrock API は認証されないため、CORS と API URL を公開範囲に注意して管理してください。
