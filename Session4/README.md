# Session4 — 管理者用の会員管理画面を作る（一覧・更新・削除）

Session3 では、会員登録（POST）だけを API にしました。Session4 では、管理者が登録済みの会員を **一覧表示・更新・削除** できる管理画面を作ります。この研修では認証（ログイン）は付けません。

## 構成

```text
管理者のブラウザー（管理画面用の S3 バケットの admin.html）
   │ GET / PUT / DELETE
   ▼
API Gateway HTTP API（users-admin-api-<名前>）
   │
   ▼
Lambda（users-admin-function-<名前>）
   │
   ▼
DynamoDB（users-table-<名前>）… Session2 で作ったテーブルを使う
```

会員登録の API（Session3 の `users-api-<名前>`）は POST のみのまま変えません。管理の機能は、別の API と Lambda に分けます。

管理画面の置き場所も、会員向けサイトとは **別の S3 バケット**（`<名前>-admin`）にします。個人情報を扱う画面の URL を、一般の会員に見せるサイトから切り離すためです。

## 事前準備

- [Session1](../Session1/README.md)〜[Session3](../Session3/README.md) を完了する
- Session3 の会員登録フォームから、会員を 1 件以上登録しておく
- AWS コンソールのリージョンを **アジアパシフィック（東京） `ap-northeast-1`** にする
- `<名前>` は Session2・Session3 と同じ値を使う

> **認証がないことに注意**: 管理 API は、会員の個人情報（名前、メールアドレス、住所、電話番号）を返し、削除もできます。この研修では手順を簡単にするため、**認証を付けていません**。API の URL と管理画面の URL を知っている人は、誰でも会員の閲覧・更新・削除ができます。
>
> - 研修で使うテスト用の会員データだけを登録し、**実在の個人情報は入れない**でください。
> - API の URL と管理画面の URL は、受講者以外に教えたり、画面共有や資料に載せたりしないでください。
> - 研修が終わったら、**必ず** 「片付け」の手順で API と管理画面用のバケットを削除してください。
> - 実際のサービスでは、ログイン（Amazon Cognito など）で管理者を確認してから、この種の API を公開します。

## コードの読み方（lambda_function.py・初心者向け）

`lambda_function.py` は、管理画面からの要求を受け取り、DynamoDB の会員データを一覧・取得・更新・削除する Python のプログラムです。Session2 の `app.py` と似ていますが、「登録」がありません。

### 用語の説明

| 用語 | 意味 |
|---|---|
| 認証 | 「その人が本人（管理者）か」を確かめることです。この研修では付けていません |
| 環境変数 | プログラムの外から渡す設定です。テーブル名を、コードに直接書かずに済みます |
| `ConditionExpression` | 「この条件のときだけ書き込む」という指定です。更新と削除で、会員がいるかを確かめるのに使います |

### 主な部分の説明

- **`TABLE_NAME`**: 読み書きするテーブル名です。環境変数から読みます。設定していないと、Lambda は起動時にエラー（`KeyError`）になります。
- **`list_users(query)`**: 会員を一覧で返します（`scan`）。一度に取る件数は `limit` で決め、続きがあるときは `nextToken` が付きます。
- **`get_user(user_id)`**: 会員を 1 件返します。
- **`update_user(user_id, event)`**: 会員の内容を書き換えます。`ConditionExpression="attribute_exists(id)"` は「その ID の会員がいるときだけ更新する」という条件です。いなければ 404 を返し、新しい会員を作ってしまうことを防ぎます。
- **`delete_user(user_id)`**: 会員を削除します。成功したときは本文のない 204 を返します。
- **`ROUTES`**: `"GET /users"` のような「メソッドと URL」と、呼び出す関数の対応表です。
- **`lambda_handler(event, context)`**: 要求の `routeKey` を `ROUTES` で探し、対応する処理を実行します。

### 返す番号（statusCode）の意味

| 番号 | 意味 |
|---|---|
| 200 | 成功（一覧・取得・更新） |
| 204 | 成功（本文なし。削除） |
| 400 | 送られたデータが正しくない |
| 404 | 対象の会員が見つからない |
| 500 | サーバー内部のエラー |

### 管理画面のコード（Session1 フォルダの admin.html・admin.js）

- `admin.html`: 会員の一覧表、ユーザIDの検索欄、表示をクリアするボタン、更新フォームがあります。更新フォームは、「編集」を押すまで隠れています。
- `admin.js`: ボタンを押したときの動きです。`callApi` が API を呼びます。ユーザIDで検索するときは、`GET /users/{id}` を呼んで 1 件だけ表示します。見つからないとき（404）は「見つかりませんでした」と表示します。
- 一覧に表示する名前や住所は、`textContent` で「ただの文字」として入れています。会員登録の内容は誰でも入力できるため、`<` などが含まれていても動かないようにするためです。
- 削除の前には、確認のダイアログを出します。

---

## 1. Lambda 関数を作成する

1. **Lambda** → **関数の作成** → **一から作成** を選ぶ
2. 次の設定で作成する

   | 項目 | 値 |
   |---|---|
   | 関数名 | `users-admin-function-<名前>` |
   | ランタイム | **Python 3.12** |
   | アーキテクチャ | **x86_64** |
   | 実行ロール | **既存のロールを使用する** → Session2 で作った `users-function-<名前>-role-xxxx` を選ぶ |

3. **コード** タブの `lambda_function.py` の初期コードをすべて削除し、このフォルダの `lambda_function.py` の内容を貼り付ける
4. **Deploy（デプロイ）** をクリックする
5. **ランタイム設定** のハンドラーが `lambda_function.lambda_handler` になっていることを確認する

> Session2 の実行ロールには、DynamoDB の権限（`AmazonDynamoDBFullAccess`）がすでに付いています。新しく権限を付ける必要はありません。

## 2. 環境変数を設定する

Lambda の **設定** タブ → **環境変数** → **編集** で、次を追加して **保存** する。

| キー | 値 |
|---|---|
| `TABLE_NAME` | `users-table-<名前>` |

## 3. Lambda 単体でテストする

`get-user.json`、`update-user.json`、`delete-user.json` の `u-0001` は、実際に登録した会員の ID に置き換えます。

1. **テスト** タブで **新しいイベント** を作り、`test-events/list-users.json` を貼り付けて実行する
   - `statusCode` が **200** で、`users` に登録済みの会員が出れば成功です
2. `test-events/get-user.json`（ID を置き換える）を実行する
   - `statusCode` が **200** で、`body` に 1 件の会員の情報が出れば成功です。存在しない ID で実行すると **404** になります
3. `test-events/update-user.json`（ID を置き換える）を実行する
   - `statusCode` が **200** になれば成功です。もう一度 `list-users.json` を実行し、年齢などが変わったことを確かめます
4. `test-events/delete-user.json` は、削除しても困らない会員の ID で実行する
   - `statusCode` が **204** で、一覧から消えれば成功です。同じ ID でもう一度実行すると **404** になります

> **エラーが出たら**: `KeyError: 'TABLE_NAME'` は環境変数の未設定です。`AccessDeniedException` は、実行ロールの DynamoDB 権限を確かめてください。

## 4. 管理画面用の S3 バケットを作る

会員向けサイト（Session1）とは別のバケットを作り、公開の設定をします。手順は [Session1](../Session1/README.md) の Step 1・3・4 と同じです。違うのは次の点だけです。

| 項目 | 値 |
|---|---|
| バケット名 | <font color="red">lastname-firstname-admin</font>（例：`yamada-taro-admin`） |
| パブリックアクセスをすべてブロック | チェックを外す |
| 静的ウェブサイトホスティング | 有効にする。インデックスドキュメントとエラードキュメントは、どちらも `admin.html` |
| バケットポリシー | Session1 の Step 4 と同じ内容。`Resource` のバケット名を `lastname-firstname-admin` にする |

> ファイルのアップロードは、手順 7 で行います。ウェブサイトエンドポイント（`http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com`）を控えておきます。手順 6 の CORS で使います。

## 5. HTTP API を作成する

1. **API Gateway** → **API を作成** → **HTTP API** → **構築** を選ぶ
2. 統合に Lambda の `users-admin-function-<名前>` を選び、API 名を `users-admin-api-<名前>` にする
3. ルートに、次の 4 つを追加する。統合先は、どれも `users-admin-function-<名前>` にする

   | メソッド | パス | 役割 |
   |---|---|---|
   | GET | `/users` | 会員の一覧を取得する |
   | GET | `/users/{id}` | 会員を 1 件取得する |
   | PUT | `/users/{id}` | 会員の内容を更新する |
   | DELETE | `/users/{id}` | 会員を削除する |

   > `{id}` は、実際の会員の ID が入る場所です。波括弧を含めてそのまま入力します。

4. ステージは `$default`、自動デプロイを有効にして作成する
5. API の URL（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com`）を控える。末尾の `/` は付けない

## 6. API の CORS を設定する

1. API Gateway で `users-admin-api-<名前>` を開き **CORS** を選ぶ
2. 次の値を設定する

   | 項目 | 値 |
   |---|---|
   | 許可されたオリジン | 手順 4 の **管理画面用バケット** のオリジン（`http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com`）。Session3 の会員向けサイトのオリジンとは別の値です |
   | 許可されたメソッド | `GET`, `PUT`, `DELETE`, `OPTIONS` |
   | 許可されたヘッダー | `content-type` |
   | 認証情報 | 無効 |

3. 保存する

> `PUT` や `DELETE` を許可しないと、ブラウザーが要求を止めてしまい、管理画面に「Failed to fetch」と出ます。ワイルドカード `*` は使わず、必要なオリジンだけを許可してください。

## 7. 管理画面に API の URL を設定して公開する

`Session1/config.js` の `window.ADMIN_API_ENDPOINT` に、手順 5 で控えた URL を設定します。末尾に `/` は付けません。

```javascript
window.ADMIN_API_ENDPOINT = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com";
```

手順 4 で作った **管理画面用のバケット** を開き、次の 4 ファイルをバケット直下にアップロードします。

- `admin.html`
- `admin.js`
- `styles.css`
- `config.js`

> 会員向けサイトのバケット(Session1)には、管理画面のファイルを置きません。管理画面は、この S3 バケットで公開します。

## 8. 管理画面で確かめる

1. ブラウザーで、管理画面用バケットの `admin.html` を開く(例: `http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com/admin.html`)
2. **会員一覧を取得** を押す
   - 登録済みの会員が表に出れば成功です
   - **表示をクリア** を押すと、表と検索欄が空に戻ります（会員のデータは消えません）
3. **ユーザIDで検索** の欄に登録済みのユーザIDを入れて **検索** を押す。その会員 1 件だけが表に出ることを確かめる。存在しないIDでは「見つかりませんでした」と出る（入力欄の例は `sample-0001`）
4. 会員の **編集** を押し、年齢などを変えて **更新** を押す。一覧の内容が変わることを確かめる
5. 削除しても困らない会員の **削除** を押し、確認のダイアログで OK を押す。一覧から消えることを確かめる

### PowerShell から API を呼んで確かめる（任意）

```powershell
$api = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com"
# 一覧
(Invoke-RestMethod -Uri "$api/users").users
```

## 確認ポイント

- [ ] Lambda のテストで、一覧が 200 で返る
- [ ] HTTP API に 4 つのルート（`GET /users`、`GET /users/{id}`、`PUT /users/{id}`、`DELETE /users/{id}`）がある
- [ ] 管理画面用の別バケットを作り、`admin.html` などをアップロードした
- [ ] CORS で管理画面用バケットのオリジンと、`GET`, `PUT`, `DELETE`, `OPTIONS`、`content-type` を許可した
- [ ] 管理画面で、一覧・ユーザIDでの検索・表示のクリア・更新・削除ができる

## よくあるトラブルと対処法

| 症状 | 確認すること |
|---|---|
| 「取得に失敗しました: Failed to fetch」 | CORS のオリジンとメソッド（`GET`, `PUT`, `DELETE`）を見直す。`config.js` の URL が正しいか、アップロードし直したかも確認する |
| 「管理 API の URL は Session4 で config.js に設定します」 | `config.js` の `ADMIN_API_ENDPOINT` が空。設定してアップロードし直す |
| 404 が返る | API のルートに `/users` と `/users/{id}` があるか、API の URL の末尾に余計なパスが付いていないかを確認する |
| 画面の変更が反映されない | `admin.html`・`admin.js`・`config.js` を管理画面用バケットにアップロードし直し、ブラウザーを再読み込みする |

## 片付け

認証のない API を残さないため、**研修が終わったらすぐに** 行ってください。

1. API Gateway の `users-admin-api-<名前>` を削除する
2. Lambda の `users-admin-function-<名前>` を削除する（実行ロールは Session2 と共有しているため、ここでは削除しない）
3. 管理画面用の S3 バケット(`lastname-firstname-admin`)を空にして削除する

Session2・Session3 のリソースは、これまでの手順どおり、すべての Session が終わってから削除します。

## 次へ

[Session5](../Session5/README.md) に進んでください。Amazon Bedrock で料理のおすすめを生成します。
