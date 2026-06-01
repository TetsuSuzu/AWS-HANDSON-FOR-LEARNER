# AWS ハンズオン：会員登録 Web アプリを作ろう

## このハンズオンで作るもの

ユーザーが情報を入力して登録できる、シンプルな **会員登録 Web アプリ** を AWS 上に構築します。

```
【全体構成】

ブラウザ（Session1 の index.html）
  │
  │ 登録ボタンを押したとき（API リクエスト）
  ▼
┌───────────────────┐
│  Amazon API Gateway│  ← API の窓口（HTTP リクエストを受け付ける）
└───────────────────┘
  │
  │ Lambda を呼び出す
  ▼
┌──────────────────┐
│  AWS Lambda      │  ← サーバーレスで動く処理（Python）
└──────────────────┘
  │
  │ データを保存する
  ▼
┌──────────────────┐
│  Amazon DynamoDB │  ← NoSQL データベース（ユーザー情報を格納）
└──────────────────┘
```

## 使用するファイル

| ファイル名 | 用途 |
|---|---|
| `lambda_function.py` | Lambda 関数のコード（DynamoDB にデータを書き込む） |
| `lambda_test_event.json` | Lambda のテスト用イベント |

---

## 手順の流れ

1. IAM ロールを作成
2. DynamoDB でテーブルを作成
3. Lambda 関数を作成・テスト
4. API Gateway で REST API を作成
5. index.html の API URL を書き換えて S3 にアップロード
6. 動作確認

---

## Step 1：IAM ロールを作成する

Lambda 関数が DynamoDB と Bedrock にアクセスできるよう、IAM ロールを作成します。  
このロールは Session3 でも使い回します。

### 1-1. IAM の画面を開く

1. AWS マネジメントコンソールで検索バーに `IAM` と入力して選択
2. 左側メニューの **「ロール」** をクリック
3. **「ロールを作成」** ボタンをクリック

### 1-2. ロールを設定する

| 項目 | 値 |
|---|---|
| 信頼されたエンティティタイプ | **AWS のサービス** |
| サービスまたはユースケース | **Lambda** |

「次へ」をクリック

### 1-3. 許可ポリシーを追加する

検索ボックスで以下の 3 つのポリシーを検索してチェックを入れる：

| ポリシー名 | 用途 |
|---|---|
| `AmazonDynamoDBFullAccess` | DynamoDB へのアクセス |
| `AWSLambdaBasicExecutionRole` | Lambda の基本実行権限（CloudWatch Logs） |
| `AmazonBedrockFullAccess` | Bedrock へのアクセス（Session3 で使用） |

「次へ」をクリック

### 1-4. ロール名を設定する

| 項目 | 値 |
|---|---|
| ロール名 | <font color="red">lastname-firstname</font> |

> ※ <font color="red">lastname-firstname</font> は自分の名前に置き換えてください（例：`yamada-taro`）。

**「ロールを作成」** をクリック

---

## Step 2：DynamoDB テーブルを作成する

DynamoDB はデータを保存するデータベースです。ここで登録したユーザー情報を格納します。

### 2-1. DynamoDB の画面を開く

1. 画面上部の検索バーに `DynamoDB` と入力して選択
2. 左側メニューの **「テーブル」** をクリック
3. 右上の **「テーブルの作成」** ボタンをクリック

### 2-2. テーブルを設定する

| 項目 | 値 |
|---|---|
| テーブル名 | `users` |
| パーティションキー | `id`（型：**文字列**） |
| ソートキー | （何も入力しない） |

「テーブル設定」セクションは **「デフォルト設定」** のままでOK

**「テーブルの作成」** をクリック

> ステータスが「作成中」→「アクティブ」になれば完了です（数十秒かかります）。

---

## Step 3：Lambda 関数を作成する

Lambda はサーバーを立てずにコードを実行できるサービスです。

### 3-1. Lambda の画面を開く

1. 検索バーに `Lambda` と入力して選択
2. **「関数の作成」** ボタンをクリック

### 3-2. 関数を設定する

| 項目 | 値 |
|---|---|
| 関数名 | `users-post-function`（任意） |
| ランタイム | **Python 3.12** |
| アーキテクチャ | x86_64 |
| 実行ロール | **既存のロールを使用する** → <font color="red">lastname-firstname</font> を選択 |

> **💡 実行ロールとは？**  
> Lambda 関数が他の AWS サービス（DynamoDB・Bedrock など）にアクセスするための「権限証明書」です。  
> Lambda はデフォルトでは何もアクセスできないため、Step1 で作成したロールを割り当てることで DynamoDB へのデータ保存が可能になります。

「関数の作成」をクリック

### 3-3. コードを貼り付ける

1. 関数の詳細画面が開いたら、**「コードソース」** セクションまでスクロール
2. `lambda_function.py` の内容をすべて削除し、以下のコードをコピーして貼り付ける

```python
import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

def lambda_handler(event, context):
    required_keys = ['id', 'name', 'email', 'age', 'address', 'tel']
    item = {key: event.get(key, '') for key in required_keys}
    table.put_item(Item=item)
    return {'message': '登録が完了しました'}
```

**📝 コード解説**

| 行・処理 | 内容 |
|---|---|
| `import boto3` | AWS を Python から操作するための SDK（ライブラリ）を読み込む |
| `dynamodb.resource` / `Table('users')` | DynamoDB の `users` テーブルに接続する |
| `lambda_handler(event, context)` | API Gateway からリクエストが来たときに呼び出される関数。`event` にリクエスト内容が入る |
| `required_keys` | 登録に必要な項目名のリスト（id・name・email・age・address・tel） |
| `event.get(key, '')` | `event`（リクエスト）から各項目の値を取り出す。値がなければ空文字にする |
| `table.put_item(Item=item)` | 取り出した値を DynamoDB のテーブルに 1 件保存する |
| `return {'message': ...}` | 処理が完了したことを示すメッセージを API Gateway に返す |

3. 右上の **「Deploy」（デプロイ）** ボタンをクリック

> 「関数 users-post-function が正常に更新されました」と表示されれば OK です。

### 3-4. Lambda をテストする

1. **「テスト」** タブをクリック
2. **「新しいイベントを作成」** を選択
3. イベント名に `testEvent` と入力
4. テストイベントの JSON を以下に書き換える（`lambda_test_event.json` の内容）：

```json
{
  "id": "user123",
  "name": "山田太郎",
  "email": "taro.yamada@example.com",
  "age": "30",
  "address": "東京都千代田区",
  "tel": "090-1234-5678"
}
```

5. **「保存」** をクリック → **「テスト」** をクリック
6. 結果に `"message": "登録が完了しました"` が表示されれば成功！

> DynamoDB の `users` テーブルを確認して「項目の探索」から `user123` が登録されていれば完璧です。

---

## Step 4：API Gateway で REST API を作成する

API Gateway は、ブラウザからのリクエストを Lambda に橋渡しする役割を担います。

### 4-1. API Gateway の画面を開く

1. 検索バーに `API Gateway` と入力して選択
2. **「APIを作成」** ボタンをクリック

### 4-2. API の種類を選ぶ

**「REST API」** の **「構築」** をクリック

> 「REST API（プライベート）」ではなく「REST API」を選んでください。

### 4-3. API を作成する

| 項目 | 値 |
|---|---|
| 新しい API を作成 | **新しい API** |
| API 名 | `users-registration-api` |
| API エンドポイントタイプ | **リージョン** |

「APIを作成」をクリック

### 4-4. POST メソッドを作成する

1. 左側のリソース一覧で **`/`（ルート）** を選択
2. **「メソッドを作成」** ボタンをクリック

| 項目 | 値 |
|---|---|
| メソッドタイプ | **POST** |
| 統合タイプ | **Lambda 関数** |
| Lambda プロキシ統合 | **オフ（チェックを外す）** |
| Lambda 関数 | `users-post-function` を選択（リージョン：ap-northeast-1） |

「メソッドを作成」をクリック

> 「Lambda 関数に権限を追加しますか？」と聞かれたら **「OK」** をクリックしてください。

### 4-5. マッピングテンプレートを設定する

1. 作成した POST メソッドをクリックして詳細画面を開く
2. **「統合リクエスト」** タブをクリック → **「編集」** をクリック
3. 「マッピングテンプレート」セクションを展開 → **「マッピングテンプレートを追加」** をクリック

| 項目 | 値 |
|---|---|
| コンテンツタイプ | `application/json` |
| テンプレート本文 | `$input.json('$')` |

「保存」をクリック

> **💡 マッピングテンプレートとは？**  
> API Gateway がブラウザから受け取ったリクエストを、Lambda が扱いやすい形に変換するための「翻訳ルール」です。  
> `$input.json('$')` と書くと、リクエストのボディ（JSON）をそのまま Lambda の `event` として渡します。  
> これにより Lambda のコードでは `event["id"]` や `event["name"]` のように直接値を取り出すことができます。

### 4-6. CORS を有効にする

ブラウザから API を呼び出せるようにするため、CORS（クロスオリジンリソース共有）を設定します。

1. リソース一覧で **`/`（ルート）** を選択したまま
2. **「CORS を有効にする」** ボタンをクリック

| 項目 | 値 |
|---|---|
| Access-Control-Allow-Methods | **POST** と **OPTIONS** にチェック |
| Access-Control-Allow-Headers | `Content-Type` が含まれていることを確認 |
| Access-Control-Allow-Origin | `*` |

「保存」をクリック

### 4-7. API をデプロイする

1. **「APIをデプロイ」** ボタンをクリック

| 項目 | 値 |
|---|---|
| ステージ | **新しいステージ** |
| ステージ名 | `users-stage` |

「デプロイ」をクリック

### 4-8. エンドポイント URL をメモする

デプロイ後に表示される **「ステージの詳細」** 画面で、**「URLを呼び出す」** の URL をコピーしてメモしておきます。

```
例: https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/users-stage
```

> この URL は次のステップで index.html に貼り付けます。

---

## Step 5：index.html の API URL を書き換えて S3 にアップロードする

### 5-1. HTML ファイルの API エンドポイントを書き換える

Session1 の `index.html` をテキストエディタ（メモ帳など）で開き、以下の部分を探します：

```javascript
var registrationUrl = "https://APIドメイン名";
```

Step 4-8 でメモした URL に書き換えます：

```javascript
var registrationUrl = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/users-stage/";
```

> URL の末尾に `/` があることを確認してください。

### 5-2. S3 にアップロードする

1. Session1 で作成した S3 バケット（<font color="red">lastname-firstname</font>）を開く
2. **「アップロード」** をクリック → 書き換えた `index.html` を選択 → **「アップロード」** をクリック

---

## Step 6：動作確認

### 6-1. ウェブサイトにアクセスする

```
https://dkonfkxt9sp21.cloudfront.net/
```

### 6-2. 登録してみる

フォームに以下のような情報を入力して「登録」ボタンを押してみましょう：

| 項目 | 入力例 |
|---|---|
| ユーザID | `test001` |
| 名前 | `テスト 太郎` |
| メールアドレス | `test@example.com` |
| 年齢 | `25` |
| 住所 | `東京都渋谷区` |
| 電話番号 | `090-0000-0000` |

「登録が完了しました」というメッセージが表示されれば成功！

### 6-3. DynamoDB でデータを確認する

1. DynamoDB の画面を開く
2. 「テーブル」→「users」をクリック
3. **「項目を探索」** タブをクリック
4. 登録したデータが表示されていれば完璧です！

---

## よくあるトラブルと対処法

### エラー「登録に失敗しました」が出る

- `index.html` の `var registrationUrl` が正しい API Gateway URL になっているか確認
- URL の末尾に `/` があるか確認（例：`https://xxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/users-stage/`）
- Lambda 関数が正しくデプロイされているか確認

### フォームを送信しても何も起きない

- ブラウザの開発者ツール（F12）→「コンソール」タブでエラーを確認
- CORS の設定が正しいか API Gateway で確認
- マッピングテンプレートが設定されているか確認

---

## 完成サイト

| サイト | URL |
|---|---|
| 勉強会サイト（Session1〜3統合） | https://dkonfkxt9sp21.cloudfront.net/ |
