# AWS ハンズオン（Session1〜6）

S3 で静的ウェブサイトを公開し、DynamoDB・Lambda・API Gateway で会員 API を作成します。管理者用の会員管理画面と、Bedrock による料理のおすすめも追加します。

## セッションの流れ

| 順番 | セッション | 内容 |
|---|---|---|
| 0 | [Session0](Session0/README.md) | 教材を入手する（git clone または zip） |
| 1 | [Session1](Session1/README.md) | S3 静的ウェブサイトを作成・公開する |
| 2 | [Session2](Session2/README.md) | DynamoDB テーブルと Lambda 関数を作成・テストする |
| 3 | [Session3](Session3/README.md) | HTTP API を作成し、CORS とサイト接続を設定する |
| 4 | [Session4](Session4/README.md) | 管理者用の会員管理画面（一覧・更新・削除）を作成する |
| 5 | [Session5](Session5/README.md) | Amazon Bedrock で料理のおすすめを生成する |
| 6 | [Session6](Session6/README.md) | 店リストを tool_use で読み、回答の精度を比べる |

Session0 で教材を入手してから、Session1〜6 を順番に進めてください。

## フォルダ構成

```text
AWS-HANDSON-FOR-LEARNER/
├── Session0/                  教材の入手手順（git clone / zip）
│   └── README.md
├── Session1/                  S3 静的サイト（HTML・JavaScript・CSS）
│   ├── README.md              S3 作成手順
│   ├── index.html             ウェブページ（HTML）
│   ├── app.js                 ページの動き（JavaScript）
│   ├── admin.html             管理者用の会員管理画面（Session4 で別の S3 バケットに置く）
│   ├── admin.js               会員管理画面の動き（JavaScript）
│   ├── config.js              API URL の設定（Session3・4・6 で設定）
│   ├── styles.css             ページのデザイン（CSS）
│   ├── photo1.png             画像（おすすめ風景①）
│   ├── photo2.png             画像（おすすめ風景②）
│   └── Bucketpolicy.txt       公開読み取り用のバケットポリシー例
├── Session2/                  DynamoDB と Lambda（会員 API）
│   ├── README.md              セッション案内
│   ├── 01-dynamodb.md         DynamoDB の作成手順
│   ├── 02-lambda.md           Lambda の作成・設定・テスト手順
│   ├── app.py                 会員 API の Lambda コード
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
├── Session5/                  Bedrock で料理のおすすめ
│   ├── README.md
│   ├── lambda_function.py     Bedrock を呼び出す Lambda コード
│   └── test-event.json        Lambda のテストイベント
├── Session6/                  店リストを tool_use で読み、回答の精度を比べる
│   ├── README.md
│   ├── lambda_function.py     店リストを読む Lambda コード
│   ├── shops.txt              ランチマップから作った店リスト
│   └── test-event.json        Lambda のテストイベント
├── amplify.yml                Amplify Hosting 用のビルド設定
├── README.md                  この案内
└── CONTRIBUTING.md            リポジトリ管理者向けの手順書
```

## リソース名

Session1 の S3 バケット名に使う `lastname-firstname`（管理画面用は Session4 で `lastname-firstname-admin`）と、Session2〜6 の `<名前>` には同じ個人名を使います（例: `yamada-taro`）。AWS のリソース名が他の受講者と重ならないようにしてください。

## 注意事項

- Session1 の S3 静的ウェブサイトは公開設定です。個人情報、パスワード、認証情報、秘密鍵などはアップロードしないでください。
- Session2〜6 で作成した AWS リソースは、ハンズオン終了後に各手順の案内に従って削除してください。特に Session5・6 の Bedrock 呼び出しは従量課金です。
- Session4 の管理画面と管理 API には認証がありません。URL を知る人は誰でも会員の閲覧・更新・削除ができます。テスト用のデータだけを登録し、研修が終わったら管理 API と、管理画面用の S3 バケットを削除してください。
