# Session9 — GitHub Actions と AWS を OIDC でつなぐ（任意）

GitHub Actions から AWS を操作するときに、**アクセスキーを使わず** に、OIDC（OpenID Connect）で一時的な権限を受け取る設定をします。

> **このセッションの位置づけ**
> このハンズオンの Session1〜8 では、GitHub と AWS はつなぎません（Amplify も Git なしで公開します）。このセッションは、将来、GitHub から AWS へ自動でデプロイしたくなったときのための **参考手順** です。本編を進めるために必要ではありません。

## このセッションで分かること

- OIDC とは何か、なぜアクセスキーより安全なのか
- AWS 側で必要な設定（IAM の ID プロバイダーと IAM ロール）
- GitHub Actions のワークフローから、そのロールを使って AWS を操作する書き方

## 事前準備

- GitHub のアカウントと、練習用のリポジトリ（公開でも非公開でも可）
- AWS アカウントで IAM を作成できる権限
- 次の値を控えておく（以降の手順で `<...>` の部分に入れます）

| 値 | 例 |
|---|---|
| GitHub のユーザー名または組織名（`<GitHubの所有者>`） | `TetsuSuzu` |
| GitHub のリポジトリ名（`<リポジトリ名>`） | `AWS-HANDSON-FOR-LEARNER` |
| AWS アカウント ID（`<アカウントID>`） | 12 桁の数字 |

## 用語の説明

> **OIDC とは？**
> 「この要求は、確かに GitHub のこのリポジトリから来た」ということを、署名付きの **トークン**（証明書のようなもの）で伝える仕組みです。AWS はそのトークンを確認して、一時的な権限を渡します。
>
> **なぜアクセスキーを使わないのか？**
> アクセスキーを GitHub に保存すると、漏れたときに誰でも AWS を操作できます。期限もありません。OIDC は、ワークフローが動いている間だけ有効な一時的な権限を使うので、漏れるものがなく、キーを定期的に交換する手間もありません。
>
> **IAM の ID プロバイダーとは？**
> 「GitHub が出すトークンを信頼する」と、AWS に登録する設定です。
>
> **IAM ロールとは？**
> 一時的に引き受ける権限のセットです。「どのリポジトリのどのブランチなら、このロールを使ってよい」という条件（信頼ポリシー）を付けます。

```
【全体の流れ】

GitHub Actions（ワークフロー）
  │ 1. GitHub に OIDC トークンを発行してもらう
  ▼
AWS STS
  │ 2. トークンを確認し、条件（リポジトリ・ブランチ）が合えば
  │    一時的な認証情報（約 1 時間で失効）を発行する
  ▼
ワークフロー
  │ 3. 一時的な認証情報で AWS を操作する
  ▼
AWS のサービス（S3、Amplify など）
```

## 手順の流れ

1. IAM に GitHub の ID プロバイダーを登録する
2. IAM ロールを作成する（信頼ポリシーと権限）
3. GitHub Actions のワークフローを書く
4. 動作を確かめる
5. 片付け

---

## Step 1：IAM に GitHub の ID プロバイダーを登録する

1. 検索欄に **IAM** と入力して開く
2. 左のメニューで **ID プロバイダ** → **プロバイダを追加** をクリック
3. 次のとおり入力する

   | 項目 | 値 |
   |---|---|
   | プロバイダのタイプ | **OpenID Connect** |
   | プロバイダの URL | `https://token.actions.githubusercontent.com` |
   | 対象者（Audience） | `sts.amazonaws.com` |

4. **プロバイダを追加** をクリック

> AWS アカウントごとに、この登録は 1 回だけです。すでに登録されている場合は、この Step は飛ばしてください。

---

## Step 2：IAM ロールを作成する

### 2-1. ロールの作成を始める

1. IAM の左のメニューで **ロール** → **ロールを作成** をクリック
2. 信頼されたエンティティタイプは **カスタム信頼ポリシー** を選ぶ

### 2-2. 信頼ポリシーを貼り付ける

次の JSON を貼り付けます。`<アカウントID>`、`<GitHubの所有者>`、`<リポジトリ名>` は自分の値に置き換えます。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<アカウントID>:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:<GitHubの所有者>/<リポジトリ名>:ref:refs/heads/main"
                }
            }
        }
    ]
}
```

この条件は、次の意味です。

| 条件 | 意味 |
|---|---|
| `aud` が `sts.amazonaws.com` | AWS 向けに発行されたトークンだけを受け付ける |
| `sub` が `repo:<所有者>/<リポジトリ名>:ref:refs/heads/main` | **そのリポジトリの `main` ブランチ** から動いたワークフローだけを受け付ける |

> **重要**: `sub` の条件は必ず付けてください。条件がないと、GitHub 上の **ほかの誰のリポジトリ** からでも、このロールを使えてしまいます。`repo:*` のようなワイルドカードで広げすぎないでください。
>
> ブランチを増やしたいときは、`StringLike` の値を配列にして、`refs/heads/dev` などを追加します。

### 2-3. 権限を付ける

1. 付ける権限は、ワークフローが行う操作に必要な **最小限** にする
2. この練習では、まず AWS に入れたことだけを確かめるので、権限は付けなくても構いません（`aws sts get-caller-identity` は権限なしで実行できます）
3. 実際にデプロイする場合は、たとえば S3 への書き込みだけを許可するポリシーを作って付ける

> **注意**: `AdministratorAccess` は付けないでください。ワークフローの中身が書き換えられたときに、AWS アカウント全体が操作されてしまいます。

### 2-4. ロール名を付けて作成する

1. ロール名: `github-actions-role-<名前>`（例：`github-actions-role-yamada-taro`）
2. **ロールを作成** をクリック
3. 作成したロールを開き、**ARN** を控える

```
例: arn:aws:iam::123456789012:role/github-actions-role-yamada-taro
```

---

## Step 3：GitHub Actions のワークフローを書く

練習用のリポジトリに、`.github/workflows/aws-oidc-test.yml` を作ります。

```yaml
name: aws-oidc-test

on:
  workflow_dispatch:   # 手動で実行する
  push:
    branches: [main]

permissions:
  id-token: write      # OIDC トークンを発行するために必要
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: AWS の認証情報を取得する
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<アカウントID>:role/github-actions-role-<名前>
          aws-region: ap-northeast-1

      - name: 自分が誰として AWS に入ったかを表示する
        run: aws sts get-caller-identity
```

ポイントは次のとおりです。

| 項目 | 意味 |
|---|---|
| `permissions: id-token: write` | **これがないと OIDC トークンが発行されず、認証に失敗します** |
| `role-to-assume` | Step 2 で控えたロールの ARN |
| `aws-region` | 操作する AWS のリージョン（東京は `ap-northeast-1`） |

> ロールの ARN は秘密の値ではありませんが、アクセスキーのように GitHub の Secrets に入れる必要もありません。ワークフローのファイルに直接書いて構いません。

---

## Step 4：動作を確かめる

1. 上のファイルを `main` ブランチに push する（または GitHub の **Actions** タブから `aws-oidc-test` を **Run workflow** で実行する）
2. **Actions** タブで、ワークフローの実行を開く
3. `aws sts get-caller-identity` の出力に、次のような内容が表示されれば成功です

```json
{
    "UserId": "AROAxxxxxxxxxxxxxxxxx:GitHubActions",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/github-actions-role-yamada-taro/GitHubActions"
}
```

`assumed-role/github-actions-role-...` と出れば、アクセスキーを使わずに、ロールを引き受けて AWS に入れています。

### 確認ポイント

- [ ] IAM に `token.actions.githubusercontent.com` の ID プロバイダーがある
- [ ] ロールの信頼ポリシーに、`aud` と `sub` の両方の条件がある
- [ ] ワークフローに `permissions: id-token: write` がある
- [ ] `aws sts get-caller-identity` に `assumed-role/...` が表示された

---

## よくあるトラブルと対処法

| 症状 | 確認すること |
|---|---|
| `Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity` | 信頼ポリシーの `sub` の値が、実際の `repo:<所有者>/<リポジトリ名>:ref:refs/heads/<ブランチ名>` と一致しているか確認する。大文字と小文字、ブランチ名に注意する |
| `Credentials could not be loaded` / トークンが取得できない | ワークフローに `permissions: id-token: write` があるか確認する |
| `No OpenID Connect provider found` | Step 1 の ID プロバイダーを、同じ AWS アカウントに登録したか確認する。信頼ポリシーの `Federated` の ARN も確認する |
| 別のブランチや、プルリクエストから動かない | `sub` が `main` ブランチ限定になっている。プルリクエストは `repo:<所有者>/<リポジトリ名>:pull_request` になる。必要な分だけ `sub` に追加する |
| 権限がなくて操作が失敗する（`AccessDenied`） | ロールに付けた権限ポリシーを確認する |

---

## 片付け

使い終わったら、不要な権限を残さないために削除します。

1. IAM → ロール → `github-actions-role-<名前>` を削除する
2. 他で使っていなければ、IAM → ID プロバイダ → `token.actions.githubusercontent.com` を削除する
3. 練習用リポジトリの `.github/workflows/aws-oidc-test.yml` を削除する

> ID プロバイダーは、ほかのプロジェクトで使っている可能性があります。使っていないことを確かめてから削除してください。
