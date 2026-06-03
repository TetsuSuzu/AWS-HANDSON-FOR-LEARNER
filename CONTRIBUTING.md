# GitHub 運営ガイド

このファイルは **リポジトリ管理者・運営者向け** のGitHub操作手順書です。  
受講者向けのAWSハンズオン手順は [README.md](README.md) を参照してください。

---

## 目次

1. [Issues（課題管理）](#1-issues課題管理)
2. [Projects（進捗管理ボード）](#2-projects進捗管理ボード)
3. [Gists（コード共有）](#3-gistsコード共有)
4. [Pull Request（変更の取り込み）](#4-pull-request変更の取り込み)
5. [CODEOWNERS（責任者設定）](#5-codeowners責任者設定)

---

## 1. Issues（課題管理）

Issues はリポジトリに関する **タスク・バグ・改善要望** を記録・管理する機能です。

### ラベルの種類

| ラベル | 色 | 用途 |
|---|---|---|
| `session1` | 青 | Session1（S3）に関するタスク |
| `session2` | 黄 | Session2（Lambda + DynamoDB）に関するタスク |
| `session3` | 赤 | Session3（API Gateway + Bedrock）に関するタスク |
| `docs` | 紺 | 手順書・ドキュメントの改善 |

### 登録済みのIssue一覧

| # | タイトル | ラベル |
|---|---|---|
| #1 | Session1: S3静的サイトホスティングの手順確認 | session1 |
| #2 | Session2: IAM + Lambda + DynamoDB の手順確認 | session2 |
| #3 | Session3: API Gateway + Bedrock 連携の手順確認 | session3 |
| #4 | Session2/README.md を作成する | docs |
| #5 | Session3/README.md の内容を充実させる | docs |
| #6 | 受講者向けトラブルシューティングガイドを追加する | docs |

### CLIでIssueを作成する方法

```bash
gh issue create \
  --repo TetsuSuzu/AWS-HANDSON-FOR-LEARNER \
  --title "タイトル" \
  --label "session1" \
  --body "内容"
```

### Issueを確認する

```
https://github.com/TetsuSuzu/AWS-HANDSON-FOR-LEARNER/issues
```

---

## 2. Projects（進捗管理ボード）

Projects は Issues を **ボード形式** で管理し、進捗を可視化する機能です。

### 設定済みのプロジェクト

| プロジェクト名 | URL |
|---|---|
| AWSハンズオン 学習進捗管理 | https://github.com/users/TetsuSuzu/projects/4 |

### ステータスの使い方

| ステータス | 意味 |
|---|---|
| 📋 Todo | 未着手 |
| 🔄 In Progress | 対応中 |
| ✅ Done | 完了 |

Issueの対応を始めたら **「In Progress」** に、完了したら **「Done」** に移動させてください。

### CLIでIssueをProjectsに追加する方法

```bash
gh project item-add 4 \
  --owner TetsuSuzu \
  --url https://github.com/TetsuSuzu/AWS-HANDSON-FOR-LEARNER/issues/番号
```

---

## 3. Gists（コード共有）

Gists はコードの断片を **URLで簡単に共有** できる機能です。  
受講者にコードを配布する際に使用します。

### 公開中のGist一覧

| Session | 内容 | URL |
|---|---|---|
| Session1 | S3バケットポリシー | https://gist.github.com/TetsuSuzu/52ac3992fedf13078686a3a1001c8540 |
| Session2 | Lambda関数（DynamoDB登録） | https://gist.github.com/TetsuSuzu/bc7e8259462a96c11dc58b75f61a58d3 |
| Session2 | Lambdaテストイベント | https://gist.github.com/TetsuSuzu/1ff21322a9206bd40d6430cd0b7c9f28 |
| Session3 | Lambda関数（Bedrock AI連携） | https://gist.github.com/TetsuSuzu/cac498a24fc62682afc73427c3e7412e |

### 一覧ページ

```
https://gist.github.com/TetsuSuzu
```

### CLIでGistを作成する方法

```bash
gh gist create ファイル名 --public --desc "説明文"
```

---

## 4. Pull Request（変更の取り込み）

Pull Request（PR）はファイルの変更を **レビューしてからmasterに取り込む** 仕組みです。

### 基本的な流れ

```
1. ブランチ作成
   git checkout -b feature/作業名

2. ファイルを変更・追加

3. コミット
   git add ファイル名
   git commit -m "変更内容の説明"

4. GitHubにプッシュ
   git push -u origin feature/作業名

5. PRを作成
   gh pr create --title "タイトル" --body "説明" --base master

6. Files changed タブで差分を確認
   緑（+）= 追加された行
   赤（-）= 削除された行

7. Merge pull request でmasterに取り込む
```

### PRの確認

| 状態 | URL |
|---|---|
| 未完了のPR | https://github.com/TetsuSuzu/AWS-HANDSON-FOR-LEARNER/pulls?q=is:pr+is:open |
| マージ済みのPR | https://github.com/TetsuSuzu/AWS-HANDSON-FOR-LEARNER/pulls?q=is:pr+is:merged |

### マージ済みPR一覧

| # | タイトル | 内容 |
|---|---|---|
| #7 | README にGistコード一覧を追加 | README.mdにGistリンクを追記 |
| #8 | CODEOWNERSファイルとgitignore更新 | .github/CODEOWNERS を新規作成 |

---

## 5. CODEOWNERS（責任者設定）

CODEOWNERS は **ファイルごとの責任者** を定義するファイルです。  
PRで変更があった際に、自動でレビュアーとして追加されます。

### ファイルの場所

```
.github/CODEOWNERS
```

### 現在の設定

```
# リポジトリ全体のデフォルト責任者
*          @TetsuSuzu

# Session別の責任者
Session1/  @TetsuSuzu
Session2/  @TetsuSuzu
Session3/  @TetsuSuzu

# ドキュメント
*.md       @TetsuSuzu
```

### 書き方のルール

```
<ファイルパターン>  <GitHubユーザー名>

# 例：Session1フォルダは @user1 と @user2 が担当
Session1/  @user1 @user2

# 例：Pythonファイルはすべて @user3 が担当
*.py  @user3
```

### 注意点

- PR作成者が自分自身の場合、自分はレビュアーに追加されません
- レビュー承認を **必須** にするにはブランチ保護ルールと組み合わせます
  - Settings → Branches → Branch protection rules → **Require review from Code Owners**

---

## CLIのアカウント切り替え

このリポジトリは `TetsuSuzu` アカウントで管理しています。  
`SuzukiTetsuyainFuttsu` でログイン中の場合は切り替えてください。

```bash
# 現在のログイン状態を確認
gh auth status

# TetsuSuzuに切り替え
gh auth switch --user TetsuSuzu
```
