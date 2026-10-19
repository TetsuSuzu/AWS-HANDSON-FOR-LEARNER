# AWS ハンズオン（Session1〜4）

S3 で静的ウェブサイトを公開し、DynamoDB・Lambda・API Gateway で会員 API を作成します。Bedrock による料理のおすすめも追加します。

## セッションの流れ

| 順番 | セッション | 内容 |
|---|---|---|
| 0 | [Session0](Session0/README.md) | 教材を入手する（git clone または zip） |
| 1 | [Session1](Session1/README.md) | S3 静的ウェブサイトを作成・公開する |
| 2 | [Session2](Session2/README.md) | DynamoDB テーブルと Lambda 関数を作成・テストする |
| 3 | [Session3](Session3/README.md) | HTTP API を作成し、CORS とサイト接続を設定する |
| 4 | [Session4](Session4/README.md) | Amazon Bedrock で料理のおすすめを生成する |

Session0 で教材を入手してから、Session1〜4 を順番に進めてください。

## フォルダ構成

```text
Session1/
  README.md                 S3 静的サイト作成手順
  index.html                ウェブページ
  styles.css                ページのスタイル
  photo1.png, photo2.png    サイトで使用する画像
  config.js                 API URL の設定（Session3・4 で設定）
  Bucketpolicy.txt          公開読み取り用の例
Session2/
  README.md                 セッション案内
  01-dynamodb.md            DynamoDB 作成手順
  02-lambda.md              Lambda 作成・設定・テスト手順
  app.py                    Lambda の Python コード
  test-events/              Lambda テストイベント
Session3/
  README.md                 HTTP API、CORS、サイト公開・接続手順
Session4/
  README.md                 Bedrock API 作成手順
  lambda_function.py        Bedrock を呼び出す Lambda
  test-event.json           Lambda テストイベント
amplify.yml                 Amplify Hosting 用ビルド設定
```

## リソース名

Session1 の S3 バケット名に使う `lastname-firstname` と、Session2〜4 の `<名前>` には同じ個人名を使います（例: `yamada-taro`）。AWS のリソース名が他の受講者と重ならないようにしてください。

## 注意事項

- Session1 の S3 静的ウェブサイトは公開設定です。個人情報、パスワード、認証情報、秘密鍵などはアップロードしないでください。
- Session2〜4 で作成した AWS リソースは、ハンズオン終了後に各手順の案内に従って削除してください。特に Session4 の Bedrock 呼び出しは従量課金です。
