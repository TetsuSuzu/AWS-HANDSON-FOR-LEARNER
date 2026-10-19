# Session5 — Amazon Cognito で会員 API にログイン認証を追加する

Session3 で作った会員 API の全ルートを Cognito の JWT 認証で保護し、Session1 のサイトにログイン／ログアウトを追加します。ログインしていない場合、会員登録・一覧・取得・更新・削除 API は利用できません。

サイトは **AWS Amplify Hosting** で公開し、Cognito の設定値も API の URL と同じく **Amplify の環境変数** で渡します。S3 や CloudFront に `config.js` を手でアップロードする必要はありません。

## 構成

```text
Amplify Hosting（Session1 のサイト、HTTPS）
   │  環境変数 → amplify.yml → config.js（API URL・Cognito の設定値）
   │
   │ Cognito Hosted UI でログイン（Authorization Code + PKCE）
   │ Authorization: Bearer <トークン>
   ▼
API Gateway HTTP API（JWT authorizer）
   │
   ▼
Session2 の Lambda → DynamoDB
```

Bedrock のおすすめ API（Session4）はこのセッションでは保護しません。会員 API は Cognito、Bedrock API は Session4 で設定した CORS に従います。

## 事前準備

- [Session1](../Session1/README.md)〜[Session4](../Session4/README.md) を完了する
- Session3 で作成した **Amplify アプリ** と、ブランチの **HTTPS URL**（例: `https://<branch>.<app-id>.amplifyapp.com/`）を控える
- Session3 の API URL を控える
- Cognito のユーザープールは `ap-northeast-1` に作成する

> Cognito の callback URL には HTTP の URL は使えません。Amplify の URL は HTTPS です。

## 1. Cognito ユーザープールを作成する

1. AWS コンソールを `ap-northeast-1` にし、**Amazon Cognito** → **ユーザープールを作成** を選ぶ
2. サインイン識別子に **メールアドレス** を選び、セルフサービスサインアップを有効にする
3. パスワードポリシーと必要属性は教材の既定値を使う。メール認証が必要な場合は、画面の案内どおり Cognito のメール設定を行う
4. アプリケーションタイプは **Single-page application (SPA)** を選ぶ（public client。クライアントシークレットを作成しない）
5. アプリクライアント名を `users-site-<名前>` とし、作成する
6. 作成後、ユーザープール ID とアプリクライアント ID を控える

> **重要**: クライアントシークレットを発行・配布しないでください。ブラウザーに置く SPA は public client とし、Authorization Code Grant と PKCE を使います。

## 2. Cognito のドメインと OAuth を設定する

1. ユーザープールの **ドメイン** で Cognito ドメインを作成する。例: `users-site-<名前>-<一意な文字列>`
2. アプリクライアントの **ログインページ** または **Managed login** 設定を開く
3. OAuth 設定を次のとおりにする

   | 項目 | 値 |
   |---|---|
   | OAuth grant type | Authorization code grant |
   | OpenID Connect scopes | `openid`, `email`, `profile` |
   | Callback URL | Amplify の HTTPS URL（末尾の `/` を含む）。例: `https://<branch>.<app-id>.amplifyapp.com/` |
   | Sign-out URL | 同じ Amplify の URL |

4. 保存する。Cognito ドメイン URL は `https://<設定したドメイン>.auth.ap-northeast-1.amazoncognito.com` の形です。実際に表示された URL を控えてください

> **callback URL は次の手順の `COGNITO_CALLBACK_URL` と 1 文字も違えないでください。** スキーム・ホスト名・末尾の `/` が一致しないと、ログイン時に `redirect_mismatch` になります。

## 3. API Gateway に JWT authorizer を追加する

1. Session3 の `users-api-<名前>` を開く
2. **Authorization** → **Manage authorizers** → **Create**（コンソール表示に応じて **JWT authorizer** を追加）を選ぶ
3. 次の値を設定する

   | 項目 | 値 |
   |---|---|
   | Authorizer name | `cognito-users-authorizer` |
   | Identity source | `$request.header.Authorization` |
   | Issuer URL | `https://cognito-idp.ap-northeast-1.amazonaws.com/<ユーザープールID>` |
   | Audience | Cognito のアプリクライアント ID |

4. authorizer を保存する
5. API の **Routes** で次の 5 ルートそれぞれを開き、Authorization を `cognito-users-authorizer` に設定する

   - `POST /v1/users`
   - `GET /v1/users`
   - `GET /v1/users/{id}`
   - `PUT /v1/users/{id}`
   - `DELETE /v1/users/{id}`

6. CORS の設定で、許可オリジンに **Amplify の HTTPS URL**（スキームとホスト名。末尾の `/` は付けない）を含め、許可ヘッダーに `authorization` と `content-type` が含まれていることを確認する
7. `$default` ステージの自動デプロイが有効であることを確認する

認証済みリクエストでは API Gateway がトークンを検証してから Lambda を呼び出します。Lambda の実行ロールに Cognito 権限を付ける必要はありません。

## 4. Amplify の環境変数に Cognito の値を追加して再デプロイする

Session3・Session4 で登録した環境変数は残したまま、次の 3 つを追加します。

1. AWS Amplify のアプリを開き、**ホスティング** → **環境変数** を開く
2. 次のキーと値がそろっていることを確認し、不足分を追加する

   | キー | 値 | 登録元 |
   |---|---|---|
   | `API_ENDPOINT` | Session3 で控えた会員 API の URL（末尾に `/` は付けない） | Session3 |
   | `BEDROCK_API_ENDPOINT` | Session4 で控えた Bedrock API の URL | Session4 |
   | `COGNITO_DOMAIN` | Cognito ドメイン URL（`https://` を含む） | 今回 |
   | `COGNITO_CLIENT_ID` | アプリクライアント ID | 今回 |
   | `COGNITO_CALLBACK_URL` | Amplify の HTTPS URL（末尾の `/` を含む。Step 2 の callback URL と同じ値） | 今回 |

3. 保存し、**再デプロイ** する。環境変数を変えただけでは、ビルドし直すまで反映されません
4. デプロイ完了後、ブラウザーでサイトの URL の後ろに `/config.js` を付けて開き、4 つの値が入っていることを確認する

   ```text
   https://<branch>.<app-id>.amplifyapp.com/config.js
   ```

   > 値はブラウザーに配信される公開情報です。パスワードや秘密鍵などの秘密情報は環境変数に入れないでください。

Amplify の `amplify.yml` が、ビルド時に環境変数から `config.js` を生成します。`auth.js` は、この `config.js` の値を使って Cognito のログイン画面へ移動し、戻ってきた認証コードをトークンに交換します。

## 5. ログインと API をテストする

1. Amplify の HTTPS URL を開き、**ログイン** を押す
2. Cognito Hosted UI で **サインアップ** を選び、テスト用メールアドレスでアカウントを作る。確認コードが求められる場合はメールのコードを入力する
3. ログイン後、Session1 のサイトに戻り「ログイン中です。」と表示されることを確認する
4. 会員登録フォームからテスト用データを登録し、成功することを確認する
5. **ログアウト** してから再度登録する。API が 401 または 403 となり、登録できないことを確認する
6. 再ログインして、会員 API が利用できることを確認する

トークンは `sessionStorage` に保存され、ブラウザーのタブを閉じると消えます。有効期限が切れた場合は、もう一度ログインしてください。

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| Cognito で `redirect_mismatch` | Cognito の Callback URL と `COGNITO_CALLBACK_URL` が完全一致しているか（scheme、ホスト名、末尾の `/`） |
| ログインしても設定が入っていない | 環境変数を変えたあとに再デプロイしたか。`/config.js` を開いて値を確認する |
| ログイン後に状態エラー | 同じタブでログインを開始したか。Amplify の再デプロイ後にもう一度ログインする |
| API が 401 または 403 | Issuer URL、Audience、Bearer トークン、対象ルートの authorizer 設定 |
| CORS エラー | CORS の許可オリジンが Amplify の URL と一致し、`authorization` ヘッダーを許可しているか |
| 認証コードをトークンに交換できない | Cognito アプリクライアントに client secret がなく、Authorization code grant が有効か |

## 片付け

1. API Gateway の 5 ルートから authorizer を外すか、ハンズオン終了なら API を削除する
2. Cognito ユーザープールを削除する（作成したテストユーザーも削除されます）
3. 不要なら Amplify のアプリを削除する

## 次へ

管理者用会員管理を学ぶ場合は [Session7](../Session7/README.md) に進みます。
