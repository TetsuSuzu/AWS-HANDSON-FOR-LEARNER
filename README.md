# 学習者向け AWSハンズオン 実施手順書

## はじめに — 事前準備

### ステップ1：ハンズオン資料をダウンロードする

ハンズオンで使用するファイル（HTML・CSS・画像など）を以下の手順でPCにダウンロードします。

1. **このページ** の右上の緑色の **「Code」** ボタンをクリック
2. 表示されたメニューの **「Download ZIP」** をクリック
3. ダウンロードされた ZIP ファイルを **デスクトップ** に移動する
4. ZIP ファイルを右クリック →「すべて展開...」→ 展開先を **デスクトップ** に指定して「展開」をクリック

> 展開後、デスクトップに `aws-handson-main` などのフォルダが作成されます。  
> 各 Session のフォルダ（`Session1`・`Session2`・`Session3`）の中にアップロード用ファイルが入っています。

### ステップ2：AWSアカウントを払い出す

以下のURLをブラウザで開き、**自分のメールアドレス** を入力してください。  
イベントコードを聞かれたら **`f301-06eddc-8f`** を入力してください。

```
https://catalog.us-east-1.prod.workshops.aws/join?access-code=f301-06eddc-8f
```

> AWSアカウントの払い出しが完了しないと、Session1以降の作業が行えません。

---

バケット名・ロール名などの <font color="red">lastname-firstname</font> は **自分の名前（姓-名）** に置き換えてください。  
例: `suzuki-tetsuya`

> ⚠️ <font color="red">赤字</font> の箇所はすべて **受講生ごとに異なる個人の名前** です。他の人と重複しないよう、必ず自分の名前を使ってください。

---

## 完成サイト一覧

| サイト | URL |
|---|---|
| 勉強会サイト（Session1〜3統合） | https://xxxxxxxxxxxx.cloudfront.net/ |
| 会員登録確認画面（管理者向け） | http://lastname-firstname-admin.s3-website-ap-northeast-1.amazonaws.com/ |

> ※ 会員登録確認画面（管理者向け）は、こちらのサイトは作成しません。

---

## Session1 — S3静的サイトホスティング（ランディングページ）

### 1. S3バケット作成

| 項目 | 値 |
|------|-----|
| バケット名 | <font color="red">lastname-firstname</font> |

> ※ <font color="red">lastname-firstname</font> は自分の名前に置き換えてください（例：`yamada-taro`）。

### 2. オブジェクトのアップロード

以下のファイルをバケット直下にアップロードする。

- `index.html`
- `photo1.png`
- `photo2.png`
- `styles.css`

### 3. 静的ウェブサイトホスティングの設定

| 項目 | 値 |
|------|-----|
| 静的ウェブサイトホスティング | 有効にする |
| インデックスドキュメント | `index.html` |

### 4. パブリックアクセスの設定

- 「ブロックパブリックアクセス (バケット設定)」→「パブリックアクセスをすべてブロック」の **チェックを外す**

### 5. バケットポリシーの設定

`Bucketpolicy.txt` の内容を貼り付ける（バケット名を自分のものに変更）。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::lastname-firstname/*"
        }
    ]
}
```

---

## Session2 — 会員申込アプリ（IAM + Lambda + DynamoDB）

### 1. IAMロール作成

| 項目 | 値 |
|------|-----|
| サービスまたはユースケース | Lambda |
| 許可ポリシー | `AmazonDynamoDBFullAccess` / `AWSLambdaBasicExecutionRole` / `AmazonBedrockFullAccess` |
| ロール名 | <font color="red">lastname-firstname</font> |

> ※ <font color="red">lastname-firstname</font> は自分の名前に置き換えてください（例：`yamada-taro`）。  
> このロールは Session3 でも使い回します。

### 2. Lambda関数作成

| 項目 | 値 |
|------|-----|
| 関数名 | <font color="red">users-post-function-lastname-firstname</font> |
| ランタイム | Python 3.12 |
| 実行ロール | 既存のロールを使用 → <font color="red">lastname-firstname</font> |

コードは `lambda_function.py` の内容を貼り付ける。

---

## Session3 — AI連携（Lambda + API Gateway + Bedrock）

### 1. Lambda関数作成

| 項目 | 値 |
|------|-----|
| 関数名 | <font color="red">lastname-firstname-b</font> |
| ランタイム | Python 3.12 |
| 実行ロール | 既存のロールを使用 → <font color="red">lastname-firstname</font> |

> ※ <font color="red">lastname-firstname-b</font> は自分の名前に置き換えてください（例：`yamada-taro-b`）。

作成後、**「一般設定」→「編集」からタイムアウトを「3分」に変更**する。

コードは `lambda-bedrock.txt` の内容を貼り付ける。

### 3. API Gatewayの設定

| 項目 | 値 |
|------|-----|
| APIタイプ | REST API |
| API名 | <font color="red">lastname-firstname-b</font> |
| リソース名 | <font color="red">lastname-firstname-b</font> |

詳細手順は **[Session3/README.md](Session3/README.md)** を参照してください。
