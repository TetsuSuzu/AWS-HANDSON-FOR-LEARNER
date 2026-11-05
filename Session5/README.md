# Session5 — Amazon Cognito でサインアップとログインを付ける

Session3 の会員登録 API と Session4 の管理 API は、URL を知っていれば誰でも呼べました。Session5 では、Amazon Cognito を使って、次の 2 つを付けます。

- **5-A（主役）**: 会員が、ユーザID・メールアドレス・パスワードで **サインアップ** し、メールに届いた **確認コード** で確認してから **ログイン** し、会員情報を登録する。ログインしていない人や、他人の ID では登録できない
- **5-B（後半）**: 管理 API と管理画面を、**管理者グループ（`admins`）に入った人だけ** が使えるようにする

## 事前準備

- [Session1](../Session1/README.md)〜[Session4](../Session4/README.md) を完了する
- AWS コンソールのリージョンを **アジアパシフィック（東京） `ap-northeast-1`** にする
- `<名前>` は Session2〜4 と同じ値を使う
- 確認コードを受け取れる **自分のメールアドレス** を用意する（研修用のアドレスで構いません）
- 6 の PowerShell の確認では **AWS CLI v2** を使います。`aws --version` で入っているか確かめてください（5-B の 5 も同じです）。入っていない場合は、5-A の 6 と 5-B の 5 を飛ばしても構いません。そのあとの画面での確認（5-A の 7、5-B の 6）が、どちらの代わりにもなります

この Session で使う、これまでのリソースは次のとおりです。

| リソース | 作った Session | この Session でやること |
|---|---|---|
| Lambda `users-function-<名前>` | Session2 | コードを `Session5/lambda_function.py` に貼り替える |
| HTTP API `users-api-<名前>`（ルート `POST /`、ステージ `dev`） | Session3 | JWT オーソライザーを付け、CORS に `authorization` を足す |
| 会員向けサイト（S3 バケット、Amplify `site-<名前>`） | Session1・3 | `config.js` などを置き換えて、更新をデプロイ |
| Lambda `users-admin-function-<名前>` | Session4 | コードを `Session5/admin_lambda_function.py` に貼り替える |
| HTTP API `users-admin-api-<名前>`（4 つのルート、ステージ `dev`） | Session4 | JWT オーソライザーを付け、CORS に `authorization` を足す |
| 管理画面（S3 バケット `lastname-firstname-admin`、Amplify `admin-<名前>`） | Session4 | `config.js` などを置き換えて、更新をデプロイ |

> **Session5 の途中は、画面から会員登録できない時間があります**: 5-A の 3 で `POST /` にオーソライザーを付けると、ログインの仕組みが入る前の画面（Session3 の画面）からは登録できなくなります（401）。5-A の 7 まで進めば、また登録できます。管理画面も同じで、5-B の 2 から 6 までの間は使えません。

---

## この Session で学ぶこと（講義）

### 認証と認可

| 用語 | 意味 | この Session では |
|---|---|---|
| 認証 | 「あなたは誰か」を確かめること | Cognito のユーザID とパスワードで確かめる |
| 認可 | 「何をしてよいか」を決めること | ① ログインした本人の ID でだけ会員登録できる ② 管理者グループの人だけが管理 API を使える |

Session4 までは、認証も認可もありませんでした。Session5 で、その両方を簡単な形で付けます。

### 使う 3 つの部品

| 部品 | 役割 | たとえ |
|---|---|---|
| **Amazon Cognito ユーザープール** | ユーザーの名簿を持ち、サインアップとログインを受け付ける | 会員証を発行する受付 |
| **JWT（ID トークン）** | ログインに成功した人に渡される、電子的な通行証 | 受付が渡す入館証 |
| **JWT オーソライザー** | API Gateway の入口で、通行証を確かめる | 入口の守衛 |

### Cognito ユーザープールとは

**ユーザーの名簿と、ログインの仕組みをまとめて引き受けてくれる AWS のサービス**です。パスワードの保管、パスワードの強さの確認、確認コードのメール送信、ログイン後の通行証（トークン）の発行を、Cognito が行います。自分でパスワードを保存するプログラムを書く必要はありません。

この教材では、**サインインに使う名前（ユーザー名）を、そのまま会員 ID にします**。サインアップで入力したユーザID（例: `member-0001`）が、Session2 から使っている会員の `id` になります。

### サインアップと確認コード

会員が自分で名簿に登録することを **サインアップ** といいます。この教材の流れは次のとおりです。

```text
① サインアップ: ユーザID・メールアドレス・パスワードを Cognito に送る
② Cognito が、入力されたメールアドレスに確認コード（数字）を送る
③ 確認: メールに届いたコードを入力する（本当にそのメールアドレスの持ち主かを確かめる）
④ ログイン: ユーザID とパスワードで ID トークンを受け取る
⑤ 会員情報の登録: ID トークンを付けて、名前・年齢・住所・電話番号を登録する（POST /）
```

③ が済むまで、そのユーザーはログインできません（`UserNotConfirmedException`）。

### JWT とは

JWT（ジョット、JSON Web Token）は、「この人は○○さんで、Cognito が確認済み」という内容が書かれた文字列です。3 つの部分をピリオド（`.`）でつないでいます。

```text
xxxxxxxx.yyyyyyyy.zzzzzzzz
ヘッダー . 中身 . 署名
```

| 部分 | 入っているもの |
|---|---|
| ヘッダー | 署名の方式 |
| 中身 | ユーザーの情報（クレーム）、有効期限、発行元（どのユーザープールか）、対象のアプリクライアント |
| 署名 | 発行元（Cognito）だけが付けられる印。書き換えると合わなくなる |

中身に入っている情報の 1 つ 1 つを **クレーム** といいます。この教材で使う主なクレームは次のとおりです。

| クレーム | 中身 | 使う場所 |
|---|---|---|
| `cognito:username` | ユーザー名（= 会員 ID） | 会員 API の本人確認 |
| `email` | メールアドレス | 会員 API の本人確認 |
| `cognito:groups` | 入っているグループ（例: `admins`） | 管理 API の管理者確認 |
| `iss` | 発行元（ユーザープールの URL） | JWT オーソライザー |
| `aud` | 対象のアプリクライアント ID | JWT オーソライザー |
| `exp` | 有効期限 | JWT オーソライザー |

> **ポイント**: JWT の中身は暗号ではなく、誰でも読めます。**パスワードなどの秘密は入っていません**が、他人に見せないでください。通行証を拾った人は、有効期限が切れるまで本人としてふるまえます。

### JWT オーソライザーとは

**API の入口で、通行証（JWT）を確かめる、API Gateway の機能**です。確かめるのは次の 3 点です。

1. **署名が正しいか**: 自分のユーザープール（Cognito）が発行したものか。書き換えられていないか
2. **有効期限が切れていないか**（ID トークンの既定は 1 時間）
3. **対象のアプリクライアント向けか**: この教材のアプリクライアント向けに発行されたものか

3 点がそろえば Lambda に渡し、そろわなければ **401（認証されていない）** を返します。Lambda には、確かめ終わったクレームが `requestContext.authorizer.jwt.claims` として届きます。

```text
① ブラウザー ── ユーザID・パスワード ──▶ Cognito ユーザープール
② ブラウザー ◀── ID トークン（JWT） ──── Cognito ユーザープール
③ ブラウザー ── API 呼び出し + Authorization ヘッダー（JWT）──▶ API Gateway
                                  │ JWT オーソライザーが確認
                                  ▼
                   OK → Lambda（クレーム付き） ／ NG → 401（Lambda は呼ばれない）
```

### 認証は入口で、細かい認可は Lambda で

JWT オーソライザーが確かめるのは「Cognito が発行した、期限内の通行証か」までです。「**誰が** 何をしてよいか」は、Lambda がクレームを見て決めます。

| 確認 | どこで | 合わないとき |
|---|---|---|
| 通行証が本物で期限内か | JWT オーソライザー（API Gateway） | 401 |
| 登録する `id`・`email` が、ログインした本人のものか | 会員 API の Lambda（`check_owner`） | 403「ログインした本人の ID・メールアドレスで登録してください」 |
| ログインした人が `admins` グループに入っているか | 管理 API の Lambda（`require_admin`） | 403「管理者のみ利用できます」 |

> **401 と 403 の違い**: 401 は「あなたが誰か分からない（通行証がない・期限切れ・偽物）」、403 は「あなたが誰かは分かったが、それはできない」です。

### 何がうれしいか

- **ログインしていない呼び出しは Lambda に届かない**ので、Lambda の実行や DynamoDB へのアクセスが発生しません。
- 認証の仕組みを自作せず、AWS のサービスに任せられます（パスワードの保管や確認、確認コードのメール送信を自分で書かなくてよい）。
- Lambda は、確かめ済みのクレームを読むだけで「誰か」が分かります。署名の検証を Lambda で書く必要はありません。

### 保護する範囲

| API | ルート | 入口（JWT オーソライザー） | Lambda での確認 |
|---|---|---|---|
| 会員 API `users-api-<名前>`（Session3） | `POST /` | 必須 | 本文の `id` = `cognito:username`、本文の `email` = トークンの `email`（違えば 403） |
| 管理 API `users-admin-api-<名前>`（Session4） | `GET /users`、`GET /users/{id}`、`PUT /users/{id}`、`DELETE /users/{id}` | 必須 | `cognito:groups` に `admins` が含まれる（なければ 403） |

料理のおすすめ（[Session6](../Session6/README.md)・[Session7](../Session7/README.md)）の API には、この Session では保護を付けません。

### この Session の構成

```text
会員のブラウザー（index.html）                     管理者のブラウザー（admin.html）
   │ ① サインアップ・確認コード・ログイン              │ ① ログイン
   ▼                                                  ▼
             Cognito ユーザープール（users-pool-<名前>）
             └ グループ admins（管理者だけ）
   │ ② ID トークン                                    │ ② ID トークン
   ▼                                                  ▼
API Gateway（users-api-<名前>）               API Gateway（users-admin-api-<名前>）
   │ JWT オーソライザー                               │ JWT オーソライザー
   ▼                                                  ▼
Lambda（users-function-<名前>）               Lambda（users-admin-function-<名前>）
   │ 本人確認（check_owner）                          │ 管理者確認（require_admin）
   └──────────────▶ DynamoDB（users-table-<名前>）◀──────────────┘
```

> **注意（この教材の範囲）**: ID トークンは、画面を開いている間だけ、ブラウザーのメモリに持ちます（`localStorage` などには保存しません）。有効期限（1 時間）が切れたら、もう一度ログインします。トークンの更新（リフレッシュ）は扱いません。

---

## 5-A. サインアップから会員情報の登録まで

## 1. ユーザープールを作る

1. 検索欄に **Cognito** と入力して開く。リージョンが **ap-northeast-1** であることを確認する
2. **ユーザープールを作成**（Create user pool）をクリックする
3. 次のとおり設定して作成する

   | 項目 | 設定値 |
   |---|---|
   | アプリケーションタイプ | **シングルページアプリケーション（SPA）**（ブラウザーの JavaScript から使うため） |
   | アプリケーション名（アプリクライアント名） | `users-client-<名前>` |
   | サインイン識別子のオプション | **ユーザー名** だけにチェック（メールアドレス・電話番号にはチェックしない） |
   | 自己登録（セルフサインアップ） | **有効** |
   | サインアップに必要な属性 | **email** |
   | リターン URL | 空のまま（この教材は Cognito のログイン画面を使いません。入力が必須の場合は、Session1 の Amplify の URL を入れる） |
   | ユーザープール名（入力欄がある場合） | `users-pool-<名前>` |

> **重要**: サインイン識別子は、作成後に変えられません。**ユーザー名を選んでください**。メールアドレスだけを選ぶと、ユーザー名が自動の値になり、会員 ID として使えません（ユーザー名とメールアドレスを両方選ぶと、メールアドレスは別名になります）。間違えたときは、ユーザープールを削除して作り直してください。
>
> コンソールの画面は変わることがあります。上の項目名が見つからないときは、同じ働きの設定を探してください。

4. 作成できたら、ユーザープールの画面で次の設定を確かめる（既定の値のままで構いません）

   | 確かめる設定 | 正しい状態 |
   |---|---|
   | ユーザープール名 | `users-pool-<名前>`（作成時に名前が自動で付いた場合は、名前を変更できれば変更する。変更できなくても、ユーザープール ID を控えれば手順に影響はありません） |
   | 多要素認証（MFA） | なし（この教材では使いません） |
   | 属性の検証（サインアップ時の確認） | メールアドレスを **確認コード** で検証する（Cognito が自動でメールを送る） |
   | メールの送信 | **Cognito でメールを送信**（Cognito の既定の送信。Amazon SES は使いません） |
   | パスワードポリシー | Cognito の既定（8 文字以上、大文字・小文字・数字・記号を含む） |

> **メールの注意**:
> - Cognito の既定のメール送信は、**1 日あたり約 50 通** までです（AWS アカウントごと）。研修で同じ AWS アカウントを大勢で使うと、上限に達してメールが届かなくなることがあります。サインアップのやり直しは、むやみに繰り返さないでください。
> - 確認コードのメールは `no-reply@verificationemail.com` から届きます。届かないときは **迷惑メール** のフォルダを確かめてください。

5. ユーザープールの概要に出る **ユーザープール ID**（例: `ap-northeast-1_AbCdEfGhI`）を控える

> この後の手順で `users-pool-<名前>` を開くとき、名前が違う場合は、控えたユーザープール ID で探してください。

## 2. アプリクライアントを設定する

1 で作ったアプリクライアント（`users-client-<名前>`）を確かめ、ユーザID とパスワードで直接ログインできるようにします。

1. ユーザープールの **アプリケーションクライアント**（App clients）を開き、`users-client-<名前>` を選ぶ
2. 次を確かめる

   | 項目 | 正しい状態 |
   |---|---|
   | クライアントシークレット | **なし**（ブラウザーで使う公開のクライアントには、シークレットを付けません） |

3. **認証フロー**（Authentication flows）の **編集** を開き、次の 2 つにチェックが入っている状態にして保存する。ほかのチェックは、そのままで構いません

   | 認証フロー | 意味 |
   |---|---|
   | `ALLOW_USER_PASSWORD_AUTH` | ユーザID とパスワードでログインする（この教材の画面と PowerShell が使う） |
   | `ALLOW_REFRESH_TOKEN_AUTH` | トークンを更新する（この教材では使いませんが、既定で付いています） |

4. **クライアント ID**（例: `1a2b3c4d5e6f7g8h9i0j1k2l3m`）を控える

### 控える値

| 値 | 例 | 使う場所 |
|---|---|---|
| ユーザープール ID | `ap-northeast-1_AbCdEfGhI` | 3 の発行者 URL |
| クライアント ID | `1a2b3c4d5e6f7g8h9i0j1k2l3m` | 3 の対象者、6 の PowerShell、7 の `config.js` |

> **クライアント ID は秘密ではありません**: ブラウザーの `config.js` に書いて、誰でも見られる状態で公開します。シークレットのない公開クライアントなので、それで構いません。逆に、**秘密の値（クライアントシークレット、AWS のアクセスキーなど）は、JavaScript に絶対に書かないでください**。

### 確認ポイント

- [ ] ユーザープールのサインイン識別子が **ユーザー名** だけ
- [ ] 必須の属性が `email`、自己登録が有効、メールアドレスを確認コードで検証する
- [ ] アプリクライアントにシークレットがなく、`ALLOW_USER_PASSWORD_AUTH` が有効
- [ ] ユーザープール ID とクライアント ID を控えた

## 3. 会員 API に JWT オーソライザーを付ける

1. **API Gateway** → `users-api-<名前>` を開く
2. 左のメニューの **認可**（Authorization）を開く
3. ルートの一覧で **`POST /`** を選び、**オーソライザーを作成してアタッチ**（Create and attach an authorizer）をクリックする
4. 次のとおり入力して作成する

   | 項目 | 入力する値 |
   |---|---|
   | オーソライザーのタイプ | **JWT** |
   | 名前 | `cognito-<名前>` |
   | ID ソース（Identity source） | `$request.header.Authorization`（初期値のまま） |
   | 発行者 URL（Issuer URL） | `https://cognito-idp.ap-northeast-1.amazonaws.com/<ユーザープールID>` |
   | 対象者（Audience） | 2 で控えた **クライアント ID** |

   発行者 URL の例: `https://cognito-idp.ap-northeast-1.amazonaws.com/ap-northeast-1_AbCdEfGhI`

5. ルートの一覧で、`POST /` に `JWT` のオーソライザーが付いたことを確かめる

> **ポイント**:
> - 発行者 URL の末尾に `/` を付けないでください。ユーザープール ID の大文字・小文字も、そのまま書きます。1 文字でも違うと、正しいトークンでも 401 になります。
> - ステージ `dev` の自動デプロイが有効なので、保存すると数秒で反映されます（Session3 の 3-4）。
> - この時点から、トークンのない `POST /` は 401 になります。

## 4. 会員 API の CORS に `authorization` を足す

ブラウザーは、`Authorization` ヘッダーを付けた要求を送る前に、プリフライト（OPTIONS）で「このヘッダーを送ってよいか」を API に尋ねます。Session3 の 3-7 では `content-type` だけを許可したので、`authorization` を足します。

1. **API Gateway** → `users-api-<名前>` → **CORS** を開き、**設定**（編集）をクリックする
2. **許可されたヘッダー**（Access-Control-Allow-Headers）に `authorization` を追加する。ほかの値は Session3 のまま変えない

   | 項目 | 設定値 |
   |---|---|
   | 許可されたオリジン | Session3 で設定した値のまま（`*` またはサイトのオリジン） |
   | 許可されたメソッド | `POST`, `OPTIONS`（Session3 のまま） |
   | 許可されたヘッダー | `content-type`, **`authorization`** |
   | 認証情報 | 無効（Session3 のまま） |

3. 保存する

> プリフライト（OPTIONS）は、API Gateway が CORS の設定に従って答えます。オーソライザーは OPTIONS には働かないので、OPTIONS のルートを追加する必要はありません。

## 5. 会員 API の Lambda を貼り替える

1. **Lambda** → `users-function-<名前>` を開く
2. **コード** タブの `lambda_function.py` の中身をすべて削除し、`Session5/lambda_function.py` の内容を貼り付ける（先頭から末尾まで全部置き換える）
3. **Deploy（デプロイ）** をクリックする

> 環境変数 `TABLE_NAME`（`users-table-<名前>`）、実行ロール、ハンドラー（`lambda_function.lambda_handler`）は、Session2 のまま変えません。

Session2 のコードとの違いは、`check_owner` が加わったことだけです。

- `get_claims(event)`: JWT オーソライザーが確かめたクレーム（`event["requestContext"]["authorizer"]["jwt"]["claims"]`）を取り出します。クレームがない（Lambda の画面のテストなど）ときは空です。
- `check_owner(event, user)`: クレームがあるとき、本文の `id` がトークンの `cognito:username` と、本文の `email` がトークンの `email` と同じかを確かめます。違えば 403「ログインした本人の ID・メールアドレスで登録してください」を返します。
- クレームがないときは確認を省くので、Session2 のテストイベント（`Session2/test-events/create-user.json`）は今までどおり動きます。

## 6. PowerShell で確かめる

AWS CLI の `aws cognito-idp` コマンドで、サインアップからログインまでを行い、受け取った ID トークンで API を呼びます。同じ PowerShell の画面で、上から順に実行してください（画面を閉じたら、変数の設定からやり直します）。

> `sign-up`・`confirm-sign-up`・`initiate-auth` の 3 つは、ログイン前の人が使う操作なので、AWS のアクセスキー（`aws configure`）の設定がなくても実行できます。

### 6-1. 値を変数に入れる

```powershell
$api = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev"   # Session3 で控えた会員 API の URL
$region = "ap-northeast-1"
$clientId = "<クライアントID>"        # 2 で控えた値
$user = "member-0001"                 # 会員 ID になるユーザID（英数字とハイフン）
$email = "<自分のメールアドレス>"     # 確認コードを受け取るアドレス
$password = 'Handson-2026!'           # 8 文字以上、大文字・小文字・数字・記号を含む
```

> パスワードには `,`（カンマ）と `$` を使わないでください。下のコマンドで、区切りや変数と間違えられます。

### 6-2. トークンなしで呼ぶと 401 になる

```powershell
$body = @{ id = $user; name = "鈴木愛子"; email = $email; age = 30; address = "東京都千代田区1-1"; tel = "09012345678" } | ConvertTo-Json
try {
    Invoke-RestMethod -Method Post -Uri "$api/" -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
} catch {
    [int]$_.Exception.Response.StatusCode   # 401 が出れば正しい
    $_.ErrorDetails.Message                 # {"message":"Unauthorized"}
}
```

### 6-3. サインアップする

```powershell
aws cognito-idp sign-up --region $region --client-id $clientId --username $user --password $password --user-attributes "Name=email,Value=$email"
```

- `UserConfirmed` が `false`、`CodeDeliveryDetails` に送り先のメールアドレス（一部が `*` で隠れたもの）が出れば成功です。
- メールに **確認コード**（数字 6 桁）が届きます。

### 6-4. 確認コードで確認する

`<確認コード>` は、メールに届いた数字に置き換えます。

```powershell
aws cognito-idp confirm-sign-up --region $region --client-id $clientId --username $user --confirmation-code <確認コード>
```

- 何も表示されずに終われば成功です。

> **メールがどうしても届かないとき（代わりの方法）**: Cognito の画面で、ユーザープール → **ユーザー** → `member-0001` を開き、アカウントを確認する操作（Confirm account）を行います。AWS のアクセスキーを設定済みなら、`aws cognito-idp admin-confirm-sign-up --region $region --user-pool-id <ユーザープールID> --username $user` でも確認できます。どちらも管理者の操作なので、メールアドレスの持ち主かどうかは確かめられません。研修でメールが届かないときだけ使ってください。

### 6-5. ログインして ID トークンを受け取る

```powershell
$token = aws cognito-idp initiate-auth --region $region --client-id $clientId --auth-flow USER_PASSWORD_AUTH --auth-parameters "USERNAME=$user,PASSWORD=$password" --query "AuthenticationResult.IdToken" --output text
$token.Substring(0, 20)   # eyJ で始まる長い文字列なら成功（全体は表示しない）
```

> `None` や Substring のエラーが出たら、`--query` 以降（`--query "AuthenticationResult.IdToken" --output text`）を外して実行し、表示された内容（`ChallengeName` やエラー名）を「よくあるエラー」で探してください。
>
> ID トークンは、有効期限（1 時間）まで本人として API を呼べる通行証です。画面共有や資料に載せないでください。

### 6-6. ID トークンを付けて登録すると 201 になる

`Authorization` ヘッダーに、ID トークンをそのまま入れます（この教材の画面と同じく、`Bearer` は付けません）。

```powershell
Invoke-RestMethod -Method Post -Uri "$api/" -Headers @{ Authorization = $token } -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

- 結果に `message`（登録が完了しました）と `user` が出れば成功です（201）。
- 2 回目は 409（この ID はすでに登録されています）になります。もう一度試すときは、Session4 の管理画面か DynamoDB の画面で会員を削除してください。

### 6-7. 他人の ID で登録しようとすると 403 になる

ログインしたのは `member-0001` なのに、本文の `id` を別の値にして送ります。

```powershell
$other = @{ id = "someone-9999"; name = "鈴木愛子"; email = $email; age = 30; address = "東京都千代田区1-1"; tel = "09012345678" } | ConvertTo-Json
try {
    Invoke-RestMethod -Method Post -Uri "$api/" -Headers @{ Authorization = $token } -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($other))
} catch {
    [int]$_.Exception.Response.StatusCode   # 403
    $_.ErrorDetails.Message                 # ログインした本人の ID・メールアドレスで登録してください
}
```

> 日本語が文字化けして見えるときは、PowerShell の表示の問題のことが多いです（Session3 の 3-8）。番号（403）で判断してください。

### 確認ポイント

- [ ] トークンなしの `POST /` が 401 になる
- [ ] `sign-up` → メールの確認コード → `confirm-sign-up` → `initiate-auth` で ID トークンを受け取れた
- [ ] ID トークン付きの `POST /` が 201 になる
- [ ] 他人の ID では 403「ログインした本人の ID・メールアドレスで登録してください」になる

## 7. 画面で通す（サインアップから登録まで）

### 7-1. `config.js` にクライアント ID を設定する

`Session1/config.js` の `window.COGNITO_CLIENT_ID` に、2 で控えたクライアント ID を設定します。`window.COGNITO_REGION` は `ap-northeast-1` のままです。ほかの値（API の URL など）はそのままです。Session3・4 で設定した `API_ENDPOINT` と `ADMIN_API_ENDPOINT` を消したり、上書きしたりしないでください。

```javascript
window.COGNITO_REGION = "ap-northeast-1";
window.COGNITO_CLIENT_ID = "1a2b3c4d5e6f7g8h9i0j1k2l3m";
```

> `COGNITO_CLIENT_ID` が空の間は、画面は Session1〜4 と同じ動き（ログインなしの登録フォームだけ）になります。値を入れると、サインアップ・確認コード・ログインの画面が出ます。

### 7-2. 会員向けサイトを更新する

1. Session1 の **会員向けサイトの S3 バケット** を開き、次の 4 ファイルをバケット直下にアップロードして置き換える（`admin.html` と `admin.js` は、ここには置きません）
   - `config.js`
   - `app.js`
   - `index.html`
   - `styles.css`
2. Amplify の `site-<名前>` アプリを開き、ブランチ `dev` の **更新をデプロイ** を実行する（[Session1 の 3-4](../Session1/README.md)）
3. デプロイが終わったら、ブラウザーでサイトを開き直す（画面が変わらないときは再読み込みする）

### 7-3. ブラウザーで通す

6 で使った `member-0001` とは別のユーザID（例: `member-0002`）で試します。

1. ページの **新規会員募集** の欄に、サインアップの画面が出ることを確かめる
2. ユーザID・メールアドレス・パスワードを入れて **サインアップ** を押す
3. 「メールに確認コードを送りました。コードを入力してください。」と出たら、メールに届いた確認コードを入れて **確認する** を押す
4. 「確認が完了しました。ログインしてください。」と出たら、パスワードを入れて **ログイン** を押す
5. 会員情報の登録フォームが出る。**ユーザID** と **メールアドレス** には、ログインした人の値が入っていて、書き換えられない
6. 名前・年齢・住所・電話番号を入れて **登録** を押す。「会員登録しました。」と出れば成功です
7. Session4 の管理画面か DynamoDB の画面で、`member-0002` が登録されたことを確かめる（管理画面は、5-B を始めるまでは今までどおり使えます）

### 確認ポイント

- [ ] `config.js` の `COGNITO_CLIENT_ID` を設定し、4 つのファイルを会員向けサイトのバケットに置き換えて、更新をデプロイした
- [ ] 画面で、サインアップ → 確認コード → ログイン → 登録 まで通せた
- [ ] 登録フォームのユーザID とメールアドレスが、ログインした人の値で書き換えられない

---

## 5-B. 管理者だけが管理 API を使えるようにする

## 1. `admins` グループと管理者ユーザーを作る

### 1-1. 管理者ユーザーを作る

管理者も、会員と同じユーザープールのユーザーです。5-A と同じ方法（7 の画面、または 6 の `sign-up` と `confirm-sign-up`）で、管理者用のユーザーを 1 人作ります。

| 項目 | 例 |
|---|---|
| ユーザID | `admin-0001` |
| メールアドレス | 自分のメールアドレス（会員と同じアドレスでも構いません） |

> **ポイント**: サインアップで作ると、パスワードは自分で決めたものがそのまま使えます。Cognito の画面の **ユーザーを作成** で作ることもできますが、その場合のパスワードは「仮のパスワード」になり、初回のログインでパスワードの変更（`NEW_PASSWORD_REQUIRED`）を求められます。この教材の画面はパスワードの変更に対応していないので、画面で作った場合は「よくあるエラー」の `NEW_PASSWORD_REQUIRED` の対処を行ってください。

### 1-2. `admins` グループを作り、管理者を入れる

1. Cognito → `users-pool-<名前>`（名前が違う場合は、控えたユーザープール ID で探す）→ **グループ**（Groups）→ **グループを作成** をクリックする
2. グループ名に `admins` と入力して作成する（ほかの項目は空のままで構いません）
3. 作った `admins` を開き、**ユーザーをグループに追加** で `admin-0001` を追加する

> グループ名は、Lambda のコード（`ADMIN_GROUP = "admins"`）と同じ **`admins`**（小文字、最後に `s`）にします。
>
> グループに入ったことは、**グループに入れた後にログインして受け取ったトークン** に書かれます。入れる前に受け取ったトークンは `cognito:groups` がないままなので、ログインし直してください。

## 2. 管理 API に JWT オーソライザーを付ける

オーソライザーは API ごとに作ります。5-A の 3 と同じ値で、管理 API にも作ります。

1. **API Gateway** → `users-admin-api-<名前>` → **認可**（Authorization）を開く
2. **`GET /users`** を選び、**オーソライザーを作成してアタッチ** で次のとおり作成する

   | 項目 | 入力する値 |
   |---|---|
   | オーソライザーのタイプ | **JWT** |
   | 名前 | `cognito-<名前>` |
   | ID ソース | `$request.header.Authorization` |
   | 発行者 URL | `https://cognito-idp.ap-northeast-1.amazonaws.com/<ユーザープールID>`（5-A の 3 と同じ） |
   | 対象者 | 5-A の 2 で控えた **クライアント ID**（会員と同じクライアント） |

3. 残りの 3 つのルートにも、作ったオーソライザー（`cognito-<名前>`）を選んで **アタッチ** する

   | メソッド | パス |
   |---|---|
   | GET | `/users` |
   | GET | `/users/{id}` |
   | PUT | `/users/{id}` |
   | DELETE | `/users/{id}` |

4. 4 つのルートすべてに `JWT` のオーソライザーが付いたことを確かめる。**1 つでも付け忘れると、そのルートはログインなしで呼べてしまいます**

## 3. 管理 API の CORS に `authorization` を足す

1. **API Gateway** → `users-admin-api-<名前>` → **CORS** を開き、編集する
2. **許可されたヘッダー** に `authorization` を追加する。ほかの値は Session4 の 6 のまま変えない

   | 項目 | 設定値 |
   |---|---|
   | 許可されたオリジン | 管理画面用 Amplify アプリのオリジン（`https://dev.<アプリID>.amplifyapp.com`。Session4 のまま） |
   | 許可されたメソッド | `GET`, `PUT`, `DELETE`, `OPTIONS`（Session4 のまま） |
   | 許可されたヘッダー | `content-type`, **`authorization`** |
   | 認証情報 | 無効（Session4 のまま） |

3. 保存する

## 4. 管理 API の Lambda を貼り替える

1. **Lambda** → `users-admin-function-<名前>` を開く
2. **コード** タブの `lambda_function.py` の中身をすべて削除し、`Session5/admin_lambda_function.py` の内容を貼り付ける（Lambda 側のファイル名は `lambda_function.py` のまま。ハンドラーも `lambda_function.lambda_handler` のまま）
3. **Deploy（デプロイ）** をクリックする
4. **設定** タブ → **環境変数** で、`TABLE_NAME` が `users-table-<名前>` のまま残っていることを確かめる

> **環境変数 `TABLE_NAME` は、引き続き必要です**: Session4 のコードは、`TABLE_NAME` がないと起動時に `KeyError` になりました。Session5 のコードは、`TABLE_NAME` がないと `users` という名前のテーブルを探します。そのため、環境変数を消すと、エラーの出方が変わり（`ResourceNotFoundException` など）、原因が分かりにくくなります。Session4 で設定した `TABLE_NAME` = `users-table-<名前>` は、消さずにそのまま使ってください。

Session4 のコードとの違いは、`require_admin` が加わったことだけです。

- `get_groups(claims)`: クレームの `cognito:groups` をグループ名の一覧にします。HTTP API はこのクレームを `[admins]` のような文字列で渡すので、その形にも対応しています。
- `require_admin(event)`: クレームがあるとき、`admins` が含まれているかを確かめ、なければ 403「管理者のみ利用できます」を返します。どのルートの処理よりも先に確かめるので、4 つのルートすべてに同じ確認が効きます。
- クレームがないときは確認を省くので、Session4 のテストイベントは今までどおり動きます。

## 5. PowerShell で確かめる

5-A の 6 と同じ PowerShell の画面で続けます（閉じた場合は 6-1 の変数を入れ直します）。

```powershell
$adminApi = "https://yyyyyyyyyy.execute-api.ap-northeast-1.amazonaws.com/dev"   # Session4 で控えた管理 API の URL

# ① トークンなし → 401
try { Invoke-RestMethod -Uri "$adminApi/users" } catch { [int]$_.Exception.Response.StatusCode; $_.ErrorDetails.Message }

# ② 一般の会員（member-0001）でログインし直して、そのトークン → 403「管理者のみ利用できます」
#    5-A の 6-5 のトークンは期限（1 時間）が切れていることが多いので、6-5 と同じコマンドで取り直す
$token = aws cognito-idp initiate-auth --region $region --client-id $clientId --auth-flow USER_PASSWORD_AUTH --auth-parameters "USERNAME=$user,PASSWORD=$password" --query "AuthenticationResult.IdToken" --output text
try { Invoke-RestMethod -Uri "$adminApi/users" -Headers @{ Authorization = $token } } catch { [int]$_.Exception.Response.StatusCode; $_.ErrorDetails.Message }

# ③ 管理者（admin-0001）でログインして、そのトークン → 200
$adminPassword = '<admin-0001 のパスワード>'
$adminToken = aws cognito-idp initiate-auth --region $region --client-id $clientId --auth-flow USER_PASSWORD_AUTH --auth-parameters "USERNAME=admin-0001,PASSWORD=$adminPassword" --query "AuthenticationResult.IdToken" --output text
(Invoke-RestMethod -Uri "$adminApi/users" -Headers @{ Authorization = $adminToken }).users
```

- ① は 401、② は 403、③ は登録済みの会員の一覧が出れば成功です。
- ② が 401 なら、トークンの期限切れです。6-5 をもう一度実行してください（上の ② の `$token = ...` の行と同じです）。③ が 401 なら、`$adminToken = ...` の行をもう一度実行してください。
- `$token` や `$adminToken` を取る行で `None` やエラーが出たら、`--query` 以降を外して実行し、表示された内容（`ChallengeName` やエラー名）を「よくあるエラー」で探してください。
- ③ が 403 になるときは、`admin-0001` を `admins` に入れた **後に** ログインし直したか確かめてください。

## 6. 管理画面を更新して、ログインする

1. `Session1/config.js` を確かめる（5-A の 7-1 で `COGNITO_CLIENT_ID` を設定済み。`ADMIN_API_ENDPOINT` は Session4 のまま）
2. **管理画面用の S3 バケット**（`lastname-firstname-admin`）を開き、次の 4 ファイルをバケット直下にアップロードして置き換える
   - `admin.html`
   - `admin.js`
   - `config.js`
   - `styles.css`
3. Amplify の `admin-<名前>` アプリを開き、ブランチ `dev` の **更新をデプロイ** を実行する
4. ブラウザーで管理画面（`https://dev.<アプリID>.amplifyapp.com/admin.html`）を開く。**管理者ログイン** の欄が出る
5. `admin-0001` でログインし、**会員一覧を取得** を押す。会員の一覧が出れば成功です。検索・更新・削除も Session4 と同じように使えます
6. **ログアウト** を押し、今度は一般の会員（`member-0001` など）でログインして **会員一覧を取得** を押す。「取得に失敗しました: 管理者のみ利用できます」と出れば正しい動きです

### 確認ポイント

- [ ] `admins` グループがあり、`admin-0001` だけが入っている
- [ ] 管理 API の 4 つのルートすべてに JWT オーソライザーが付いている
- [ ] 管理 API の CORS の許可ヘッダーに `authorization` がある
- [ ] Lambda `users-admin-function-<名前>` を貼り替え、環境変数 `TABLE_NAME` が残っている
- [ ] PowerShell で、トークンなし 401、一般の会員 403、管理者 200 になる
- [ ] 管理画面で、管理者はログインして一覧を取得でき、一般の会員は「管理者のみ利用できます」になる

---

## Lambda 単体でテストする（任意）

Lambda の画面の **テスト** タブでも、本人確認と管理者確認を確かめられます。`Session5/test-events/` のイベントには、JWT オーソライザーが Lambda に渡すクレーム（`requestContext.authorizer.jwt.claims`）を、手で書き入れてあります。

| ファイル | 使う Lambda | クレーム | 期待する結果 |
|---|---|---|---|
| `create-user-with-claims.json` | `users-function-<名前>` | `cognito:username` = `sample-0001`、`email` = `sample@example.com`。本文も同じ値 | 201（すでに `sample-0001` があれば 409） |
| `create-user-other-id.json` | `users-function-<名前>` | 上と同じ。本文の `id` だけ `sample-9999` | 403「ログインした本人の ID・メールアドレスで登録してください」 |
| `list-users-admin.json` | `users-admin-function-<名前>` | `cognito:groups` = `[admins]` | 200 |
| `list-users-member.json` | `users-admin-function-<名前>` | `cognito:groups` = `[members]` | 403「管理者のみ利用できます」 |

- 会員登録の 2 つのイベント（`create-user-with-claims.json`、`create-user-other-id.json`）には、クレーム（`requestContext.authorizer.jwt.claims`）だけが入っています。トークンの確認は API Gateway のオーソライザーが行うので、Lambda 単体のテストでは `Authorization` ヘッダーも ID トークンも要りません。
- 本物の呼び出し（PowerShell や画面）では、5-A の 6-6 のとおり、ID トークンを `Bearer` を付けずにそのまま `Authorization` ヘッダーに入れます。
- Lambda の画面のテストは API Gateway を通らないので、JWT オーソライザーは働きません。401 はここでは確かめられません（5-A の 6 で確かめます）。
- クレームのないイベントでは確認を省くので、[Session2](../Session2/README.md) の `test-events/create-user.json` と、[Session4](../Session4/README.md) の `test-events/` のイベントは、今までどおり使えます。
- `create-user-with-claims.json` で登録した `sample-0001` は、不要なら管理画面で削除してください。

---

## よくあるエラー

| 症状・エラー | 原因 | 対処 |
|---|---|---|
| 401 `{"message":"Unauthorized"}` | トークンがない、期限切れ、または発行者 URL・対象者が合っていない | `Authorization` ヘッダーを付けたか確かめる。オーソライザーの発行者 URL（`https://cognito-idp.ap-northeast-1.amazonaws.com/<ユーザープールID>`、末尾 `/` なし）と、対象者（クライアント ID）を見直す。ログインし直してトークンを取り直す |
| 画面で「ログインの有効期限が切れました。もう一度ログインしてください。」 | API が 401 を返した。ID トークンの期限（1 時間）切れが多い | もう一度ログインする。すぐに出るときは、上の 401 と同じくオーソライザーの設定を見直す |
| 403「ログインした本人の ID・メールアドレスで登録してください」 | 本文の `id`・`email` が、トークンの `cognito:username`・`email` と違う | ログインした人の ID とメールアドレスで登録する。画面では自動で入るので、PowerShell の本文を見直す。サインイン識別子にメールアドレスだけを選んでいると、ユーザー名が自動の値になり、会員 ID と合わない（ユーザー名を選んで、ユーザープールを作り直す） |
| 403「ログインした本人の ID・メールアドレスで登録してください」（アクセストークンを送った場合） | アクセストークンもオーソライザーは通るが、`cognito:username`・`email` のクレームがない（ユーザー名は `username`）ため、本人確認で一致しない | ID トークン（`IdToken`）を `Authorization` ヘッダーに入れる |
| 403「管理者のみ利用できます」 | ログインした人が `admins` グループに入っていない | `admins` に入れる（グループ名のつづりも確かめる）。入れた後に **ログインし直す** |
| `UsernameExistsException`（このユーザIDはすでに使われています） | 同じユーザID がすでにある（確認前のユーザーも含む） | 別のユーザID にする。確認コードの入力がまだなら、「確認コードを入力する」から確認する |
| `CodeMismatchException`（確認コードが正しくありません） | 確認コードの入力違い | メールのコードを入れ直す。ユーザID も合っているか確かめる |
| `ExpiredCodeException`（確認コードの有効期限が切れています） | コードの期限切れ、または古いコードを入力した | コードを送り直す（`aws cognito-idp resend-confirmation-code --region $region --client-id $clientId --username <ユーザID>`）。または Cognito の画面でそのユーザーを削除してから、もう一度サインアップする（同じユーザID でサインアップし直すと `UsernameExistsException` になるため） |
| `InvalidPasswordException`（パスワードが条件を満たしていません） | パスワードポリシーに合わない | 8 文字以上で、大文字・小文字・数字・記号を含める |
| `NotAuthorizedException`（ユーザIDまたはパスワードが正しくありません） | ユーザID かパスワードの間違い | 入れ直す。パスワードは大文字・小文字を区別します |
| `UserNotConfirmedException`（メールアドレスの確認が済んでいません） | 確認コードの入力がまだ | 確認コードを入力する（5-A の 6-4、画面では「確認コードを入力する」） |
| `NEW_PASSWORD_REQUIRED`（画面に「追加の認証（NEW_PASSWORD_REQUIRED）が必要ですが、この画面では対応していません。」、CLI では `ChallengeName` が返る） | Cognito の画面の **ユーザーを作成** で作ったため、パスワードが仮のまま | そのユーザーを削除して、サインアップで作り直す（5-B の 1-1）。AWS のアクセスキーを設定済みなら、`aws cognito-idp admin-set-user-password --region ap-northeast-1 --user-pool-id <ユーザープールID> --username <ユーザID> --password '<新しいパスワード>' --permanent` で、パスワードを確定させてもよい |
| `InvalidParameterException`（USER_PASSWORD_AUTH flow not enabled for this client など） | アプリクライアントで `ALLOW_USER_PASSWORD_AUTH` が有効になっていない | 5-A の 2 の認証フローで `ALLOW_USER_PASSWORD_AUTH` にチェックを入れて保存する |
| 確認コードのメールが届かない | 迷惑メールに入った、またはメール送信の上限（1 日約 50 通）に達した | 迷惑メールのフォルダを見る。上限のときは翌日まで待つ。急ぐときは 5-A の 6-4 の「代わりの方法」で確認する |
| 画面で「登録に失敗しました: Failed to fetch」「取得に失敗しました: Failed to fetch」 | CORS で `authorization` ヘッダーを許可していないため、プリフライトで止まった | 会員 API（5-A の 4）・管理 API（5-B の 3）の許可ヘッダーに `authorization` を足す。`config.js` の URL も確かめる |
| 画面にサインアップ・ログインが出ず、登録すると「登録に失敗しました: Unauthorized」 | `config.js` の `COGNITO_CLIENT_ID` が空（Session1〜4 と同じ動き）か、新しい `config.js` がサイトに反映されていない | 5-A の 7-1 で設定し、S3 に置き換えて Amplify で **更新をデプロイ** してから、再読み込みする |
| 管理画面にログイン欄が出ず、「取得に失敗しました: Unauthorized」 | 管理画面用のバケットの `config.js` が古い | 5-B の 6 で、`config.js` を管理画面用のバケットにも置き換えて、`admin-<名前>` で **更新をデプロイ** する |
| 500「サーバー内部でエラーが発生しました」 | Lambda の内部エラー（テーブル名の間違いなど） | Lambda の CloudWatch Logs を見る。環境変数 `TABLE_NAME` が `users-table-<名前>` か確かめる |

---

## 片付け

Cognito のユーザープールは、少人数・少回数の利用なら無料の範囲に収まることが多いですが、会員の個人情報（メールアドレス）を持っているので、使い終わったら削除してください。

**削除するのは、すべての Session（Session6・7 で会員向けサイトを使う場合も含む）が終わってから** です。ユーザープールを先に削除すると、ログインできなくなり、会員登録（`POST /`）が 401 で失敗します。Session3・4 の片付けと同じ時期に、まとめて行ってください。

次の順番で行います。

1. **オーソライザーを外す**: API Gateway の `users-api-<名前>`・`users-admin-api-<名前>` で、各ルートからオーソライザーを外し、オーソライザーを削除する
   - すぐに Session3・Session4 の片付けで **API ごと削除する場合は、この手順は省略できます**（オーソライザーは API と一緒に消えます）
   - API を残す場合、オーソライザーを外すと、その API はまたログインなしで呼べる状態に戻ります。外したら、早めに API を削除してください
2. **ユーザープールを削除する**（すべての Session が終わってから）: Cognito → `users-pool-<名前>`（名前が違う場合は、控えたユーザープール ID で探す）を選び、**削除** する。ユーザー・グループ（`admins`）・アプリクライアントも一緒に消えます
   - 削除保護（Deletion protection）が有効で削除できないときは、ユーザープールの設定で削除保護を無効にしてから削除する
   - ドメインがあるため削除できないと表示されたときは、先にドメインを削除する
3. 管理 API・管理画面・Lambda は [Session4 の片付け](../Session4/README.md)、会員 API・会員向けサイト・Lambda・DynamoDB は [Session3 の片付け](../Session3/README.md) の手順で削除する（Session3・4 の案内どおり、すべての Session が終わってから）

> オーソライザーを残したままユーザープールだけを削除すると、その API はすべて 401 になります（安全側に止まります）。続けて Session3・4 の片付けで API を削除してください。

## 注意事項

- ID トークンは、ブラウザーのメモリにだけ持ちます。画面を閉じたり、再読み込みしたりすると、もう一度ログインが必要です。
- トークンの更新（リフレッシュトークン）は扱いません。期限（1 時間）が切れたら、ログインし直します。
- クライアント ID は公開してよい値です。**クライアントシークレット・AWS のアクセスキー・パスワードなどの秘密は、JavaScript や `config.js` に絶対に書かないでください**。ブラウザーに送ったものは、誰でも読めます。
- 研修では、実在の個人情報を登録しないでください。

## 次へ

[Session6](../Session6/README.md) に進んでください。Amazon Bedrock で料理のおすすめを生成します。
