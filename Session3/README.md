# Session3 — HTTP API を作り、静的サイトから呼び出す

Lambda を、インターネットから呼べる URL（API）に公開します。

開始前に [Session2](../Session2/README.md) の DynamoDB と Lambda を作成・テストしてください。

> **API Gateway（HTTP API）とは？**
> 外からの要求（HTTP リクエスト）を受け付けて、対応する Lambda に渡す入口です。このハンズオンでは、API の URL そのものが「会員登録」の入口になります。URL の後ろにパスは付けません。

## 3-1. API Gateway の画面を開く

1. 検索欄に **API Gateway** と入力して開く
2. リージョンが **ap-northeast-1** であることを確認する

## 3-2. HTTP API を作成する

1. **API を作成** をクリック
2. **HTTP API** の **構築** をクリック（REST API ではなく HTTP API を選ぶ）
3. **統合** で **Lambda** を選び、次のとおり入力する

| 項目 | 入力する値 |
|---|---|
| Lambda 関数 | `users-function-<名前>`（リージョン ap-northeast-1） |
| API 名 | `users-api-<名前>` |

4. **次へ**

## 3-3. ルート（経路）を設定する

**ルート** は、「どのメソッドと URL の組み合わせを、どの Lambda に渡すか」の一覧です。このセッションでは、会員を登録する次の 1 つだけを作ります。

| メソッド | パス | 役割 |
|---|---|---|
| POST | `/`（パスなし） | 会員を登録する |

### 作り方

1. ルートの画面で **ルートを追加** をクリック
2. メソッドに **POST** を選び、パスは `/`（何も入力しない）のまま、統合先に `users-function-<名前>` を選ぶ
3. **次へ**

> 一覧の取得・照会・更新・削除の API は、このセッションでは作りません（Session4 で管理者用に作ります）。

## 3-4. ステージを設定する

**ステージ** は、API の「公開の段階」です。ここでは、URL にステージ名が付かない `$default` を使います。

1. ステージ名: **`$default`** のまま
2. **自動デプロイ** が有効になっていることを確認する（既定で有効）
3. **次へ** → **作成**

> **ポイント**: 設定を変えたら、自動デプロイが有効なら数秒で外に反映されます。無効なときは、**デプロイ** を押す必要があります。

## 3-5. API の URL を控える

1. 作成した API（`users-api-<名前>`）の画面を開く
2. **API の詳細** 、または概要に表示される **URL**（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com`）を控える
3. 末尾に `/` は付けない

> この URL が、呼び出す側（Web の画面、Android アプリなど）に設定する値です。

### 確認ポイント

- [ ] ルート `POST /`（パスなし）があり、`users-function-<名前>` につながっている
- [ ] ステージが `$default`
- [ ] API の URL を控えた

## 3-6. Session1 のサイトに API URL を設定する

Session1 の静的サイトから API を呼ぶには、API の URL を `Session1/config.js` に設定します。`<API の URL>` は 3-5 で控えた値に置き換え、末尾に `/` は付けません。

```javascript
window.API_ENDPOINT = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com";
```

### Session1 の S3 静的サイトを更新する

1. `Session1/config.js` の `window.API_ENDPOINT` に API の URL を設定する
2. AWS コンソールで Session1 の S3 バケットを開く
3. `index.html`、`app.js`、`config.js`、`styles.css`、`photo1.png`、`photo2.png` をバケット直下へアップロードし、既存ファイルは置き換える（`admin.html` と `admin.js` は別のバケットに置くため、ここでは上げません）
4. Session1 のサイト URL を開いて、会員登録フォームから登録を試す

S3 ウェブサイトエンドポイントは HTTP です。S3 の静的ウェブサイトホスティングはウェブサイトファイルを公開します。機密情報は置かないでください。

### 確認ポイント

- [ ] Session1 のサイトを更新した
- [ ] 公開先の URL を控えた（次の CORS 設定で使用）
- [ ] `Session1/config.js` に API エンドポイントを設定した

## 3-7. CORS を設定する

CORS は、ブラウザーから別のドメインにある API を呼び出すときに必要な許可設定です。Session1 の S3 ウェブサイトエンドポイントの「オリジン」（スキームとホスト名。パスや末尾の `/` は含めない）を許可します。

1. **API Gateway** → `users-api-<名前>` → **CORS** を開く（API の **設定** 内にある場合もあります）
2. 次のとおり設定する

   | 項目 | 設定値 |
   |---|---|
   | 許可されたオリジン（Access-Control-Allow-Origin） | 実際にブラウザーで開くサイトのオリジン。S3 ウェブサイトは `http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com`。複数の URL から使う場合は各オリジンを追加 |
   | 許可されたメソッド（Access-Control-Allow-Methods） | `POST`, `OPTIONS` |
   | 許可されたヘッダー（Access-Control-Allow-Headers） | `content-type` |
   | 認証情報（Access-Control-Allow-Credentials） | 無効 |

3. 保存する。ステージ `$default` の自動デプロイが有効なら、設定は自動で反映される

> **注意**: URL に含まれるスキーム（`http://` または `https://`）とホスト名を正確に登録します。末尾にパス（例: `/index.html`）や `/` を付けません。`*` の許可は使わず、必要なサイトだけを登録します。
>
> HTTP API の CORS を API Gateway 側で設定した場合、API Gateway が CORS 応答ヘッダーを返し、プリフライト（OPTIONS）要求にも応答します。OPTIONS 用の Lambda ルートは追加しません。Lambda の応答側に別の CORS ヘッダーを追加しないでください。

### 確認ポイント

- [ ] 実際のフロントエンド URL のオリジンを許可した
- [ ] `POST`, `OPTIONS` と `content-type` を許可した
- [ ] 認証情報は無効になっている

## 3-8. 動作を確かめる（PowerShell）

ブラウザや PowerShell から、実際に呼んで確かめます。`<API の URL>` は 3-5 で控えた値に置き換えてください。

### 会員を登録する（POST）

```powershell
$api = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com"
$body = '{"id":"u-0001","name":"山田太郎","email":"taro@example.com","age":30,"address":"東京都千代田区1-1","tel":"09012345678"}'
Invoke-RestMethod -Method Post -Uri $api -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

- 結果に `message` と `user` が出れば成功です。

### CORS の設定を確かめる（ブラウザーなし）

CORS を許可するかどうかを決めるのはブラウザーですが、ブラウザーが見るのは API の応答ヘッダーです。`Origin` ヘッダーを付けて `curl.exe` で呼ぶと、同じヘッダーを PowerShell から確かめられます。PowerShell の `curl` は別のコマンドの別名なので、必ず `curl.exe` と書きます。

```powershell
# 3-7 で許可したオリジン(Session1 の S3 ウェブサイト)
$origin = "http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com"

# ① プリフライト: ブラウザーが POST の前に自動で送る OPTIONS を再現する
curl.exe -s -i -X OPTIONS $api -H "Origin: $origin" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"

# ② 許可していないオリジンでも試す(許可ヘッダーが返らないのが正しい)
curl.exe -s -i -X OPTIONS $api -H "Origin: http://example.com" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"
```

①の応答で、次を確かめます。

| 見る場所 | 正しい状態 |
|---|---|
| 1 行目 | `HTTP/1.1 204`（または `200`） |
| `access-control-allow-origin` | `$origin` と同じ値 |
| `access-control-allow-methods` | `POST` を含む |
| `access-control-allow-headers` | `content-type` を含む |

②の応答には `access-control-allow-origin` が出ません。出ていたら、許可するオリジンを広げすぎています。

> `curl.exe` は CORS を強制しません。ヘッダーがなくてもリクエスト自体は成功するので、成功したかどうかではなく、ヘッダーの有無を読んでください。

### 確認ポイント

- [ ] POST で 201 相当の結果（`message` と `user`）が返る
- [ ] プリフライトの応答に、許可したオリジンと `POST`、`content-type` が出る
- [ ] 許可していないオリジンでは `access-control-allow-origin` が出ない

> **うまくいかないとき**
> - 404 Not Found: URL の末尾に `/v1/users` などを付けていないか確認（URL はそのまま使います）
> - 500 エラー: Lambda の CloudWatch Logs を確認（2-7 の権限やテーブル名を見直す）
> - 日本語が文字化けして見える: PowerShell の表示の問題のことが多いです。データの中身は、Lambda の一覧で確かめてください。
>
> `Invoke-RestMethod` はブラウザーの CORS 制約を検査しません。CORS は上の `curl.exe` で応答ヘッダーを確かめ、最後は公開した Web アプリを実際にブラウザーで開いて確認してください。

## 3-9. 片付け（使い終わったら）

Session4 で、この Session の DynamoDB テーブルと Lambda 実行ロールを引き続き使います。**Session4 以降を進める場合は、すべての Session が終わってから** 削除してください。

次の順番で削除してください（依存があるので、この順です）。

1. S3 のバケット内のオブジェクトを空にしてからバケットを削除する
2. API Gateway → `users-api-<名前>` を削除
3. Lambda → `users-function-<名前>` を削除
4. DynamoDB → `users-table-<名前>` テーブルを削除
5. IAM → 実行ロール（`users-function-<名前>-role-xxxx`）を削除（任意）

## 次の段階

Session3 の後は [Session4](../Session4/README.md) で、登録した会員を管理者が一覧・更新・削除できる管理画面を作成してください。
