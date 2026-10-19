# AWS ハンズオン（Session1〜7）

S3 で静的ウェブサイトを公開し、DynamoDB・Lambda・API Gateway で会員 API を作成します。Bedrock による料理のおすすめと、Cognito 認証も追加します。

## セッションの流れ

| 順番 | セッション | 内容 |
|---|---|---|
| 事前 | [Session0](Session0/README.md) | ハンズオン環境のセットアップ |
| 1 | [Session1](Session1/README.md) | S3 静的ウェブサイトを作成・公開する |
| 2 | [Session2](Session2/README.md) | DynamoDB テーブルと Lambda 関数を作成・テストする |
| 3 | [Session3](Session3/README.md) | HTTP API を作成し、CORS とサイト接続を設定する |
| 4 | [Session4](Session4/README.md) | Amazon Bedrock で料理のおすすめを生成する |
| 5 | [Session5](Session5/README.md) | Cognito ログインで会員 API を保護する |
| 7 | [Session7](Session7/README.md) | 管理者用会員管理（旧教材） |

まず Session0 を完了してから Session1〜5 を順番に進めてください。Session7 は旧教材として残しています。新しい API のリソース名・構成とは互換性がない部分があるため、続けて実施する場合は各手順を読み替えてください。

## フォルダ構成

```text
Session1/
  README.md                 S3 静的サイト作成手順
  index.html                ウェブページ
  styles.css                ページのスタイル
  photo1.png, photo2.png    サイトで使用する画像
  config.js                 API URL・Cognito 設定（Session3〜5 で設定）
  auth.js                   Cognito ログイン／ログアウトと認証 API 呼び出し
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
Session5/
  README.md                 Cognito と JWT 認証の設定手順
amplify.yml                 Amplify Hosting 用ビルド設定
```

## リソース名

Session1 の S3 バケット名に使う `lastname-firstname` と、Session2〜5 の `<名前>` には同じ個人名を使います（例: `yamada-taro`）。AWS のリソース名が他の受講者と重ならないようにしてください。

## 注意事項

- Session1 の S3 静的ウェブサイトは公開設定です。個人情報、パスワード、認証情報、秘密鍵などはアップロードしないでください。
- Session2〜5 で作成した AWS リソースは、ハンズオン終了後に各手順の案内に従って削除してください。特に Session4 の Bedrock 呼び出しは従量課金です。
- Session5 の Cognito を設定するまでは会員 API に認証がありません。テスト用のデータだけを使用し、個人情報を登録しないでください。
- `Session7` は以前の教材を繰り下げて残しています。旧リソース名や構成を前提とするため、新 Session1〜5 との互換性を確認してから実施してください。
