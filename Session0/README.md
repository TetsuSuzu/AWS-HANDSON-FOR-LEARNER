# Session0 — 環境セットアップ

**Session1 に進む前に、この手順を完了してください。**
ここでは「自分のリポジトリを用意 → PC に取り込む → ローカルでサイトを開く」までを行います。

```
事務局リポジトリ ──Fork──▶ 自分のGitHubリポジトリ ──clone/DL──▶ 自分のPC ──ローカルサーバー──▶ ブラウザ
```

---

## Step 1 — GitHub アカウントを用意する

すでにアカウントがある人はスキップしてください。

1. https://github.com/signup を開く
2. メールアドレス・パスワード・ユーザー名を入力して登録
3. メールに届く確認コードを入力して完了

> ユーザー名は後で公開URL（`https://<ユーザー名>.github.io/...`）に使われます。

---

## Step 2 — リポジトリを Fork する

「Fork」は、事務局のリポジトリを **自分のアカウントにコピー** する操作です。
以降、みなさんは自分のコピーを自由に編集します。

1. 事務局から案内されたリポジトリのページを開く
   （例：`https://github.com/<事務局>/AWS-HANDSON-FOR-LEARNER`）
2. 右上の **「Fork」** ボタンをクリック
3. 「Create fork」をクリック
4. `https://github.com/<自分のユーザー名>/AWS-HANDSON-FOR-LEARNER` ができれば成功

> これ以降の作業は、**必ず自分の Fork したリポジトリ** で行ってください。

---

## Step 3 — PC に取り込む

### 方法A：ZIP でダウンロード（Git をまだ知らない人向け）

1. 自分の Fork したリポジトリで、緑色の **「Code」** ボタンをクリック
2. **「Download ZIP」** をクリック
3. ダウンロードした ZIP を **デスクトップ** などに展開する

> ⚠️ ZIP 方式だと、編集内容を GitHub に戻す（push する）には Step 4 の Git が必要です。
> Session4 の自動公開まで進む人は **方法B（clone）** を推奨します。

### 方法B：git clone（推奨）

1. [Git](https://git-scm.com/downloads) をインストール
2. ターミナル（Windows は PowerShell）で以下を実行：

```bash
git clone https://github.com/<自分のユーザー名>/AWS-HANDSON-FOR-LEARNER.git
cd AWS-HANDSON-FOR-LEARNER
```

> `<自分のユーザー名>` は自分の GitHub ユーザー名に置き換えてください。

---

## Step 4 — ローカルサーバーでサイトを開く

Web サイトは、ファイルをダブルクリックするだけでも開けますが、
API 連携（Session2/3）を正しく動かすため、**ローカルサーバー**で開きます。

### Python を使う場合（推奨）

取り込んだフォルダの中で、以下を実行します。

**Windows（PowerShell）:**
```powershell
cd web
py -m http.server 8000
```

**Mac / Linux:**
```bash
cd web
python3 -m http.server 8000
```

実行したまま、ブラウザで次のURLを開きます：

```
http://localhost:8000
```

> 8000 番が使われている場合は `8080` など別の番号でも構いません（例：`py -m http.server 8080` → `http://localhost:8080`）。
> サーバーを止めるときは、ターミナルで `Ctrl + C` を押します。

### Python が入っていない場合（VS Code の Live Server）

1. [VS Code](https://code.visualstudio.com/) をインストール
2. 拡張機能 **「Live Server」** をインストール
3. `web/index.html` を開き、右下の **「Go Live」** をクリック
4. ブラウザが自動で開きます（例：`http://127.0.0.1:5500/web/index.html`）

---

## Step 5 — 表示を確認する

ブラウザに「Web販 AWS勉強会サイト」のトップページが表示されれば、セットアップ完了です 🎉

| 確認項目 | 期待する状態 |
|---|---|
| ページが表示される | ヘッダー・写真・フォームが見える |
| 写真が表示される | かぐらスキー場／富津海岸の写真が出る |

> この時点では「会員登録」「AIおすすめ」ボタンはまだ動きません（Session2/3 で API を設定します）。

---

## 配布物の確認

事務局から、以下が配布されているか確認してください（Session2/3 で使います）。

| 配布物 | 用途 |
|---|---|
| 会員登録 API のエンドポイント URL | Session2 |
| AIおすすめ API のエンドポイント URL | Session3 |

---

➡️ 準備ができたら **[Session1](../Session1/README.md)** へ。
