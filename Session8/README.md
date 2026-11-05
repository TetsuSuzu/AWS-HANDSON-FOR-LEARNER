# Session8 — Aurora と Lambda（Python）で会員 API を作る

> このセッションのコードは [gist](https://gist.github.com/TetsuSuzu/c751ca01aa96917d42e2763eefc96ffb) にあります。使うファイルを開き、中身をコピーして使えます。

[Session2](../Session2/README.md) の DynamoDB 版と同じ会員 API を、**Amazon Aurora（PostgreSQL 互換）** で作ります。Session4 まで（会員登録・管理画面が DynamoDB）を終えてから行ってください。API の形は同じなので、Session3・4 の画面は API の URL を差し替えるだけで使えます。

> **このセッションの位置づけ**
> 本編（Session2〜4）は DynamoDB です。このセッションでは、同じ題材を **リレーショナルデータベース（SQL）** で作り、DynamoDB と何が違うかを体験します。家計簿アプリのように、集計や関連するデータが増える場合に役立つ考え方を学びます。
>
> IaC（AWS SAM）で同じ構成をデプロイする版は、`AWS-HANDSON-FOR-LEARNER-IaC` リポジトリの `Session8-Aurora/` にあります。

## このセッションで作るもの

```text
API Gateway HTTP API（Session3 と同じ。統合先だけを差し替える）
   │
   ▼
Lambda（users-aurora-function-<名前>）  ← Python 3.12
   │  RDS Data API（HTTPS で SQL を送る。VPC は不要）
   ▼
Aurora PostgreSQL（users-aurora-<名前>）
   └── データベース kakeibo ／ テーブル users
          ▲
          └── 認証情報は Secrets Manager のシークレットから読む
```

## 事前準備

- AWS マネジメントコンソールのリージョンを **アジアパシフィック（東京）ap-northeast-1** にする
- `<名前>` は半角英数字で、Session2 と同じ値を使う（例: `yamada-taro`）
- Aurora の作成には **10 分以上** かかります。待っている間に、次の「用語の説明」を読んでください

> **料金の注意**: Aurora は起動している間ずっと料金がかかります（最小 ACU を 0.5 にしているため）。研修が終わったら、必ず [片付け](#片付け) を行ってください。料金は [Aurora の料金ページ](https://aws.amazon.com/jp/rds/aurora/pricing/) で確認できます。

### 用語の説明

| 用語 | 意味 |
|---|---|
| Aurora | AWS のデータベースです。MySQL または PostgreSQL と互換性があります。ここでは PostgreSQL 互換を使います |
| Aurora Serverless v2 | 負荷に合わせて処理能力（ACU）が自動で増減する Aurora です。ACU は処理能力の単位です |
| SQL | データベースに「表から探す」「追加する」などを命令するための言葉です。`SELECT`、`INSERT`、`UPDATE`、`DELETE` を使います |
| テーブル | 行と列でデータを並べた表です。このセッションでは会員を `users` テーブルに入れます |
| 主キー | 行を区別する重なりのない値です。`id` が主キーで、同じ ID は登録できません |
| RDS Data API | HTTPS の要求で SQL を実行できる仕組みです。Lambda を VPC に入れなくても Aurora に接続できます |
| Secrets Manager | パスワードなどの秘密の値を安全に保管する AWS のサービスです。Data API は、ここからパスワードを読みます |
| Query Editor | コンソールで SQL を書いて実行できる画面です。テーブルの作成に使います |
| `:id` の形（名前付きパラメーター） | SQL の中に値を直接書かず、後から差し込むための書き方です。文字列を直接つなぐと、SQL の書き換え（SQL インジェクション）の原因になるため、この書き方を使います |

## 手順

1. [Aurora クラスターを作成する](#1-aurora-クラスターを作成する)
2. [テーブルを作成する（Query Editor）](#2-テーブルを作成するquery-editor)
3. [Lambda 関数を作成し、コードを設定する](#3-lambda-関数を作成しコードを設定する)
4. [Lambda の実行ロールに権限を付ける](#4-lambda-の実行ロールに権限を付ける)
5. [テストしてみる（Lambda 単体）](#5-テストしてみるlambda-単体)
6. [（任意）HTTP API とつなぐ](#6-任意http-api-とつなぐ)
7. [（発展）家計簿の集計を SQL で書く](#7-発展家計簿の集計を-sql-で書く)
8. [片付け](#片付け)

---

## 1. Aurora クラスターを作成する

1. 検索欄に **RDS** と入力して開く。リージョンが **ap-northeast-1** であることを確認する
2. **データベースの作成** をクリックし、次のとおり選ぶ

   | 項目 | 選ぶ値 |
   |---|---|
   | 作成方法 | **標準作成** |
   | エンジンのタイプ | **Aurora（PostgreSQL 互換）** |
   | エンジンのバージョン | 表示される中で最新の 16 系（例: 16.x） |
   | テンプレート | **開発/テスト** |
   | DB クラスター識別子 | `users-aurora-<名前>` |
   | マスターユーザー名 | `postgres`（既定のまま） |
   | 資格情報の管理 | **Amazon RDS でマスターパスワードを管理する**（Secrets Manager に保存される） |
   | DB インスタンスクラス | **Serverless v2（メモリを最適化していないアーキテクチャ）** |
   | ACU の範囲（最小） | **0.5** |
   | ACU の範囲（最大） | **2** |
   | 接続 → パブリックアクセス | **いいえ** |
   | 追加設定 → 初期データベース名 | `kakeibo` |
   | 追加設定 → **RDS Data API を有効にする** | **チェックを入れる** |

   > 画面の名称や並びは、AWS の画面更新で少し変わることがあります。「Data API」と「Secrets Manager」の項目を必ず確認してください。Data API の項目が見当たらないときは、作成後にクラスターの **変更** から有効にできます。
   >
   > 最小 ACU を 0 にすると、一定時間使わないと停止して費用を抑えられます。ただし、停止からの再開に時間がかかり、Lambda がタイムアウトすることがあるため、この研修では 0.5 にしています。

3. **データベースの作成** をクリックし、作成が完了するまで待つ（ステータスが **利用可能** になる）

### 1-1. 後で使う 2 つの ARN を控える

作成したクラスターの詳細画面で、次の 2 つを控えます。

| 控えるもの | 場所 | 例 |
|---|---|---|
| クラスターの ARN | 詳細画面の **ARN** | `arn:aws:rds:ap-northeast-1:123456789012:cluster:users-aurora-yamada-taro` |
| シークレットの ARN | 詳細画面の **設定** タブ → **Secrets Manager ARN**（または Secrets Manager の画面） | `arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:rds!cluster-xxxx-xxxx` |

### 確認ポイント

- [ ] クラスターのステータスが **利用可能**
- [ ] 詳細画面で **RDS Data API** が **有効** になっている
- [ ] クラスターの ARN とシークレットの ARN を控えた

---

## 2. テーブルを作成する（Query Editor）

1. RDS の左メニューから **クエリエディタ** を開く
2. **データベースの接続** で、次のとおり入力する
   - データベース: `kakeibo`
   - 認証方法: **AWS Secrets Manager**
   - シークレット: 1-1 で作成された `rds!cluster-...` のシークレット
3. 接続したら、Session8 フォルダの `schema.sql` の内容をすべて貼り付けて **実行** する
4. 次の SQL で、テーブルができたことを確かめる

   ```sql
   SELECT * FROM users;
   ```

   結果が 0 件（行なし）で表示されれば成功です。

> **`schema.sql` の見方**: `CREATE TABLE` は表の形を決める命令です。`PRIMARY KEY` と `UNIQUE` は「重複を許さない」、`CHECK` は「この条件を満たす値だけ入れる」という決まりです。Python のコードに同じチェックを書かなくても、データベースが最後に守ってくれます。

### 確認ポイント

- [ ] `SELECT * FROM users;` が 0 件で成功する

---

## 3. Lambda 関数を作成し、コードを設定する

1. 検索欄に **Lambda** と入力して開く（リージョン **ap-northeast-1**）
2. **関数の作成** → **一から作成** を選び、次のとおり入力する

   | 項目 | 入力する値 |
   |---|---|
   | 関数名 | `users-aurora-function-<名前>` |
   | ランタイム | **Python 3.12** |
   | アーキテクチャ | **x86_64** |
   | 実行ロール | **基本的な Lambda のアクセス権限で新しいロールを作成** |

3. **関数の作成** をクリック
4. **コード** タブで `lambda_function.py` を開き、初期コードをすべて削除して、Session8 フォルダの `lambda_function.py` の内容を貼り付ける
5. **Deploy（デプロイ）** をクリック
6. **ランタイム設定** で、**ハンドラー** が初期値の `lambda_function.lambda_handler` のままであることを確認する

> **boto3 について**: Lambda の Python 実行環境には `boto3` が最初から入っています。ライブラリを追加する必要はありません。`rds-data`（Data API の道具）は、この `boto3` に含まれています。

### 3-1. 環境変数を設定する

**設定** タブ → **環境変数** → **編集** で、次の 3 つを追加して **保存** します。

| キー | 値 |
|---|---|
| `CLUSTER_ARN` | 1-1 で控えた **クラスターの ARN** |
| `SECRET_ARN` | 1-1 で控えた **シークレットの ARN** |
| `DB_NAME` | `kakeibo` |

> **環境変数とは？** プログラムに値を直接書かず、外から渡す設定です。Aurora を作り直したときも、コードを書き換えずに環境変数だけ直せます。

### 確認ポイント

- [ ] **コード** タブに `lambda_function.py` が表示され、Deploy 済み
- [ ] ハンドラーが `lambda_function.lambda_handler`
- [ ] 環境変数が 3 つ（`CLUSTER_ARN`、`SECRET_ARN`、`DB_NAME`）設定されている

---

## 4. Lambda の実行ロールに権限を付ける

Lambda が Data API を呼び、Secrets Manager からパスワードを読めるように、権限を付けます。

1. Lambda の **設定** タブ → **アクセス権限** → **ロール名** のリンクをクリック（IAM の画面が開く）
2. **許可を追加** → **インラインポリシーを作成** → **JSON** を選ぶ
3. 次の JSON を貼り付け、`<アカウントID>` と 2 か所の ARN を、1-1 で控えた値に置き換える

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "UseDataApi",
         "Effect": "Allow",
         "Action": ["rds-data:ExecuteStatement"],
         "Resource": "<クラスターの ARN>"
       },
       {
         "Sid": "ReadDbPassword",
         "Effect": "Allow",
         "Action": ["secretsmanager:GetSecretValue"],
         "Resource": "<シークレットの ARN>"
       }
     ]
   }
   ```

4. **次へ** → ポリシー名を `users-aurora-access-<名前>` にして **ポリシーの作成**

> **注意**: この JSON は、Aurora のクラスターとシークレットだけに権限を絞っています。Session2 の `AmazonDynamoDBFullAccess` のように、アカウント全体へ権限を広げていません。本番の考え方に近い書き方なので、読み比べてください。

### 確認ポイント

- [ ] 実行ロールに `users-aurora-access-<名前>` のインラインポリシーが付いている

---

## 5. テストしてみる（Lambda 単体）

API を作る前に、Lambda が Aurora を読み書きできるかを確かめます。

1. Lambda の **テスト** タブ → **新しいイベント** → イベント名 `create-user`
2. Session8 フォルダの `test-events/create-user.json` の内容を貼り付け、**保存** → **テスト**
   - `statusCode` が **201** で成功です
3. 同じように、次のイベントを順に試す

   | テストイベント | 期待する結果 |
   |---|---|
   | `test-events/list-users.json` | `statusCode` **200**、`users` に `a-0001` が出る |
   | `test-events/create-user.json` をもう一度 | `statusCode` **409**（同じ ID はすでにある） |
   | `test-events/update-user.json` | `statusCode` **200**（年齢が 31 になる） |
   | `test-events/delete-user.json` | `statusCode` **204** |
   | `test-events/delete-user.json` をもう一度 | `statusCode` **404**（すでに削除されている） |

4. Query Editor で `SELECT * FROM users;` を実行し、結果が画面の操作と一致するかを確かめる

> **エラーが出たら**
> - `KeyError: 'CLUSTER_ARN'` などは、環境変数の設定漏れです（3-1）
> - `AccessDeniedException` は、実行ロールの権限（4）を確かめてください
> - `BadRequestException` で `relation "users" does not exist` と出るときは、テーブルが作られていません（2）。データベース名が `kakeibo` かも確かめてください
> - 応答が遅い（数十秒かかる）ときは、Aurora が再開中の可能性があります。もう一度試してください

### 確認ポイント

- [ ] `create-user` が 201 で成功する
- [ ] `list-users` で登録した会員が見える
- [ ] 同じ ID の登録が 409 になる（データベースの主キーが重複を防いでいる）

---

## 6. （任意）HTTP API とつなぐ

Session3 の手順で HTTP API を作り、統合先に `users-aurora-function-<名前>` を選びます。ルートは次のとおりです。

| メソッド | パス |
|---|---|
| POST | `/`（パスなし。会員登録） |
| GET | `/users` |
| GET | `/users/{id}` |
| PUT | `/users/{id}` |
| DELETE | `/users/{id}` |

ルートの形は DynamoDB 版と同じです。そのため、Session3 の会員登録フォームや Session4 の管理画面は、**config.js の URL を新しい API に向けるだけ** で動きます。

---

## 7. （発展）家計簿の集計を SQL で書く

家計簿アプリでは、月別の支出合計やカテゴリ別の集計が必要です。SQL では次のように一行で書けます。Query Editor で試してください。

```sql
-- 入出金の表（金額は「整数の円」で持つ）
CREATE TABLE IF NOT EXISTS transactions (
  id       BIGSERIAL PRIMARY KEY,
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- 会員が消えたら、その入出金も消える
  kind     TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
  category TEXT NOT NULL,
  amount   INTEGER NOT NULL CHECK (amount >= 0),                  -- 円（小数は使わない）
  made_on  DATE NOT NULL
);

INSERT INTO transactions (user_id, kind, category, amount, made_on) VALUES
  ('a-0001', 'expense', '食費',   1200, '2026-08-01'),
  ('a-0001', 'expense', '交通費',  500, '2026-08-02'),
  ('a-0001', 'income',  '給与', 250000, '2026-08-25');

-- 月ごとの収入・支出の合計
SELECT to_char(made_on, 'YYYY-MM') AS month,
       SUM(CASE WHEN kind = 'income'  THEN amount ELSE 0 END) AS income,
       SUM(CASE WHEN kind = 'expense' THEN amount ELSE 0 END) AS expense
FROM transactions
WHERE user_id = 'a-0001'
GROUP BY month
ORDER BY month;
```

> **考えてみよう**
> - DynamoDB で同じ集計をする場合、どんな方法があるでしょうか（全件を取って Lambda で合計する、合計値を別の項目に持つ、など）
> - `ON DELETE CASCADE` があると、会員を削除したときに入出金も自動で消えます。DynamoDB では、この処理を Lambda で自分で書く必要があります
> - 金額を `FLOAT` ではなく `INTEGER` にする理由は何でしょうか

---

## 片付け

研修が終わったら、**課金が続かないように** 次の順に削除します。

1. Lambda の `users-aurora-function-<名前>` を削除する
2. （HTTP API を作った場合）API Gateway の該当 API を削除する
3. RDS で `users-aurora-<名前>` を選び、**アクション** → **削除** を選ぶ
   - 「最終スナップショットを作成する」の **チェックを外す**（研修用のため）
   - 削除の確認で `delete me` と入力する
4. IAM の実行ロールに付けた `users-aurora-access-<名前>` を削除する（ロール自体は Session2 のものを共有している場合は残してかまいません）
5. Secrets Manager に `rds!cluster-...` のシークレットが残っていないか確認する（残っていれば削除する）

> Session2 の DynamoDB テーブル・Lambda は、Session2・3 の案内どおりに削除してください。
