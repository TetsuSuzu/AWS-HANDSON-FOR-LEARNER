# AWS ハンズオン：管理者用 会員情報管理アプリを作ろう

## このハンズオンで作るもの

Session2 で登録した会員情報（DynamoDB の `users` テーブル）を、管理者が **照会（GET）・更新（PUT）・削除（DELETE）** できる管理画面を AWS 上に構築します。

```
【全体構成】

ブラウザ（admin.html）
  │
  │ 一覧表示 / 照会 / 更新 / 削除
  ▼
┌───────────────────┐
│  Amazon API Gateway│  ← GET / PUT / DELETE を受け付ける
└───────────────────┘
  │
  │ Lambda を呼び出す
  ▼
┌──────────────────┐
│  AWS Lambda      │  ← 操作内容（operation）に応じて処理を分岐
└──────────────────┘
  │
  │ 参照・書き込み・削除
  ▼
┌──────────────────┐
│  Amazon DynamoDB │  ← Session2 で作成した `users` テーブル
└──────────────────┘
```

## 使用するファイル

| ファイル名 | 用途 |
|---|---|
| `lambda_function.py` | Lambda 関数のコード（GET/PUT/DELETE を1つの関数で処理） |
| `admin.html` | 管理者用の会員情報管理ページ |

---

## 手順の流れ

1. Lambda 関数を作成・テスト
2. API Gateway で REST API を作成（GET / PUT / DELETE の3メソッド）
3. admin.html の API URL を書き換えて S3 にアップロード
4. 動作確認

---

## Step 1：Lambda 関数を作成する

Session2 で作成した IAM ロール（<font color="red">lastname-firstname</font>）をそのまま使い回します。`AmazonDynamoDBFullAccess` が付与済みのため、追加の権限設定は不要です。

### 1-1. Lambda の画面を開く

1. AWS マネジメントコンソールで検索バーに `Lambda` と入力して選択
2. **「関数の作成」** ボタンをクリック

### 1-2. 関数を設定する

| 項目 | 値 |
|---|---|
| 関数名 | <font color="red">lastname-firstname-admin</font> |
| ランタイム | **Python 3.12** |
| 実行ロール | **既存のロールを使用する** → <font color="red">lastname-firstname</font> を選択 |

「関数の作成」をクリック

### 1-3. コードを貼り付ける

1. 関数の詳細画面が開いたら、**「コードソース」** セクションまでスクロール
2. `lambda_function.py` の内容をすべて削除し、以下のコードをコピーして貼り付ける

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

def lambda_handler(event, context):
    operation = event.get('operation')

    if operation == 'get_all':
        response = table.scan()
        return {'items': response.get('Items', [])}

    if operation == 'get':
        response = table.get_item(Key={'id': event['id']})
        return {'item': response.get('Item')}

    if operation == 'put':
        required_keys = ['id', 'name', 'email', 'age', 'address', 'tel']
        item = {key: event.get(key, '') for key in required_keys}
        table.put_item(Item=item)
        return {'message': '更新が完了しました'}

    if operation == 'delete':
        table.delete_item(Key={'id': event['id']})
        return {'message': '削除が完了しました'}

    return {'error': '不明な操作です'}
```

**📝 コード解説**

| 行・処理 | 内容 |
|---|---|
| `operation` | API Gateway のマッピングテンプレートが埋め込む「どの操作か」を表す値（`get_all`/`get`/`put`/`delete`） |
| `table.scan()` | テーブル内の全件を取得する（一覧表示用） |
| `table.get_item(Key={'id': ...})` | 指定した `id` の1件を取得する（照会用） |
| `table.put_item(Item=item)` | 指定した `id` の項目を上書き保存する（新規登録にも更新にも使える） |
| `table.delete_item(Key={'id': ...})` | 指定した `id` の項目を削除する |

3. 右上の **「Deploy」（デプロイ）** ボタンをクリック

---

## Step 2：API Gateway で REST API を作成する

GET・PUT・DELETE の3つのメソッドを、すべて同じルート（`/`）に対して作成します。

### 2-1. API Gateway の画面を開く

1. 検索バーに `API Gateway` と入力して選択
2. **「APIを作成」** ボタンをクリック → **「REST API」** の **「構築」** をクリック

### 2-2. API を作成する

| 項目 | 値 |
|---|---|
| 新しい API を作成 | **新しい API** |
| API 名 | <font color="red">lastname-firstname-admin</font> |
| API エンドポイントタイプ | **リージョン** |

「APIを作成」をクリック

### 2-3. GET メソッドを作成する（一覧表示・照会）

1. リソース一覧で **`/`（ルート）** を選択 → **「メソッドを作成」** をクリック

| 項目 | 値 |
|---|---|
| メソッドタイプ | **GET** |
| 統合タイプ | **Lambda 関数** |
| Lambda プロキシ統合 | **オフ（チェックを外す）** |
| Lambda 関数 | <font color="red">lastname-firstname-admin</font> を選択 |

「メソッドを作成」をクリック（「Lambda 関数に権限を追加しますか？」には **「OK」**）

2. 作成した GET メソッドをクリック → **「統合リクエスト」** タブ → **「編集」**
3. 「マッピングテンプレート」を追加：

| 項目 | 値 |
|---|---|
| コンテンツタイプ | `application/json` |
| テンプレート本文 | 下記参照 |

```velocity
#if($input.params('id') != "")
{"operation":"get","id":"$input.params('id')"}
#else
{"operation":"get_all"}
#end
```

> クエリ文字列に `id` が付いていれば1件照会、なければ一覧取得として Lambda に伝えます。

### 2-4. PUT メソッドを作成する（更新）

1. **`/`（ルート）** を選択 → **「メソッドを作成」**

| 項目 | 値 |
|---|---|
| メソッドタイプ | **PUT** |
| 統合タイプ | **Lambda 関数** |
| Lambda プロキシ統合 | **オフ** |
| Lambda 関数 | <font color="red">lastname-firstname-admin</font> |

2. マッピングテンプレートを追加：

```velocity
{"operation":"put","id":$input.json('$.id'),"name":$input.json('$.name'),"email":$input.json('$.email'),"age":$input.json('$.age'),"address":$input.json('$.address'),"tel":$input.json('$.tel')}
```

### 2-5. DELETE メソッドを作成する（削除）

1. **`/`（ルート）** を選択 → **「メソッドを作成」**

| 項目 | 値 |
|---|---|
| メソッドタイプ | **DELETE** |
| 統合タイプ | **Lambda 関数** |
| Lambda プロキシ統合 | **オフ** |
| Lambda 関数 | <font color="red">lastname-firstname-admin</font> |

2. マッピングテンプレートを追加：

```velocity
{"operation":"delete","id":"$input.params('id')"}
```

### 2-6. CORS を有効にする

1. **`/`（ルート）** を選択 → **「CORS を有効にする」**

| 項目 | 値 |
|---|---|
| Access-Control-Allow-Methods | **GET・PUT・DELETE・OPTIONS** にチェック |
| Access-Control-Allow-Headers | `Content-Type` が含まれていることを確認 |
| Access-Control-Allow-Origin | `*` |

「保存」をクリック

### 2-7. API をデプロイする

1. **「APIをデプロイ」** ボタンをクリック

| 項目 | 値 |
|---|---|
| ステージ | **新しいステージ** |
| ステージ名 | `admin-stage` |

「デプロイ」をクリック後、**「URLを呼び出す」** の URL をメモしておきます。

```
例: https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/admin-stage
```

---

## Step 3：admin.html の API URL を書き換えて S3 にアップロードする

### 3-1. API エンドポイントを書き換える

`admin.html` をテキストエディタで開き、以下の部分を探します：

```javascript
var adminUrl = "https://APIドメイン名";
```

Step 2-7 でメモした URL に書き換えます：

```javascript
var adminUrl = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/admin-stage";
```

### 3-2. S3 にアップロードする

Session1 で作成した S3 バケット（<font color="red">lastname-firstname</font>）に、`admin.html` をそのままアップロードします（新しいバケットは不要です）。

1. Session1 の S3 バケットを開く
2. **「アップロード」** をクリック → 書き換えた `admin.html` を選択 → **「アップロード」**

---

## Step 4：動作確認

### 4-1. 管理画面にアクセスする

```
https://xxxxxxxxxxxx.cloudfront.net/admin.html
```

または S3 ウェブサイトエンドポイント経由でも確認できます。

### 4-2. 各機能を確認する

| 確認項目 | 操作 | 期待する動作 |
|---|---|---|
| 一覧表示 | 「一覧を表示」を押す | Session2 で登録した会員が一覧表示される |
| 照会 | ユーザIDを入力して「照会」を押す | 該当会員の情報がフォームに表示される |
| 更新 | フォームの内容を変更して「更新」を押す | 「更新が完了しました」と表示され、DynamoDB の値が変わる |
| 削除 | ユーザIDを入力して「削除」を押す | 「削除が完了しました」と表示され、一覧から消える |

---

## よくあるトラブルと対処法

### 一覧・照会が失敗する

- `admin.html` の `var adminUrl` が正しい API Gateway URL になっているか確認
- CORS で **GET** が許可されているか確認

### 更新・削除が失敗する

- CORS で **PUT** / **DELETE** が許可されているか確認（GET だけ許可されている状態になりやすいので注意）
- マッピングテンプレートがメソッドごとに正しく設定されているか確認

### 照会しても情報が出てこない

- 入力したユーザIDが Session2 で実際に登録したものと一致しているか確認（大文字・小文字も区別されます）

---

## 完成イメージ

| 画面 | URL |
|---|---|
| 管理者用 会員情報管理 | `https://xxxxxxxxxxxx.cloudfront.net/admin.html`（Session1 で作ったサイトに追加されます） |
