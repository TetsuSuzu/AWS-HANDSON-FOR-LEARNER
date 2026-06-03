# Session4 — 自動デプロイ（GitHub Actions）

## このセッションで学ぶこと

**GitHub Actions** を使って、GitHubにコードをpushすると **自動でS3にデプロイ** される仕組みを構築します。

```
【全体の流れ】

開発者が index.html を編集
  │
  │ git push
  ▼
GitHub リポジトリ
  │
  │ GitHub Actions が自動起動
  ▼
┌─────────────────────┐
│   GitHub Actions    │  ← 自動でジョブを実行
│  (ubuntu-latest)    │
└─────────────────────┘
  │
  │ aws s3 sync コマンド
  ▼
┌─────────────────────┐
│    Amazon S3        │  ← Session1 で作ったバケット
│  (静的サイト)        │
└─────────────────────┘
  │
  ▼
CloudFront 経由でサイト公開
```

---

## GitHub Actions とは

GitHub に組み込まれた **CI/CD（自動化）ツール** です。

| 用語 | 意味 |
|---|---|
| **Workflow（ワークフロー）** | 自動化の手順書。YAMLファイルで書く |
| **Trigger（トリガー）** | ワークフローが起動するきっかけ（例: pushしたとき） |
| **Job（ジョブ）** | ワークフロー内の処理のまとまり |
| **Step（ステップ）** | ジョブ内の個々の処理 |
| **Runner（ランナー）** | ジョブを実行するサーバー（GitHubが用意） |

---

## 事前準備：AWSの認証情報をGitHubに登録する

GitHub Actions から S3 にアクセスするために、AWSの認証情報を **GitHub Secrets** に登録します。

### 1. AWSアクセスキーを発行する

1. AWS マネジメントコンソール → **IAM** を開く
2. 左メニュー **「ユーザー」** → 自分のユーザー名をクリック
3. **「セキュリティ認証情報」** タブ → **「アクセスキーを作成」** をクリック
4. ユースケース：**「その他」** を選択 → 「次へ」
5. **「アクセスキーを作成」** をクリック
6. `アクセスキーID` と `シークレットアクセスキー` をメモ（この画面を閉じると二度と見られません）

### 2. GitHub Secrets に登録する

1. このリポジトリの **「Settings」** タブを開く
2. 左メニュー **「Secrets and variables」** → **「Actions」** をクリック
3. **「New repository secret」** ボタンをクリック

以下の2つを登録します：

| Name（名前） | Secret（値） |
|---|---|
| `AWS_ACCESS_KEY_ID` | 発行したアクセスキーID |
| `AWS_SECRET_ACCESS_KEY` | 発行したシークレットアクセスキー |

---

## ワークフローファイルの確認

`.github/workflows/deploy-to-s3.yml` が自動デプロイの設定ファイルです。

```yaml
name: S3へ自動デプロイ

on:
  push:
    branches:
      - master          # masterブランチにpushされたときに起動
    paths:
      - 'Session1/**'   # Session1フォルダの変更があったときのみ

jobs:
  deploy:
    runs-on: ubuntu-latest   # GitHubが用意するUbuntuサーバーで実行

    steps:
      # 1. リポジトリのファイルをランナーに取得
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      # 2. AWS認証情報を設定
      - name: AWS認証情報を設定
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      # 3. S3にアップロード
      - name: S3にデプロイ
        run: |
          aws s3 sync Session1/ s3://aws-learners-s3 \
            --delete \
            --exclude "*.md"
```

### `YOUR-BUCKET-NAME` の書き換え

バケット名は `aws-learners-s3` に設定済みです。

---

## 動作確認

### 1. ファイルを変更してpushする

`Session1/index.html` を少し編集して、GitHubにpushします。

```bash
git add Session1/index.html
git commit -m "テスト: GitHub Actionsの動作確認"
git push origin master
```

### 2. GitHub Actions の実行を確認する

1. リポジトリの **「Actions」** タブをクリック
2. 実行中または完了したワークフロー **「S3へ自動デプロイ」** をクリック
3. 各ステップが ✅ になれば成功

### 3. S3・サイトを確認する

CloudFront の URL にアクセスして、変更が反映されていることを確認します。

---

## よくあるエラーと対処法

| エラー | 原因 | 対処法 |
|---|---|---|
| `Unable to locate credentials` | Secretsの登録名が間違っている | `AWS_ACCESS_KEY_ID` のスペルを確認 |
| `Access Denied` | IAMユーザーにS3の権限がない | IAMユーザーに `AmazonS3FullAccess` を追加 |
| `NoSuchBucket` | バケット名が間違っている | `YOUR-BUCKET-NAME` を正しいバケット名に修正 |
| ワークフローが起動しない | トリガーのブランチ名が違う | `branches: master` が合っているか確認 |
