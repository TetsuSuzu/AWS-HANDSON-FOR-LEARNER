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

---

バケット名・ロール名などの <font color="red">lastname-firstname</font> は **自分の名前（姓-名）** に置き換えてください。  
例: `suzuki-tetsuya`

> ⚠️ <font color="red">赤字</font> の箇所はすべて **受講生ごとに異なる個人の名前** です。他の人と重複しないよう、必ず自分の名前を使ってください。

---

## コード一覧（Gist）

ハンズオンで使用するコードをGistで公開しています。コピーしてご利用ください。

| Session | 内容 | リンク |
|---|---|---|
| Session1 | S3バケットポリシー | https://gist.github.com/TetsuSuzu/52ac3992fedf13078686a3a1001c8540 |
| Session2 | Lambda関数（DynamoDB登録） | https://gist.github.com/TetsuSuzu/bc7e8259462a96c11dc58b75f61a58d3 |
| Session2 | Lambdaテストイベント | https://gist.github.com/TetsuSuzu/1ff21322a9206bd40d6430cd0b7c9f28 |
| Session3 | Lambda関数（Bedrock AI連携） | https://gist.github.com/TetsuSuzu/cac498a24fc62682afc73427c3e7412e |

---

## 完成サイト一覧

| サイト | URL |
|---|---|
| 勉強会サイト（Session1〜3統合） | https://d69f16572v74l.cloudfront.net/ |
| 会員登録確認画面（管理者向け） | http://lastname-firstname-admin.s3-website-ap-northeast-1.amazonaws.com/ |

> ※ 会員登録確認画面（管理者向け）は、こちらのサイトは作成しません。
> ※ 上記サイトは受講生自身が作成するものです。完成イメージを確認したい場合は、下記の「答え合わせ用サンプルサイト」を参照してください。

---

## 答え合わせ用サンプルサイト（講師・運営向け）

Session1〜3の完成形を実際にAWS上に構築した参考実装です。受講生が使うハンズオン用のリソース（`lastname-firstname` 個人名や `aws-learners-s3`）とは完全に分離されています。

| サイト | URL |
|---|---|
| 完成サンプルサイト | https://d69f16572v74l.cloudfront.net/ |

<details>
<summary>作成したAWSリソース一覧（クリックで展開）</summary>

| リソース | 名前 | リージョン |
|---|---|---|
| S3バケット | `aws-handson-sample-site` | ap-northeast-1 |
| CloudFront | `E3PP2GPN6BWSGR`（`d69f16572v74l.cloudfront.net`） | グローバル |
| IAMロール | `handson-sample` | - |
| DynamoDBテーブル | `users` | ap-northeast-1 |
| Lambda（Session2） | `users-post-function-handson-sample` | ap-northeast-1 |
| Lambda（Session3） | `handson-sample-b` | ap-northeast-1 |
| API Gateway（Session2） | `handson-sample-users-registration-api`（ステージ `users-stage`） | ap-northeast-1 |
| API Gateway（Session3） | `handson-sample-b`（ステージ `prod`） | ap-northeast-1 |

後片付けする場合は、上記リソースをすべて削除してください（CloudFrontは無効化後に削除が必要です）。

</details>

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

---

## 付録：GitHubでファイル修正前後を比較する手順

このリポジトリでファイルを修正した場合、GitHubでその変更を視覚的に確認することができます。

### **方法1：単一コミットの詳細を確認**

1. GitHub リポジトリのトップページを開く
2. 「Commits」をクリックしてコミット一覧を表示
3. 確認したいコミットをクリック
4. 赤色（`−`）が削除行、緑色（`+`）が追加行として表示されます

**例：**  
`https://github.com/[ユーザー名]/[リポジトリ名]/commit/[コミットハッシュ]`

### **方法2：2つのコミット間で比較**

1. 以下の形式でURLを構築します：
   ```
   https://github.com/[ユーザー名]/[リポジトリ名]/compare/[修正前のコミットハッシュ]...[修正後のコミットハッシュ]
   ```

2. ページ上部の「Unified」または「Split」ボタンで表示形式を切り替え：
   - **Unified view** = 1列表示（赤/緑で色分け）
   - **Split view** = 左右2列表示（修正前と修正後を並べて表示）

3. ファイル左の三角形アイコンをクリックすると、詳細を展開/折りたたみできます

### **方法3：ブランチやPull Requestで比較**

1. 「Pull requests」タブをクリック
2. 該当するPRを選択
3. **「Files changed」タブをクリック**
4. 修正内容が赤/緑で表示されます

### **表示のコツ**

- ファイル内で大量の変更がある場合、**「Hide whitespace」チェックボックス**を有効にすると、スペースやインデントの変更を非表示にできます
- 特定のファイルだけを確認したい場合は、ファイル名の検索ボックスで絞り込めます
- コメントを追加したい場合、差分行の左側の「+」ボタンをクリック
