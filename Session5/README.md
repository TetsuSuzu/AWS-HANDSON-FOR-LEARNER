# Session5 — 検索ツールを使って、回答の精度が上がるかを確かめる

Session4 では、AI に何も調べさせずに料理のおすすめを答えてもらいました。Session5 では、同じ質問を **検索ツール（tool_use）** を使える形で AI に送り、インターネットの公開情報を取りながら答えさせます。そして、2 つの回答の精度を比べます。

例の質問は「**東京駅八重洲口でおいしい食事をしたい。店名と住所も教えてください**」です。

## 構成

```text
Session1 のサイト（料理のおすすめ欄）
   │ POST /v1/recommendations（Session4・ツールなし）
   │ POST /v1/search-recommendations（Session5・ツールあり）
   ▼
API Gateway HTTP API（Session4 で作成した travel-recommendation-api-<名前>）
   │
   ▼
Lambda（travel-search-function-<名前>）
   │
   ├── Amazon Bedrock（Claude Sonnet 4.6）… 「検索が必要か」を判断する
   │        ▲ 検索結果を受け取り、回答を書く
   │
   └── Brave Search API … 検索結果（タイトル・URL・要約）を返す
```

## tool_use とは

**tool_use** は、AI が「自分では分からないことを、道具（ツール）で調べる」仕組みです。

1. 私たちは、AI に「`web_search` という検索ツールを使ってよい」と伝える
2. AI は質問を読み、「店の住所は検索して確かめよう」と判断して、ツールの使用を依頼する（検索キーワードを決める）
3. Lambda がツールを実行し（実際に検索 API を呼ぶ）、結果を AI に返す
4. AI は検索結果を読んで、回答を書く

AI は、検索結果を「読んだ上で」答えるため、推測だけで答えるより、正確になりやすいと期待できます。ただし、検索結果が古い、間違っている、ということもあります。そのため、この Session では **最後に自分で確かめます**。

## 事前準備

- [Session1](../Session1/README.md)〜[Session4](../Session4/README.md) を完了している
- Session4 の Lambda 実行ロール（Bedrock の権限を付けたもの）の名前を控える

### 検索 API のキーを受け取る

このハンズオンで使う Brave Search API のキーは、講師が用意して配布します。受講者が自分でアカウントを作る必要はありません。

> **注意**
> - 配布された API キーは、他人に教えたり、Session1 のサイトや GitHub に書いたりしないでください。このハンズオンでは、Lambda の環境変数に入れます。
> - 検索結果の利用は、Brave Search API の利用規約に従ってください。
> - 食べログなどのサイトを、プログラムで直接読み取るのは、この Session では行いません。サイトの利用規約で禁止されている場合があるためです。検索 API が返した結果（タイトル・URL・要約）だけを使います。

## 1. Lambda 関数を作成する

1. AWS コンソールのリージョンを **アジアパシフィック（東京） ap-northeast-1** にする
2. **Lambda** → **関数の作成** → **一から作成** を選ぶ
3. 次の設定で作成する

   | 項目 | 値 |
   |---|---|
   | 関数名 | `travel-search-function-<名前>` |
   | ランタイム | **Python 3.12** |
   | アーキテクチャ | **x86_64** |
   | 実行ロール | **既存のロールを使用する** → Session4 の Lambda 実行ロールを選ぶ |

4. **関数の作成** をクリック

### コードを貼り付ける

1. **コード** タブで `lambda_function.py` を開く
2. `Session5/lambda_function.py` の内容をすべてコピーし、エディターの内容を置き換える
3. **Deploy（デプロイ）** をクリックする
4. **ランタイム設定** → **編集** → **ハンドラー** を `lambda_function.handler` にして保存する

### 環境変数を設定する

**設定** → **環境変数** → **編集** で、次の 2 つを追加します。

| キー | 値 |
|---|---|
| `MODEL_ID` | `global.anthropic.claude-sonnet-4-6` |
| `BRAVE_API_KEY` | 講師から配布された API キー |

> `MODEL_ID` は Session4 と同じ値です。環境変数にしているので、モデルを変えるときはコードを書き換えず、この値だけを変えます。

### タイムアウトを延ばす

AI の回答と検索を行うため、Lambda の既定の時間では足りないことがあります。

1. **設定** → **一般設定** → **編集**
2. **タイムアウト** を **30 秒** にして保存する

### 確認ポイント

- [ ] ランタイムが Python 3.12、ハンドラーが `lambda_function.handler`
- [ ] 環境変数に `MODEL_ID` と `BRAVE_API_KEY` がある
- [ ] タイムアウトが 30 秒

## 2. テストする（Lambda 単体）

1. Lambda の画面で **テスト** タブ → **新しいイベント**
2. イベント名を `search-recommendation` にする
3. `Session5/test-event.json` の内容を貼り付けて **保存** → **テスト**
4. 実行結果の `body` に、`answer`（回答）と `sources`（参照した URL の一覧）が入っていれば成功です。

> **エラーが出たら**: 実行結果と、**モニタリング** → **CloudWatch Logs** のログを確認します。
> - `KeyError: 'BRAVE_API_KEY'` や `KeyError: 'MODEL_ID'` → 環境変数を確認する
> - `AccessDeniedException` → Session4 の Bedrock 権限を確認する
> - 検索に失敗する場合は、API キーが正しいか、プランが有効かを確認する

## 3. API にルートを追加する

Session4 で作成した `travel-recommendation-api-<名前>` に、新しいルートを追加します。

1. API Gateway で `travel-recommendation-api-<名前>` を開く
2. **ルート** → **ルートを作成** で、次を入力する

   | 項目 | 値 |
   |---|---|
   | メソッド | `POST` |
   | パス | `/v1/search-recommendations` |

3. 作成したルートの **統合** に、`travel-search-function-<名前>` を選んで接続する
4. `$default` ステージで自動デプロイが有効であることを確認する

> CORS の設定は Session4 のままで使えます（`POST` と `content-type` を許可済みのはずです）。

## 4. 同じ質問で 2 つの回答を比べる

PowerShell で、同じ質問を 2 つの API に送ります。`<API の URL>` は Session4 の API の URL に置き換えてください（末尾に `/` は付けません）。

```powershell
$api = "<API の URL>"
$body = '{"prompt":"東京駅八重洲口でおいしい食事をしたい。店名と住所も教えてください"}'
$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)

# A: ツールなし（Session4）
$a = Invoke-RestMethod -Method Post -Uri "$api/v1/recommendations" -ContentType "application/json; charset=utf-8" -Body $bytes
$a.answer

# B: 検索ツールあり（Session5）
$b = Invoke-RestMethod -Method Post -Uri "$api/v1/search-recommendations" -ContentType "application/json; charset=utf-8" -Body $bytes
$b.answer
$b.sources | Format-Table title, url
```

- `A` は、AI の知識だけで答えた回答です。
- `B` は、検索結果を使った回答です。`sources` に、参照した URL が出ます。

## 5. 精度を確かめる

B の `sources` の URL を実際に開き、回答の内容を一つずつ照合します。次の表に、A と B の結果を書き込んでください。

| 確かめる項目 | A（ツールなし） | B（検索あり） | 参照 URL で確認できたか |
|---|---|---|---|
| 店名は実在するか | | | |
| 住所は正しいか | | | |
| 八重洲口から徒歩で行けるか | | | |
| 営業時間・定休日は書かれているか | | | |
| 書かれている情報の出どころ（URL）があるか | | | |

**精度の判断の目安**
- 実在しない店名や、違う場所の住所があれば、その項目は「誤り」とします。
- 参照 URL で確認できない情報は、「根拠なし」とします。
- B が A より誤りや根拠なしを減らせたかを確かめます。

> **ふりかえり**: 検索を使っても、必ず正しくなるわけではありません。検索結果そのものが古い、または不正確なこともあります。「URL を示させる」「自分で確認する」という 2 つを組み合わせることが、AI を使う上で大切です。

## 片付け

ハンズオンが終わったら、次の順番で削除してください。

1. API Gateway → `travel-recommendation-api-<名前>` の **ルート** から `POST /v1/search-recommendations` を削除する
2. Lambda → `travel-search-function-<名前>` を削除する
3. 配布された API キーは、ハンズオン終了後に講師が無効化します。受講者の画面からキーを消してください（Lambda の環境変数から削除）

## 次へ

Session5 はここまでです。
