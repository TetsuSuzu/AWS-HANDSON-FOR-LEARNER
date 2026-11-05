# AWS ハンズオン（Session1〜9）

S3 に置いたファイルを Amplify で静的ウェブサイトとして公開し、DynamoDB・Lambda・API Gateway で会員 API を作成します。管理者用の会員管理画面を作り、Amazon Cognito でサインアップとログインを付けます。さらに、Bedrock による料理のおすすめも追加します。最後に、同じ会員 API を Aurora（リレーショナルデータベース）で作る Session8 で、DynamoDB との違いを体験します。

## セッションの流れ

| 順番 | セッション | 内容 |
|---|---|---|
| 0 | [Session0](Session0/README.md) | 教材を入手する（git clone または zip） |
| 1 | [Session1](Session1/README.md) | S3 にファイルを置き、Amplify で静的ウェブサイトを公開する |
| 2 | [Session2](Session2/README.md) | DynamoDB テーブルと Lambda 関数を作成・テストする |
| 3 | [Session3](Session3/README.md) | HTTP API を作成し、CORS とサイト接続を設定する |
| 4 | [Session4](Session4/README.md) | 管理者用の会員管理画面（一覧・更新・削除）を作成する |
| 5 | [Session5](Session5/README.md) | Amazon Cognito でサインアップとログインを付ける |
| 6 | [Session6](Session6/README.md) | Amazon Bedrock で料理のおすすめを生成する |
| 7 | [Session7](Session7/README.md) | 店リストを tool_use で読み、回答の精度を比べる |
| 8 | [Session8](Session8/README.md) | Aurora（PostgreSQL 互換）で会員 API を作る（任意・従量課金） |
| 9 | [Session9](Session9/README.md) | GitHub Actions と AWS を OIDC でつなぐ（任意・本編では使わない参考手順） |

Session0 で教材を入手してから、Session1〜7 を順番に進めてください。Session8 は Session4 までの後であれば、いつでも取り組めます。

## フォルダ構成

```text
AWS-HANDSON-FOR-LEARNER/
├── Session0/                  教材の入手手順（git clone / zip）
│   └── README.md
├── Session1/                  静的サイト（HTML・JavaScript・CSS）を S3 と Amplify で公開
│   ├── README.md              S3・Amplify の手順
│   ├── index.html             ウェブページ（HTML）
│   ├── app.js                 ページの動き（JavaScript）
│   ├── admin.html             管理者用の会員管理画面（Session4 で別の S3 バケットと Amplify アプリに置く）
│   ├── admin.js               会員管理画面の動き（JavaScript）
│   ├── config.js              API URL の設定（Session3・4・5・7 で設定）
│   ├── styles.css             ページのデザイン（CSS）
│   ├── photo1.png             画像（おすすめ風景①）
│   └── photo2.png             画像（おすすめ風景②）
├── Session2/                  DynamoDB と Lambda（会員 API）
│   ├── README.md              セッション案内
│   ├── 01-dynamodb.md         DynamoDB の作成手順
│   ├── 02-lambda.md           Lambda の作成・設定・テスト手順
│   ├── lambda_function.py     会員 API の Lambda コード
│   └── test-events/           Lambda のテストイベント
│       ├── create-user.json
│       └── list-users.json
├── Session3/                  HTTP API と CORS
│   └── README.md
├── Session4/                  会員管理画面（管理 API の Lambda）
│   ├── README.md
│   ├── lambda_function.py     一覧・取得・更新・削除の Lambda コード
│   └── test-events/           Lambda のテストイベント
│       ├── list-users.json
│       ├── update-user.json
│       └── delete-user.json
├── Session5/                  Cognito でサインアップとログイン
│   ├── README.md
│   ├── lambda_function.py     会員 API の本人確認の Lambda コード
│   ├── admin_lambda_function.py  管理 API の管理者確認の Lambda コード
│   ├── test-events/           Lambda のテストイベント
│   ├── test_member_lambda.py  会員 API の確認テスト
│   └── test_admin_lambda.py   管理 API の確認テスト
├── Session6/                  Bedrock で料理のおすすめ
│   ├── README.md
│   ├── lambda_function.py     Bedrock を呼び出す Lambda コード
│   └── test-event.json        Lambda のテストイベント
├── Session7/                  店リストを tool_use で読み、回答の精度を比べる
│   ├── README.md
│   ├── lambda_function.py     店リストを読む Lambda コード
│   ├── shops.txt              ランチマップから作った店リスト
│   └── test-event.json        Lambda のテストイベント
├── Session8/                  Aurora で会員 API（SQL・Data API）
│   ├── README.md
│   ├── schema.sql             users テーブルを作る SQL
│   ├── lambda_function.py     Data API で SQL を実行する Lambda コード
│   └── test-events/           Lambda のテストイベント
│       ├── create-user.json
│       ├── list-users.json
│       ├── update-user.json
│       └── delete-user.json
├── Session9/                  GitHub Actions と AWS の OIDC 連携（任意）
│   └── README.md
├── README.md                  この案内
└── CONTRIBUTING.md            リポジトリ管理者向けの手順書
```

## リソース名

Session1 の S3 バケット名に使う `lastname-firstname`（管理画面用は Session4 で `lastname-firstname-admin`。Amplify のアプリ名は `site-<名前>`、`admin-<名前>`）と、Session2〜7 の `<名前>` には同じ個人名を使います（例: `yamada-taro`）。AWS のリソース名が他の受講者と重ならないようにしてください。

## 注意事項

- Session1 の Amplify のサイトは、誰でも閲覧できる公開設定です。個人情報、パスワード、認証情報、秘密鍵などはアップロードしないでください。
- Session2〜7 で作成した AWS リソースは、ハンズオン終了後に各手順の案内に従って削除してください。特に Session6・7 の Bedrock 呼び出しは従量課金です。Session5 の Cognito のユーザープールは、会員のメールアドレスを持つため、使い終わったら削除してください。Session8 の Aurora は起動している間ずっと課金されるため、研修後に必ず片付けてください。
- Session4 の管理画面と管理 API には、Session5 で Cognito のログインを付けるまで認証がありません。URL を知る人は誰でも会員の閲覧・更新・削除ができます。テスト用のデータだけを登録し、研修が終わったら管理 API と、管理画面用の Amplify アプリと S3 バケットを削除してください。
