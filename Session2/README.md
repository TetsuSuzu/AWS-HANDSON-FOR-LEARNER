# Session2 — 会員登録 API を呼び出す

## このセッションで学ぶこと

事務局が用意した **会員登録 API** を、ローカルのサイトから呼び出して、
フォームに入力したデータを登録できるようにします。

```
ブラウザ（web/index.html）
  │  登録ボタン → API リクエスト（fetch / ajax）
  ▼
┌──────────── 事務局が用意済み ────────────┐
│  API Gateway → Lambda → DynamoDB        │
│  （会員情報を受け取り、DBに保存する）         │
└──────────────────────────────┘
```

> ⚠️ API Gateway・Lambda・DynamoDB は **事務局が構築済み** です。
> みなさんは「配布されたエンドポイント URL を設定して、呼び出す」ことだけを行います。
> （裏側の作り方を知りたい人は [staff/README.md](../staff/README.md) を参照）

---

## Step 1 — 配布されたエンドポイントを確認する

事務局から、次のような **会員登録 API のエンドポイント URL** が配布されます。

```
例: https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/users-stage/
```

> URL の末尾に `/` が付いていることを確認してください。

---

## Step 2 — index.html にエンドポイントを設定する

`web/index.html` をエディタで開き、ファイル上部の **設定ブロック** を探します。

```javascript
// =====================================================================
//  ★ ここを書き換えます（事務局から配布されるエンドポイント）★
// =====================================================================
var registrationUrl = "";   // ← Session2: 会員登録APIのエンドポイント
var bedrockUrl      = "";   // ← Session3: AIおすすめAPIのエンドポイント
// =====================================================================
```

`registrationUrl` の `""` の中に、Step 1 の URL を貼り付けます。

```javascript
var registrationUrl = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/users-stage/";
```

保存します。

---

## Step 3 — 動作確認

1. ローカルサーバーを起動（Session1 と同じ）
   ```powershell
   cd web
   py -m http.server 8000
   ```
2. ブラウザで `http://localhost:8000` を開く
3. **「新規会員募集」** セクションのフォームに入力する：

   | 項目 | 入力例 |
   |---|---|
   | ユーザID | `test001` |
   | 名前 | `テスト 太郎` |
   | メールアドレス | `test@example.com` |
   | 年齢 | `25` |
   | 住所 | `東京都渋谷区` |
   | 電話番号 | `090-0000-0000` |

4. **「登録」** ボタンをクリック
5. **「登録が完了しました」** と表示されれば成功！

> 登録済みデータの確認（DynamoDB の中身）は事務局が行います。

---

## 仕組みの解説（読み物）

`web/index.html` の中で、登録ボタンが押されたときの処理はこうなっています。

```javascript
$.ajax({
    type: 'POST',                       // POST で送信
    url: registrationUrl,               // 配布された API のURL
    contentType: 'application/json',
    data: JSON.stringify(requestBody)   // フォームの入力を JSON にして送る
});
```

- フォームの入力値を **JSON** にまとめて、API に **POST** リクエストで送ります。
- API（事務局の Lambda）がそれを受け取り、データベース（DynamoDB）に保存します。
- 保存が終わると `{"message": "登録が完了しました"}` が返ってきて、画面に表示されます。

---

## よくあるトラブル

| 症状 | 対処 |
|---|---|
| 「未設定です」と出る | `registrationUrl` に URL を貼り、保存したか確認 |
| 「登録に失敗しました」 | URL が正しいか・末尾に `/` があるか確認。事務局に API が稼働中か確認 |
| ボタンを押しても無反応 | ブラウザの開発者ツール（F12）→「Console」でエラーを確認 |
| CORS エラーが出る | `http://localhost:8000` のように **ローカルサーバー**で開いているか確認（ファイルを直接ダブルクリックしていないか） |

---

➡️ 次は **[Session3](../Session3/README.md)**：AI おすすめ機能を呼び出します。
