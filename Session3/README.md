# Session3 — AI おすすめ機能を呼び出す

## このセッションで学ぶこと

事務局が用意した **生成AI（Amazon Bedrock）連携 API** を呼び出し、
入力した好みに合わせて AI が旅先のおすすめ料理を提案する機能を動かします。

```
ブラウザ（web/index.html）
  │  テキスト入力 → API リクエスト
  ▼
┌──────────── 事務局が用意済み ────────────┐
│  API Gateway → Lambda → 生成AI（Bedrock）  │
│  （質問を受け取り、AIの回答を返す）            │
└──────────────────────────────┘
```

> ⚠️ API Gateway・Lambda・生成AI は **事務局が構築済み** です。
> みなさんは「配布されたエンドポイント URL を設定して、呼び出す」ことだけを行います。
> （裏側の作り方を知りたい人は [staff/README.md](../staff/README.md) を参照）

---

## Step 1 — 配布されたエンドポイントを確認する

事務局から、次のような **AIおすすめ API のエンドポイント URL** が配布されます。

```
例: https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/recommend
```

---

## Step 2 — index.html にエンドポイントを設定する

`web/index.html` の上部の設定ブロックで、今度は `bedrockUrl` に貼り付けます。

```javascript
var registrationUrl = "https://.../users-stage/";          // Session2 で設定済み
var bedrockUrl      = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/recommend";
```

保存します。

---

## Step 3 — 動作確認

1. ローカルサーバーを起動して `http://localhost:8000` を開く
2. **「あなたの好きな食事は？」** セクションのテキスト欄に入力する
   - 例：`長野でおすすめの食事を教えて`
3. **「おすすめを表示」** ボタンをクリック
4. AI からの回答が表示されれば成功！🎉

> 回答が返るまで数秒〜十数秒かかることがあります。「問い合わせしています...」の表示のまま少し待ってください。

---

## 仕組みの解説（読み物）

`web/index.html` の中の処理は次のようになっています。

```javascript
$.ajax({
    type: 'post',
    url: bedrockUrl,                              // 配布された AI API のURL
    contentType: 'application/json',
    data: JSON.stringify({ "key1": $("#text").val() }),  // 入力テキストを key1 で送る
    success: function(data) {
        $("#response").html(marked.parse(JSON.parse(data)));  // 回答をMarkdownとして表示
    }
});
```

- 入力テキストを `{"key1": "..."}` という形で API に送ります。
- API（事務局の Lambda）が生成AIに問い合わせ、回答テキストを返します。
- 返ってきた回答を、`marked` ライブラリで **Markdown → HTML** に変換して表示します。

---

## よくあるトラブル

| 症状 | 対処 |
|---|---|
| 「未設定です」と出る | `bedrockUrl` に URL を貼り、保存したか確認 |
| `error` と出る | URL が正しいか確認。事務局に API が稼働中か確認 |
| 反応が返ってこない | 生成AIの応答に時間がかかることがある。数十秒待っても返らなければ再試行 |
| CORS エラー | `http://localhost:8000` などローカルサーバーで開いているか確認 |

---

➡️ 次は **[Session4](../Session4/README.md)**：作ったサイトを GitHub Pages で世界に公開します。
