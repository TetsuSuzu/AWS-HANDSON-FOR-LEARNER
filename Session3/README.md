# Session3 — HTTP API を作り、静的サイトから呼び出す

Lambda を、インターネットから呼べる URL（API）に公開します。

開始前に [Session2](../Session2/README.md) の DynamoDB と Lambda を作成・テストしてください。

> **API Gateway（HTTP API）とは？**
> 外からの要求（HTTP リクエスト）を受け付けて、対応する Lambda に渡す入口です。URL のパス（`/v1/users` など）と、メソッド（GET、POST など）ごとに、どの処理に渡すかを決めます。

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

**ルート** は、「どのメソッドと URL の組み合わせを、どの Lambda に渡すか」の一覧です。次の 5 つを作ります。

| メソッド | パス | 役割 |
|---|---|---|
| POST | `/v1/users` | 会員を登録する |
| GET | `/v1/users` | 会員の一覧を取る |
| GET | `/v1/users/{id}` | 会員を 1 件取る |
| PUT | `/v1/users/{id}` | 会員の内容を更新する |
| DELETE | `/v1/users/{id}` | 会員を削除する |

> **`{id}` とは？**
> URL の中の「変わる部分」です。`/v1/users/u-0001` と呼ぶと、`id` は `u-0001` になり、Lambda に渡されます。

### 作り方

1. ルートの画面で **ルートを追加** をクリック
2. メソッドとパスを入力し、統合先に `users-function-<名前>` を選ぶ
3. 上の表の 5 つをすべて追加する
4. **次へ**

> 「ルートの追加」を繰り返すと、統合先の選択を忘れやすいので、5 つすべてで `users-function-<名前>` になっているか確認してください。

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

- [ ] 5 つのルートがあり、すべて `users-function-<名前>` につながっている
- [ ] ステージが `$default`
- [ ] API の URL を控えた

## 3-6. Session1 のサイトに API URL を設定する

Session1 の静的サイトから API を呼ぶには、API の URL を `Session1/config.js` に設定します。`<API の URL>` は 3-5 で控えた値に置き換え、末尾に `/` は付けません。

```javascript
window.API_ENDPOINT = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com";
```

### 方法 A：Session1 の S3 静的サイトを更新する

1. `Session1/config.js` の `window.API_ENDPOINT` に API の URL を設定する
2. AWS コンソールで Session1 の S3 バケットを開く
3. `index.html`、`config.js`、`styles.css`、`photo1.png`、`photo2.png` をバケット直下へアップロードし、既存ファイルは置き換える
4. Session1 で CloudFront も作成している場合は、ディストリビューションの **Invalidations** から `/*` を無効化する
5. Session1 のサイト URL を開いて、会員登録フォームから登録を試す

S3 ウェブサイトエンドポイントは HTTP です。CloudFront を利用する場合は HTTPS の CloudFront ドメインを使ってください。S3 の静的ウェブサイトホスティングはウェブサイトファイルを公開します。機密情報は置かないでください。

### 方法 B：AWS Amplify Hosting

このリポジトリの `Session1` は HTML/CSS/JavaScript の静的サイトで、Node.js の依存パッケージはありません。リポジトリのルートにある `amplify.yml` が、Amplify のビルド時に環境変数から `Session1/config.js` を生成します。

1. AWS マネジメントコンソールで **AWS Amplify** を開き、**新しいアプリを作成** → **Git リポジトリをホスト** を選ぶ
2. GitHub などのプロバイダーを接続し、この教材リポジトリとブランチを選択する
3. ビルド設定でリポジトリルートの `amplify.yml` が使われることを確認する
4. アプリの **環境変数（Environment variables）** を開き、次を追加する

   | キー | 値 |
   |---|---|
   | `API_ENDPOINT` | 3-5 で控えた API の URL（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com`） |

5. 保存してビルド・デプロイする。環境変数を後から変更した場合は再デプロイする
6. デプロイ完了後に表示される Amplify のブランチ URL を控える

> `API_ENDPOINT` はビルドでブラウザーに配信する設定値です。API URL は公開情報ですが、パスワードや秘密鍵などの秘密情報を環境変数に入れないでください。

> Session4 で Bedrock API を追加するときは、同じ Amplify アプリの `BEDROCK_API_ENDPOINT` 環境変数も登録して再デプロイします。

### 確認ポイント

- [ ] Session1 のサイトを更新した、または Amplify Hosting にデプロイした
- [ ] 公開先の URL を控えた（次の CORS 設定で使用）
- [ ] `Session1/config.js` または Amplify 環境変数に API エンドポイントを設定した

## 3-7. CORS を設定する

CORS は、ブラウザーから別のドメインにある API を呼び出すときに必要な許可設定です。Session1 の S3 ウェブサイトエンドポイント、CloudFront、または Amplify で公開した URL の「オリジン」（スキームとホスト名。パスや末尾の `/` は含めない）を許可します。

1. **API Gateway** → `users-api-<名前>` → **CORS** を開く（API の **設定** 内にある場合もあります）
2. 次のとおり設定する

   | 項目 | 設定値 |
   |---|---|
   | 許可されたオリジン（Access-Control-Allow-Origin） | 実際にブラウザーで開くサイトのオリジン。S3 ウェブサイトは `http://<バケット名>.s3-website-ap-northeast-1.amazonaws.com`、CloudFront は `https://<ディストリビューションのドメイン名>`、Amplify はデプロイ画面に表示されたブランチ URL。複数の URL から使う場合は各オリジンを追加 |
   | 許可されたメソッド（Access-Control-Allow-Methods） | `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS` |
   | 許可されたヘッダー（Access-Control-Allow-Headers） | `content-type` |
   | 認証情報（Access-Control-Allow-Credentials） | 無効 |

3. 保存する。ステージ `$default` の自動デプロイが有効なら、設定は自動で反映される

> **注意**: URL に含まれるスキーム（`http://` または `https://`）とホスト名を正確に登録します。末尾にパス（例: `/index.html`）や `/` を付けません。`*` の許可は使わず、必要なサイトだけを登録します。
>
> HTTP API の CORS を API Gateway 側で設定した場合、API Gateway が CORS 応答ヘッダーを返し、プリフライト（OPTIONS）要求にも応答します。OPTIONS 用の Lambda ルートは追加しません。Lambda の応答側に別の CORS ヘッダーを追加しないでください。

### 確認ポイント

- [ ] 実際のフロントエンド URL のオリジンを許可した
- [ ] `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS` と `content-type` を許可した
- [ ] 認証情報は無効になっている

## 3-8. 動作を確かめる（PowerShell）

ブラウザや PowerShell から、実際に呼んで確かめます。`<API の URL>` は 3-5 で控えた値に置き換えてください。

### 会員を登録する（POST）

```powershell
$api = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com"
$body = '{"id":"u-0001","name":"山田太郎","email":"taro@example.com","age":30,"address":"東京都千代田区1-1","tel":"09012345678"}'
Invoke-RestMethod -Method Post -Uri "$api/v1/users" -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

- 結果に `message` と `user` が出れば成功です。

### 一覧を取る（GET）

```powershell
Invoke-RestMethod -Uri "$api/v1/users?limit=20"
```

- `users` の中に、登録した `u-0001` が出れば成功です。

### 1 件取る（GET）

```powershell
Invoke-RestMethod -Uri "$api/v1/users/u-0001"
```

### 更新する（PUT）

```powershell
$body = '{"id":"u-0001","name":"山田次郎","email":"taro@example.com","age":31,"address":"東京都千代田区1-1","tel":"09012345678"}'
Invoke-RestMethod -Method Put -Uri "$api/v1/users/u-0001" -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

### 削除する（DELETE）

```powershell
Invoke-WebRequest -Method Delete -Uri "$api/v1/users/u-0001" -UseBasicParsing | Select-Object StatusCode
```

- `StatusCode` が **204** なら成功です（本文は空）。

### 確認ポイント

- [ ] POST で 201 相当の結果（`message` と `user`）が返る
- [ ] GET 一覧に登録した会員が出る
- [ ] PUT で `name` が「山田次郎」に変わる
- [ ] DELETE 後、GET 1 件で 404（見つからない）になる

> **うまくいかないとき**
> - 404 Not Found: パスの綴りを確認（`/v1/users` の `v1` を忘れていないか）
> - 500 エラー: Lambda の CloudWatch Logs を確認（2-7 の権限やテーブル名を見直す）
> - 日本語が文字化けして見える: PowerShell の表示の問題のことが多いです。データの中身は、Lambda の一覧で確かめてください。
>
> PowerShell の呼び出しは API の動作確認には使えますが、ブラウザーの CORS 制約は検査しません。CORS を含めた確認には、公開した Web アプリを実際にブラウザーで開いて API を呼び出してください。

## 3-9. 片付け（使い終わったら）

次の順番で削除してください（依存があるので、この順です）。

1. CloudFront を使った場合は、CloudFront ディストリビューションを無効化し、無効化が完了してから削除する（無効化には時間がかかります）
2. S3 を使った場合は、バケット内のオブジェクトを空にしてからバケットを削除する
3. Amplify を使った場合は、Amplify コンソールでアプリを削除する
4. API Gateway → `users-api-<名前>` を削除
5. Lambda → `users-function-<名前>` を削除
6. DynamoDB → `users-table-<名前>` テーブルを削除
7. IAM → 実行ロール（`users-function-<名前>-role-xxxx`）を削除（任意）

## 次の段階

Session3 の後は [Session4](../Session4/README.md) で Bedrock の料理おすすめ機能を追加してください。
