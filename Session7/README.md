# Session7 — 管理者用 会員情報管理画面

Session2・Session3 で作った会員 API（HTTP API）を使って、管理者用の画面（`admin.html`）から会員の **一覧・照会・更新・削除** をします。

> **新しい API や Lambda は作りません。** Session3 の `users-api-<名前>` と `users-function-<名前>` をそのまま使います。マッピングテンプレートは使いません。

## このハンズオンで作るもの

```text
ブラウザ（admin.html）
   │
   │ GET / PUT / DELETE（JSON）
   ▼
API Gateway HTTP API（users-api-<名前>）  ← Session3 で作成済み
   │
   │ ルートごとに Lambda を呼び出す
   ▼
Lambda（users-function-<名前>）           ← Session2 で作成済み
   │
   ▼
DynamoDB（users-table-<名前>）            ← Session2 で作成済み
```

## 使うルート

Session3 で作成済みの 5 つのうち、次の 4 つを使います。

| メソッド | パス | 画面での操作 |
|---|---|---|
| GET | `/v1/users?limit=100` | 一覧を表示 |
| GET | `/v1/users/{id}` | 照会 |
| PUT | `/v1/users/{id}` | 更新 |
| DELETE | `/v1/users/{id}` | 削除 |

> 仕様は Android アプリ側の `docs/api-spec.md` と同じ形です。Android アプリも同じ API を呼び出すため、データの形（`age` は数値、エラーは `message` を含む JSON）は変えていません。

## 使用するファイル

| ファイル名 | 用途 |
|---|---|
| `admin.html` | 管理者用の会員情報管理ページ（jQuery で API を呼び出す） |

---

## 手順の流れ

1. Session3 の API URL を確認する
2. `admin.html` の API URL を書き換えて S3 にアップロードする
3. 動作確認

---

## Step 1：API URL を確認する

1. AWS マネジメントコンソールで **API Gateway** を開く
2. `users-api-<名前>` を選び、概要に表示される **URL** を控える（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com`）
3. 末尾に `/` は付けない

---

## Step 2：admin.html の API URL を書き換えて S3 にアップロードする

### 2-1. API URL を設定する

`admin.html` をテキストエディタで開き、次の行を探します。

```javascript
var apiUrl = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com";
```

Step 1 で控えた URL に書き換えます。パスは `apiUrl` の後ろに自動で付くため、ここには `/v1/users` を入れないでください。

### 2-2. S3 にアップロードする

Session1 で作成した S3 バケット（<font color="red">lastname-firstname</font>）に、`admin.html` をアップロードします（新しいバケットは不要です）。

1. Session1 の S3 バケットを開く
2. **「アップロード」** をクリック → 書き換えた `admin.html` を選択 → **「アップロード」**

> 同じバケットに置くため、Session3 で設定した CORS の許可オリジンに、そのまま含まれます。CORS の設定を追加する必要はありません。

---

## Step 3：動作確認

### 3-1. 管理画面を開く

```text
https://xxxxxxxxxxxx.cloudfront.net/admin.html
```

S3 ウェブサイトエンドポイントを使っている場合は、そのドメインの `/admin.html` を開きます。

### 3-2. 各機能を確認する

| 確認項目 | 操作 | 期待する動作 |
|---|---|---|
| 一覧表示 | 「一覧を表示」を押す | Session2 で登録した会員が一覧に表示される |
| 照会 | ユーザIDを入力して「照会」を押す | 該当会員の情報がフォームに表示される |
| 更新 | フォームの内容を変えて「更新」を押す | 「更新が完了しました」と表示され、一覧の値が変わる |
| 削除 | ユーザIDを入力して「削除」を押す | 「削除が完了しました」と表示され、一覧から消える |

---

## よくあるトラブルと対処法

### 一覧・照会・更新・削除が失敗する

- `admin.html` の `apiUrl` が `users-api-<名前>` の URL になっているか確認する（末尾に `/` や `/v1/users` を付けない）
- ブラウザの開発者ツール（F12）の **コンソール** と **ネットワーク** タブで、どのリクエストが何のステータスで失敗したか確認する

### 更新が 400 エラーになる

- 画面に出るメッセージ（例: 「年齢は0以上の整数で指定してください」）の項目を直す
- 電話番号は数字のみ、メールアドレスは `@` を含む形式で入力する

### 照会しても情報が出てこない

- 入力したユーザIDが Session2 で登録したものと一致しているか確認する（大文字・小文字も区別されます）

