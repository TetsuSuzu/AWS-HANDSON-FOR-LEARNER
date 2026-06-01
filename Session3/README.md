# AWS ハンズオン：AI連携（Lambda + API Gateway + Bedrock）

## このハンズオンで作るもの

ユーザーが入力した食事の好みをもとに、生成 AI（Amazon Bedrock）が旅先のおすすめ料理を提案する機能を AWS 上に構築します。

```
【全体構成】

ブラウザ（Session1 の index.html）
  │
  │ テキストを入力してボタンを押したとき
  ▼
┌───────────────────┐
│  Amazon API Gateway│  ← AI へのリクエストを受け付ける
└───────────────────┘
  │
  │ Lambda を呼び出す
  ▼
┌──────────────────┐
│  AWS Lambda      │  ← Amazon Bedrock を呼び出す処理（Python）
└──────────────────┘
  │
  │ AI に問い合わせる
  ▼
┌──────────────────┐
│ Amazon Bedrock   │  ← 生成 AI（Claude Sonnet 4.6）が回答を生成
└──────────────────┘
```

## 使用するファイル

| ファイル名 | 用途 |
|---|---|
| `lambda.txt` | Lambda 関数のコード（Bedrock を呼び出す） |

---

## 手順の流れ

1. Lambda 関数を作成・テスト
2. API Gateway で REST API を作成
3. index.html の API URL を書き換えて S3 にアップロード
4. 動作確認

---

## Step 1：Lambda 関数を作成する

Lambda はサーバーを立てずにコードを実行できるサービスです。ここでは Amazon Bedrock の AI モデルを呼び出す処理を実装します。

### 1-1. Lambda の画面を開く

1. AWS マネジメントコンソールで検索バーに `Lambda` と入力して選択
2. **「関数の作成」** ボタンをクリック

### 1-2. 関数を設定する

| 項目 | 値 |
|---|---|
| 関数名 | <font color="red">lastname-firstname-b</font> |
| ランタイム | **Python 3.12** |
| 実行ロール | **既存のロールを使用する** → <font color="red">lastname-firstname</font> を選択 |

> ※ <font color="red">lastname-firstname-b</font> は自分の名前に置き換えてください（例：`yamada-taro-b`）。

「関数の作成」をクリック

> **💡 実行ロールとは？**  
> Lambda 関数が他の AWS サービスにアクセスするための「権限証明書」です。  
> Session2 で作成した <font color="red">lastname-firstname</font> ロールには `AmazonBedrockFullAccess` が付与済みのため、このロールを割り当てるだけで Bedrock の AI モデルを呼び出せるようになります。

### 1-3. コードを貼り付ける

1. 関数の詳細画面が開いたら、**「コードソース」** セクションまでスクロール
2. `lambda_function.py` の内容をすべて削除し、`lambda.txt` の内容をコピーして貼り付ける

```python
import json
import boto3

bedrock_runtime_client = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

def lambda_handler(event, context):
    user_prompt = event["key1"]
    model_id = 'global.anthropic.claude-sonnet-4-6'
    system_prompt = "あなたは生成AIのエージェントです。ユーザからの質問に丁寧に回答してください。"
    max_tokens = 1000
    temperature = 0

    user_message = {
        "role": "user",
        "content": user_prompt
    }
    body = json.dumps(
        {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [user_message],
        "temperature": temperature
        }
    )

    response = bedrock_runtime_client.invoke_model(body=body, modelId=model_id)
    response_json = json.loads(response.get('body').read())
    return response_json['content'][0]['text']
```

**📝 コード解説**

| 行・処理 | 内容 |
|---|---|
| `import boto3` / `import json` | AWS SDK と JSON 変換ライブラリを読み込む |
| `boto3.client('bedrock-runtime', region_name='us-east-1')` | Bedrock を呼び出すためのクライアントを作成する。Bedrock のモデルは `us-east-1`（バージニア北部）で使用する |
| `lambda_handler(event, context)` | API Gateway からリクエストが来たときに呼び出される関数 |
| `event["key1"]` | フロントエンドから送られてきたユーザーの入力テキストを取り出す |
| `model_id` | 使用する AI モデルの ID（Claude Sonnet 4.6 の推論プロファイル） |
| `system_prompt` | AI に対する役割の指示文。ここを変えると AI の振る舞いが変わる |
| `max_tokens` | AI が返す回答の最大文字数（トークン数）の上限 |
| `temperature` | AI の回答のランダム性（0 = 毎回同じ回答、1 に近いほどバリエーションが増える） |
| `bedrock_runtime_client.invoke_model(...)` | 設定した内容で Bedrock の AI モデルを呼び出す |
| `response_json['content'][0]['text']` | AI からの回答テキストを取り出してそのまま返す |

3. 右上の **「Deploy」（デプロイ）** ボタンをクリック

> 「関数が正常に更新されました」と表示されれば OK です。

### 1-4. タイムアウトを延長する

1. **「設定」** タブ → **「一般設定」** → **「編集」** をクリック
2. タイムアウトを **1 分** に変更して **「保存」** をクリック

> Bedrock の応答に時間がかかる場合があるため、デフォルト（3 秒）から延長します。

### 1-5. Lambda をテストする

1. **「テスト」** タブをクリック
2. **「新しいイベントを作成」** を選択
3. イベント名に `testEvent` と入力
4. テストイベントの JSON を以下に書き換える：

```json
{
    "key1": "長野でおすすめの料理を教えてください"
}
```

5. **「保存」** をクリック → **「テスト」** をクリック
6. 結果に AI からの回答テキストが表示されれば成功！

---

## Step 2：API Gateway で REST API を作成する

API Gateway は、ブラウザからのリクエストを Lambda に橋渡しする役割を担います。

### 2-1. API Gateway の画面を開く

1. 検索バーに `API Gateway` と入力して選択
2. **「APIを作成」** ボタンをクリック

### 2-2. API の種類を選ぶ

**「REST API」** の **「構築」** をクリック

> 「REST API（プライベート）」ではなく「REST API」を選んでください。

### 2-3. API を作成する

| 項目 | 値 |
|---|---|
| 新しい API を作成 | **新しい API** |
| API 名 | <font color="red">lastname-firstname-b</font> |
| API エンドポイントタイプ | **リージョン** |

「APIを作成」をクリック

### 2-4. リソースを作成する

1. **「リソースを作成」** をクリック
2. リソース名に <font color="red">lastname-firstname-b</font> と入力
3. **「リソースを作成」** をクリック

### 2-5. POST メソッドを作成する

1. 作成したリソースを選択 → **「メソッドを作成」** をクリック

| 項目 | 値 |
|---|---|
| メソッドタイプ | **POST** |
| 統合タイプ | **Lambda 関数** |
| Lambda プロキシ統合 | **オフ（チェックを外す）** |
| Lambda 関数 | <font color="red">lastname-firstname-b</font> を選択（リージョン：ap-northeast-1） |

「メソッドを作成」をクリック

> 「Lambda 関数に権限を追加しますか？」と聞かれたら **「OK」** をクリックしてください。

### 2-6. マッピングテンプレートを設定する

1. 作成した POST メソッドをクリックして詳細画面を開く
2. **「統合リクエスト」** タブをクリック → **「編集」** をクリック
3. 「マッピングテンプレート」セクションを展開 → **「マッピングテンプレートを追加」** をクリック

| 項目 | 値 |
|---|---|
| コンテンツタイプ | `application/json` |
| テンプレート本文 | `{"key1":$input.json('$.key1')}` |

「保存」をクリック

> **💡 マッピングテンプレートとは？**  
> API Gateway がブラウザから受け取ったリクエストを、Lambda が扱いやすい形に変換するための「翻訳ルール」です。  
> フロントエンドは `{"key1": "長野でおすすめの料理は？"}` という形で送信しており、`$input.json('$.key1')` でその値だけを取り出して Lambda に渡します。  
> これにより Lambda のコードでは `event["key1"]` でユーザーの入力テキストを直接受け取ることができます。

### 2-7. CORS を有効にする

ブラウザから API を呼び出せるようにするため、CORS（クロスオリジンリソース共有）を設定します。

1. リソースを選択 → **「CORS を有効にする」** ボタンをクリック

| 項目 | 値 |
|---|---|
| Access-Control-Allow-Methods | **POST** と **OPTIONS** にチェック |
| Access-Control-Allow-Headers | `Content-Type` が含まれていることを確認 |
| Access-Control-Allow-Origin | `*` |

「保存」をクリック

### 2-8. API をデプロイする

1. **「APIをデプロイ」** ボタンをクリック

| 項目 | 値 |
|---|---|
| ステージ | **新しいステージ** |
| ステージ名 | `prod` |

「デプロイ」をクリック

### 2-9. エンドポイント URL をメモする

デプロイ後に表示される **「ステージの詳細」** 画面で、**「URLを呼び出す」** の URL をコピーしてメモしておきます。

```
例: https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod
```

> この URL は次のステップで index.html に貼り付けます。

---

## Step 3：index.html の API URL を書き換えて S3 にアップロードする

### 3-1. HTML ファイルの API エンドポイントを書き換える

Session1 の `index.html` をテキストエディタ（メモ帳など）で開き、以下の部分を探します：

```javascript
var bedrockUrl = "https://APIドメイン名";
```

Step 2-9 でメモした URL にリソース名を加えた URL に書き換えます：

```javascript
var bedrockUrl = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/lastname-firstname-b";
```

### 3-2. S3 にアップロードする

1. Session1 で作成した S3 バケット（<font color="red">lastname-firstname</font>）を開く
2. **「アップロード」** をクリック → 書き換えた `index.html` を選択 → **「アップロード」** をクリック

---

## Step 4：動作確認

### 4-1. ウェブサイトにアクセスする

```
https://xxxxxxxxxxxx.cloudfront.net/
```

### 4-2. AI おすすめ機能を試す

1. 「あなたの好きな食事は？」セクションにテキストを入力（例：「長野でおすすめの食事を教えて」）
2. **「おすすめを表示」** ボタンをクリック
3. AI（Bedrock）からの回答が表示されれば成功！

---

## よくあるトラブルと対処法

### AI おすすめ機能が動かない

- `index.html` の `var bedrockUrl` が正しい API Gateway URL になっているか確認
- URL の末尾にリソース名（`/prod/lastname-firstname-b`）が含まれているか確認
- Lambda 関数が正しくデプロイされているか確認

### Lambda テストでエラーが出る

- Amazon Bedrock（us-east-1）でモデルのアクセス権が付与されているか確認
- 推論プロファイル `global.anthropic.claude-sonnet-4-6` を使用しているか確認（オンデマンドモデル ID では動作しない）
- IAM ロールに `AmazonBedrockFullAccess` が付与されているか確認

### タイムアウトエラーが出る

- API Gateway のタイムアウトは最大 29 秒のため、Bedrock の応答が遅い場合はエラーになることがある
- Lambda のタイムアウトが 1 分に設定されているか確認（Step 1-4 参照）

---

## 完成サイト

| サイト | URL |
|---|---|
| 勉強会サイト（Session1〜3統合） | https://xxxxxxxxxxxx.cloudfront.net/ |
