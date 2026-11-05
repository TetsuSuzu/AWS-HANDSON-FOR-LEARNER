# Session6 — 店リストを tool_use で読んで、回答の精度を比べる

> このセッションのコードは [gist](https://gist.github.com/TetsuSuzu/85e34b4acd299711ee18f6161205fe3f) にあります。`Session6_` で始まるファイルを開き、中身をコピーして使えます。

Session5 では、AI に何も調べさせずに料理のおすすめを答えてもらいました。Session6 では、作成者のマップ「ランチマップ」から作った **店リスト**（`shops.txt`）を、AI がツール（tool_use）で読んで答えます。同じ質問を Session5（ツールなし）と比べ、精度が上がるかを確かめます。

例の質問は「**東京駅八重洲口でおいしい食事をしたい。店名と住所も教えてください**」です。

## 構成

```text
Session1 のサイト（料理のおすすめ欄）
   │ 料理のおすすめ（Session6・ツールあり）＝ travel-search-api-<名前> の URL
   ▼
API Gateway HTTP API（travel-search-api-<名前>。URL そのものが入口で、パスは付けない）
   │
   ▼
Lambda（travel-search-function-<名前>）
   │
   ├── Amazon Bedrock（Claude Sonnet 4.6）… 店リストを読むかを判断する
   │        ▲ 店リストを受け取り、その中から回答を書く
   │
   └── shops.txt（ランチマップから作った店リスト。Lambda と同じフォルダに置く）
```

外部の検索サービスは使いません。キーも不要です。

## tool_use とは

**tool_use** は、AI が「自分では分からないことを、道具（ツール）で調べる」仕組みです。

1. 私たちは、AI に「`get_map_shops` という店リストを読むツールを使ってよい」と伝える
2. AI は質問を読み、「店リストを見よう」と判断して、ツールの使用を依頼する
3. Lambda がツールを実行し、店リストを AI に返す
4. AI は店リストの中から、質問に合う店を選んで回答を書く

AI は、店リストを「読んだ上で」答えるため、推測だけで答えるより、実在する店を挙げやすくなると期待できます。ただし、リストに無い店を作ってしまうこともあります。そのため、この Session では **最後に自分で確かめます**。

## 事前準備

- [Session1](../Session1/README.md)〜[Session5](../Session5/README.md) を完了している（Session4 の管理画面は、この Session の動作には必須ではありません）
- Session5 の Lambda 実行ロール（Bedrock の権限を付けたもの）の名前を控える
- `Session6` フォルダの `lambda_function.py` と `shops.txt` を用意する

> **店リストについて**: `shops.txt` は、作成者の Google マイマップ「ランチマップ」の店を一覧にしたものです。カテゴリ、店名、ひとことメモが入っています。住所や営業時間は入っていません。

## 1. Lambda 関数を作成する

1. AWS コンソールのリージョンを **アジアパシフィック（東京） ap-northeast-1** にする
2. **Lambda** → **関数の作成** → **一から作成** を選ぶ
3. 次の設定で作成する

   | 項目 | 値 |
   |---|---|
   | 関数名 | `travel-search-function-<名前>` |
   | ランタイム | **Python 3.12** |
   | アーキテクチャ | **x86_64** |
   | 実行ロール | **既存のロールを使用する** → Session5 の Lambda 実行ロールを選ぶ |

4. **関数の作成** をクリック

### コードと店リストを配置する

1. **コード** タブで `lambda_function.py` の内容を、`Session6/lambda_function.py` の内容で置き換える
2. `Session6/shops.txt` を、Lambda のコードと同じフォルダに置く。コンソールの「アップロード元」で **.zip ファイル** を使う場合は、`lambda_function.py` と `shops.txt` を一緒に zip にします
3. **Deploy（デプロイ）** をクリックする
4. **ランタイム設定** → **編集** → **ハンドラー** を `lambda_function.lambda_handler` にして保存する

### 環境変数を設定する

**設定** → **環境変数** → **編集** で、次を追加します。

| キー | 値 |
|---|---|
| `MODEL_ID` | `global.anthropic.claude-sonnet-4-6` |

> `MODEL_ID` は Session5 と同じ値です。モデルを変えるときは、コードを書き換えず、この値だけを変えます。

### タイムアウトを延ばす

AI の回答と店リストの読み込みを行うため、既定の時間では足りないことがあります。

1. **設定** → **一般設定** → **編集**
2. **タイムアウト** を **30 秒** にして保存する

### 確認ポイント

- [ ] ランタイムが Python 3.12、ハンドラーが `lambda_function.lambda_handler`
- [ ] 環境変数 `MODEL_ID` がある
- [ ] `shops.txt` が `lambda_function.py` と同じフォルダにある
- [ ] タイムアウトが 30 秒

## 2. テストする（Lambda 単体）

1. Lambda の画面で **テスト** タブ → **新しいイベント**
2. イベント名を `search-recommendation` にする
3. `Session6/test-event.json` の内容を貼り付けて **保存** → **テスト**
4. 実行結果の `body` に、`answer`（回答）と `sources`（参照したマップの名前）が入っていれば成功です。

> **エラーが出たら**: 実行結果と、**モニタリング** → **CloudWatch Logs** のログを確認します。
> - `KeyError: 'MODEL_ID'` → 環境変数を確認する
> - `FileNotFoundError` で `shops.txt` が見つからない → `shops.txt` が Lambda のコードと同じフォルダにあるかを確認する
> - `AccessDeniedException` → Session5 の Bedrock 権限を確認する

## 3. 検索用の HTTP API を作成する

Session5 とは別に、検索用の HTTP API を作ります。Session5 の API とは、URL を分けるためです。

1. API Gateway で **API を作成** → **HTTP API** → **構築** を選ぶ
2. **統合** で **Lambda** を選び、`travel-search-function-<名前>` を指定する。API 名は `travel-search-api-<名前>`。ペイロード形式は **2.0**
3. **ルート** で、次を入力する

   | 項目 | 値 |
   |---|---|
   | メソッド | `POST` |
   | パス | `/`（何も入力しない） |

4. **次へ** → **作成**。ステージ名は `dev`（初期値の `$default` から書き換える）、自動デプロイを有効にする
5. **CORS** で、Session1 のサイトのオリジンを許可する（`POST`、`OPTIONS`、`content-type`）
6. ステージ `dev` の URL（例: `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev`）を控える（末尾に `/` は付けない）
7. Session1 の `config.js` に、次の行を追加して S3 に再アップロードし、Amplify で **更新をデプロイ** する

   ```javascript
   window.SEARCH_API_ENDPOINT = "<控えた URL>";
   ```


## 4. 同じ質問で 2 つの回答を比べる

PowerShell で、同じ質問を 2 つの API に送ります。A は Session5 の API の URL、B は手順 3 で作った検索用の API の URL を使います（末尾に `/` は付けません）。

```powershell
$bytes = [System.Text.Encoding]::UTF8.GetBytes('{"prompt":"東京駅八重洲口でおいしい食事をしたい。店名と住所も教えてください"}')

# A: ツールなし（Session5 の API の URL）
$apiA = "<Session5 の API の URL>"
$a = Invoke-RestMethod -Method Post -Uri $apiA -ContentType "application/json; charset=utf-8" -Body $bytes
$a.answer

# B: 店リストのツールあり（Session6 の API の URL）
$apiB = "<検索用の API の URL>"
$b = Invoke-RestMethod -Method Post -Uri $apiB -ContentType "application/json; charset=utf-8" -Body $bytes
$b.answer
$b.sources
```

CORS の設定は、`Origin` ヘッダーを付けた `curl.exe` で確かめられます(PowerShell の `curl` は別のコマンドの別名なので、`curl.exe` と書きます)。

```powershell
$origin = "https://dev.<アプリID>.amplifyapp.com"
curl.exe -s -i -X OPTIONS $apiB -H "Origin: $origin" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"
```

- 応答の `access-control-allow-origin` が `$origin` と同じ値で、`access-control-allow-methods` に `POST`、`access-control-allow-headers` に `content-type` が含まれていれば設定は正しいです。
- `curl.exe` は CORS を強制しません。成功したかどうかではなく、ヘッダーの有無を読んでください。

- `A` は、AI の知識だけで答えた回答です。
- `B` は、店リストを読んだ上で答えた回答です。`sources` に、参照したマップの名前が出ます。

## 5. 精度を確かめる

B の回答に出てきた店が、`shops.txt` に本当にあるかを確かめます。次の表に、A と B の結果を書き込んでください。

| 確かめる項目 | A（ツールなし） | B（店リストあり） |
|---|---|---|
| 挙げた店は、店リストに載っているか | | |
| 店名は正しく書けているか | | |
| カテゴリ（とんかつ、カレーなど）と合っているか | | |
| 店リストに無い店を挙げていないか | | |

**精度の判断の目安**
- 店リストに無い店を挙げていたら、その店は「誤り」とします。
- 店名の誤字や、別の店と混ざっている場合も「誤り」とします。
- B が A より誤りを減らせたかを確かめます。

> **ふりかえり**: 店リストを読ませても、必ず正しくなるわけではありません。店リストに無い店を挙げる、という誤りは起きます。「情報源を示させる」「自分で照合する」の 2 つを組み合わせることが、AI を使う上で大切です。

## 片付け

ハンズオンが終わったら、次の順番で削除してください。

1. API Gateway → `travel-search-api-<名前>` を削除する
2. Lambda → `travel-search-function-<名前>` を削除する

## 次へ

Session6 はここまでです。
