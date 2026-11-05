# Session3 — HTTP API を作り、静的サイトから呼び出す

Lambda を、インターネットから呼べる URL（API）に公開します。

開始前に [Session2](../Session2/README.md) の DynamoDB と Lambda を作成・テストしてください。

> **API Gateway（HTTP API）とは？**
> 外からの要求（HTTP リクエスト）を受け付けて、対応する Lambda に渡す入口です。このハンズオンでは、ステージ名までの URL（`.../dev`）そのものが「会員登録」の入口になります。その後ろにパスは付けません。

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

### 作り方（API の作成中、3-2 の続き）

3-2 で Lambda を統合に選ぶと、**ルートを設定する画面** で、初期のルートが 1 つ自動で入っています（例: `ANY /users-function-<名前>`）。このままだと、会員登録のルートにならないので、次のとおり書き換えます。

1. 一覧にある初期のルートを、次の値に書き換える

   | 項目 | 入力する値 |
   |---|---|
   | メソッド | **POST**（`ANY` から変更する） |
   | リソースパス | **`/`**（`/users-function-<名前>` を消して、スラッシュ 1 文字だけにする） |
   | 統合ターゲット | `users-function-<名前>` |

2. 初期のルートのほかに行があれば、**削除** して、`POST /` の 1 行だけにする
3. **次へ**

> **ポイント**: パスの `/` は「パスなし」の意味です。`/users` や `/v1/users` のように、パスを足さないでください。パスを足すと、API の URL にもそのパスを付けないと呼べません。この教材の Lambda は `POST /` を会員登録として受け付けます。

### すでに API を作ってしまった場合（ルートを直す）

1. **API Gateway** → `users-api-<名前>` → 左のメニューの **ルート** を開く
2. 一覧に `POST /` がなければ、**作成** をクリックし、メソッド **POST**、パス `/` で作成する
3. 作成した `POST /` を選び、**統合をアタッチ** で `users-function-<名前>` を選んで **アタッチ**
4. 不要なルート（`ANY /users-function-<名前>` など）は、選んで **削除** する

### 確認ポイント

- [ ] ルートの一覧に `POST /` があり、`users-function-<名前>` につながっている
- [ ] 余分なルート（`ANY /...` など）が残っていない

> 一覧の取得・照会・更新・削除の API は、このセッションでは作りません（Session4 で管理者用に作ります）。

## 3-4. ステージを設定する

> **ステージと環境とは？**
> **環境** は、システムを動かす場所を、目的ごとに分けたものです。たとえば、作っている最中のものを試す **開発環境**、公開前に確かめる **検証環境**、利用者が実際に使う **本番環境** に分けます。環境を分けておくと、開発中の変更が本番の利用者に影響しません。
>
> API Gateway では、この環境の区分を **ステージ** で表します。同じ API を、`dev`、`stg`、`prod` のような名前のステージで別々に公開できます。ステージの名前は URL の一部になり、`https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev` のように、末尾にステージ名が付きます。
>
> | 環境 | ステージ名の例 |
> |---|---|
> | 開発環境 | `dev` |
> | 検証環境 | `stg`（`test` や `staging` も使われます） |
> | 本番環境 | `prod` |
>
> 名前を `$default` にしたステージは特別で、URL にステージ名が付きません。簡単に始めたいときに便利ですが、環境の区別がつかなくなります。

このハンズオンは学習用なので、開発環境にあたるステージ **`dev`** を 1 つだけ作ります。

1. ステージ名: 初期値の `$default` を消して、**`dev`** と入力する
2. **自動デプロイ** が有効になっていることを確認する（既定で有効）
3. **次へ** → **作成**

> **ポイント**: 設定を変えたら、自動デプロイが有効なら数秒で外に反映されます。無効なときは、**デプロイ** を押す必要があります。

## 3-5. API の URL を控える

1. 作成した API（`users-api-<名前>`）の画面を開く
2. **ステージ** で `dev` を選び、表示される **URL を呼び出す**（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev`）を控える。API の概要に表示される URL の場合は、末尾に `/dev` を付ける
3. 末尾に `/` は付けない

> この URL が、呼び出す側（Web の画面、Android アプリなど）に設定する値です。
>
> ルート `POST /` を呼ぶときは、`.../dev/` のように、URL の末尾に `/` を付けて送ります。この教材のコマンドと `app.js` は、`/` を付けて送る書き方にしてあります（控える URL 自体には `/` を付けません）。

### 確認ポイント

- [ ] ルート `POST /`（パスなし）があり、`users-function-<名前>` につながっている
- [ ] ステージが `dev`
- [ ] API の URL を控えた

## 3-6. Session1 のサイトに API URL を設定する

Session1 の静的サイトから API を呼ぶには、API の URL を `Session1/config.js` に設定します。`<API の URL>` は 3-5 で控えた値に置き換え、末尾に `/` は付けません。

```javascript
window.API_ENDPOINT = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev";
```

### Session1 のサイトを更新する

1. `Session1/config.js` の `window.API_ENDPOINT` に API の URL を設定する
2. AWS コンソールで Session1 の S3 バケットを開く
3. `config.js` をバケット直下へアップロードし、既存ファイルを置き換える（ほかのファイルを変えたときは、そのファイルも置き換える。`admin.html` と `admin.js` は別のバケットに置くため、ここでは上げません）
4. Amplify の `site-<名前>` アプリを開き、ブランチ `dev` の **更新をデプロイ** を実行する（[Session1 の 3-4](../Session1/README.md)）
5. Session1 のサイト URL（Amplify の URL）を開いて、会員登録フォームから登録を試す

Amplify で公開したサイトは、誰でも閲覧できます。機密情報は置かないでください。

### 確認ポイント

- [ ] `config.js` を S3 に置き換え、Amplify で再デプロイした
- [ ] 公開先の URL を控えた（次の CORS 設定で使用）
- [ ] `Session1/config.js` に API エンドポイントを設定した

## 3-7. CORS を設定する

CORS は、ブラウザーから別のドメインにある API を呼び出すときに必要な許可設定です。オリジンは、サイトの URL のうち、スキームとホスト名の部分です（例: `https://dev.<アプリID>.amplifyapp.com`）。このハンズオンでは、動作確認を優先して、許可するオリジンに `*`（すべてのオリジン）を指定します。

1. **API Gateway** → `users-api-<名前>` → **CORS** を開く（API の **設定** 内にある場合もあります）
2. 次のとおり設定する

   | 項目 | 設定値 |
   |---|---|
   | 許可されたオリジン（Access-Control-Allow-Origin） | `*`（すべてのオリジンを許可）。ハンズオン用の設定です |
   | 許可されたメソッド（Access-Control-Allow-Methods） | `POST`, `OPTIONS` |
   | 許可されたヘッダー（Access-Control-Allow-Headers） | `content-type` |
   | 認証情報（Access-Control-Allow-Credentials） | 無効 |

3. 保存する。ステージ `dev` の自動デプロイが有効なら、設定は自動で反映される

> **ハンズオン用の設定です。本来は、ドメイン（オリジン）を指定します**: `*` は、どのサイトのブラウザーからでも、この API を呼べるようにします。手順を簡単にするための設定で、実際のサービスでは使いません。
>
> - この API には認証がありません。ハンズオンが終わったら、3-9 の手順で API を削除してください。
> - `*` を指定するときは、認証情報（Access-Control-Allow-Credentials）を有効にできません。**無効** のままにします。
>
> HTTP API の CORS を API Gateway 側で設定した場合、API Gateway が CORS 応答ヘッダーを返し、プリフライト（OPTIONS）要求にも応答します。OPTIONS 用の Lambda ルートは追加しません。Lambda の応答側に別の CORS ヘッダーを追加しないでください。

### 【本来の設定】ドメイン（オリジン）を指定する

実際のサービスでは、`*` ではなく、**API を呼ぶサイトのドメインだけ** を指定します。Session1 で控えた Amplify の URL を使う場合の設定は、次のとおりです。

| 項目 | 本来の設定値 |
|---|---|
| 許可されたオリジン（Access-Control-Allow-Origin） | `https://dev.<アプリID>.amplifyapp.com`（Session1 の 3-3 で控えた URL。複数のサイトから使う場合は、それぞれ追加） |
| 許可されたメソッド | `POST`, `OPTIONS` |
| 許可されたヘッダー | `content-type` |
| 認証情報 | 無効 |

- **オリジンの書き方**: スキーム（`https://`）とホスト名までを、正確に書きます。パス（例: `/index.html`）や末尾の `/` は付けません。`http://` と `https://` は別のオリジンです。
- **`*` との違い**: ドメインを指定すると、そのサイト以外のブラウザーからの呼び出しは、ブラウザーが拒否します。3-8 の `curl.exe` の確認では、②（別のオリジン）の応答に `access-control-allow-origin` が出なくなります。
- **独自ドメインを使う場合**: Amplify に独自ドメインを設定したときは、その独自ドメイン（例: `https://www.example.com`）を指定します。

### 確認ポイント

- [ ] 許可されたオリジンを `*` にした（ハンズオン用。本来はドメインを指定する）
- [ ] `POST`, `OPTIONS` と `content-type` を許可した
- [ ] 認証情報は無効になっている

## 3-8. 動作を確かめる（PowerShell）

ブラウザや PowerShell から、実際に呼んで確かめます。`<API の URL>` は 3-5 で控えた値に置き換えてください。

### 会員を登録する（POST）

1. API の URL を変数に入れる（`xxxxxxxxxx` は 3-5 で控えた URL に置き換える）

   ```powershell
   $api = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev"
   ```

2. 登録する会員のデータ（本文）を変数に入れる

   ```powershell
   $body = '{"id":"u-0002","name":"鈴木愛子","email":"aiko@example.com","age":30,"address":"東京都千代田区1-1","tel":"09012345678"}'
   ```

3. API に送る

   ```powershell
   Invoke-RestMethod -Method Post -Uri "$api/" -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
   ```

> `$api` と `$body` は、同じ PowerShell の画面で続けて使います。画面を閉じたときは、1 と 2 をもう一度実行してください。
>
> **`"$api/"` の末尾の `/` は必要です。** ルート `POST /` は、ステージ名の後ろの `/` に当たります。`.../dev` だけで送ると `{"message":"Not Found"}` になります。

- 結果に `message` と `user` が出れば成功です。

### CORS の設定を確かめる（ブラウザーなし）

CORS を許可するかどうかを決めるのはブラウザーですが、ブラウザーが見るのは API の応答ヘッダーです。`Origin` ヘッダーを付けて `curl.exe` で呼ぶと、同じヘッダーを PowerShell から確かめられます。PowerShell の `curl` は別のコマンドの別名なので、必ず `curl.exe` と書きます。

```powershell
# ブラウザーが送るオリジン(Session1 の Amplify のサイト)
$origin = "https://dev.<アプリID>.amplifyapp.com"

# ① プリフライト: ブラウザーが POST の前に自動で送る OPTIONS を再現する
curl.exe -s -i -X OPTIONS "$api/" -H "Origin: $origin" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"

# ② 別のオリジンでも試す(`*` を許可しているので、こちらにも許可ヘッダーが返るのが正しい)
curl.exe -s -i -X OPTIONS "$api/" -H "Origin: http://example.com" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"
```

①の応答で、次を確かめます。

| 見る場所 | 正しい状態 |
|---|---|
| 1 行目 | `HTTP/1.1 204`（または `200`） |
| `access-control-allow-origin` | `*` |
| `access-control-allow-methods` | `POST` を含む |
| `access-control-allow-headers` | `content-type` を含む |

②の応答にも `access-control-allow-origin: *` が出ます。`*` はすべてのオリジンを許可する設定だからです。実際のサービスでオリジンを絞った場合は、②では出なくなります。

> `curl.exe` は CORS を強制しません。ヘッダーがなくてもリクエスト自体は成功するので、成功したかどうかではなく、ヘッダーの有無を読んでください。

### curl.exe で API をまとめてテストする

上の確認を、1 つのスクリプトで一度に行えます。[curl-test.ps1](curl-test.ps1) は、`curl.exe` で次の 6 つを順に確かめ、結果を `[OK]` と `[NG]` で表示します。

| 番号 | テスト | 期待する結果 |
|---|---|---|
| 1 | プリフライト | 204 または 200。`allow-origin` が `*`（オリジンを絞った場合は Origin と同じ値）。`allow-methods` に `POST`、`allow-headers` に `content-type` |
| 2 | プリフライト（別のオリジン） | `*` を許可しているので、`access-control-allow-origin` が `*` で返る（絞った場合は出ない） |
| 3 | 会員登録（正常） | 201。**実際の応答にも** `access-control-allow-origin` が付く |
| 4 | 同じ ID をもう一度登録 | 409 |
| 5 | 必須項目が足りない | 400 |
| 6 | JSON の形式が壊れている | 400 |

```powershell
cd <このリポジトリ>\Session3
.\curl-test.ps1 -Api "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev" -Origin "https://dev.<アプリID>.amplifyapp.com"
```

- `-Api` は 3-5 で控えた URL（ステージ名の `/dev` まで）、`-Origin` はブラウザーが送るオリジン（Amplify の URL）です。
- スクリプトを実行できない場合は、`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` を実行してからもう一度試します（今開いている PowerShell だけに効きます）。
- テスト 3 で、DynamoDB に会員を 1 件登録します（ID は `curl-<日時>`）。不要になったら、Session4 の管理画面か DynamoDB の画面で削除してください。

テスト 1・2 が失敗するときは、3-7 の CORS の設定（`*`、`POST`・`OPTIONS`、`content-type`）を見直してください。テスト 3 が 404 のときは 3-3 のルート（`POST /`）を、500 のときは Lambda の権限（2-6）を確認します。

### 確認ポイント

- [ ] POST で 201 相当の結果（`message` と `user`）が返る
- [ ] プリフライトの応答に、`access-control-allow-origin: *` と `POST`、`content-type` が出る
- [ ] 別のオリジンでも `access-control-allow-origin: *` が出る（`*` を許可しているため）

> **うまくいかないとき**
> - `{"message":"Not Found"}`（404）: API Gateway がルートを見つけられていません。次を順に確認してください。
>   1. URL の末尾に `/` を付けて送っているか（`.../dev/`）。付けないと、ルート `POST /` に届きません
>   2. ルートの一覧に `POST /` があるか（3-3）。`/v1/users` など別のパスで作っていないか
>   3. ステージ名が URL と合っているか（`dev`）
> - 500 エラー: Lambda の CloudWatch Logs を確認（2-7 の権限やテーブル名を見直す）
> - 日本語が文字化けして見える: PowerShell の表示の問題のことが多いです。データの中身は、Lambda の一覧で確かめてください。
>
> `Invoke-RestMethod` はブラウザーの CORS 制約を検査しません。CORS は上の `curl.exe` で応答ヘッダーを確かめ、最後は公開した Web アプリを実際にブラウザーで開いて確認してください。

## 3-9. 片付け（使い終わったら）

Session4 で、この Session の DynamoDB テーブルと Lambda 実行ロールを引き続き使います。**Session4 以降を進める場合は、すべての Session が終わってから** 削除してください。

次の順番で削除してください（依存があるので、この順です）。

1. Amplify の `site-<名前>` アプリを削除する
2. S3 のバケット内のオブジェクトを空にしてからバケットを削除する
3. API Gateway → `users-api-<名前>` を削除
4. Lambda → `users-function-<名前>` を削除
5. DynamoDB → `users-table-<名前>` テーブルを削除
6. IAM → 実行ロール（`users-function-<名前>-role-xxxx`）を削除（任意）

## 次の段階

Session3 の後は [Session4](../Session4/README.md) で、登録した会員を管理者が一覧・更新・削除できる管理画面を作成してください。
