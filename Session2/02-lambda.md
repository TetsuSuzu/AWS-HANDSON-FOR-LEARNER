# 手順 2：Lambda 関数を作る

API からの要求を受けて、DynamoDB を読み書きするプログラム（Lambda 関数）を作ります。

> **Lambda とは？**
> サーバーを用意せず、呼び出されたときだけプログラムを動かす仕組みです。この手順では、Lambda の画面にある Python エディターでプログラムを書きます。

## 2-1. Lambda の画面を開く

1. 検索欄に **Lambda** と入力して開く
2. リージョンが **ap-northeast-1** であることを確認する

## 2-2. 関数を作成する

1. **関数の作成** をクリック
2. **一から作成** を選び、次のとおり入力する

| 項目 | 入力する値 |
|---|---|
| 関数名 | `users-function-<名前>` |
| ランタイム | **Python 3.12** |
| アーキテクチャ | **x86_64** |
| 実行ロール | **基本的な Lambda のアクセス権限で新しいロールを作成** |

3. **関数の作成** をクリック
4. 数秒待つと、関数の画面が開きます

> **実行ロールとは？**
> Lambda が、ほかの AWS サービス（この教材では DynamoDB）を使うときの「許可証」です。今は CloudWatch（ログ）へ書く権限だけ付いています。DynamoDB の権限は、2-6 で付けます。

## 2-3. Python のプログラムを書く

Lambda の画面にあるコードエディターを使います。ローカルのファイルを zip にしたり、アップロードしたりする必要はありません。

1. Lambda の画面で **コード** タブを開く
2. コードソースにある `lambda_function.py` を開く
3. `Session2/app.py` のコードをすべてコピーする（このフォルダ内のファイル）
4. `lambda_function.py` のエディターにある初期コードをすべて選択して、コピーしたコードに置き換える
5. **Deploy（デプロイ）** をクリックし、変更を反映する

> **注意**: コードは先頭から末尾まで全部置き換えてください。一部だけ残すと、関数名が重複したり、正しく動かなくなったりします。

### 別の方法：PowerShell で zip をアップロードする

Lambda のコードを PowerShell で zip にしてアップロードする場合は、次の方法も使えます。コードは `Session2` フォルダ内の `app.py` を使います。

1. PowerShell を開き、`Session2` フォルダに移動する。コマンド中の `<ユーザー名>` と `<名前>` は実際の値に置き換える（`<` `>` は入力しない）

   ```powershell
   cd C:\Users\<ユーザー名>\AWS-HANDSON-FOR-LEARNER\Session2
   ```

2. `app.py` を zip にする

   ```powershell
   Compress-Archive -Path app.py -DestinationPath users-function-<名前>.zip -Force
   ```

   > zip ファイルは現在の `Session2` フォルダに作成されます。

3. Lambda の **コード** タブで **アップロード元** → **.zip ファイル** → **アップロード** を選び、作成した zip を指定する
4. **保存** または **Deploy（デプロイ）** をクリックする
5. ランタイム設定のハンドラーを `app.handler` に変更して保存する

> **注意**: この方法ではファイル名が `app.py` なので、ハンドラーは `lambda_function.handler` ではなく `app.handler` にします。コンソール上でコードを書く方法と、zip をアップロードする方法のどちらか一方を選んでください。

### 2-4. ハンドラーを設定する（コンソールでコードを書く場合）

ハンドラーは「どの関数から始めるか」を指定する項目です。コンソールでコードを書く方法では、`lambda_function.py` の `handler` 関数から始まるように設定します。PowerShell で zip をアップロードした場合は、2-3 の別の方法で設定した `app.handler` のままにしてください。

コンソールで関数を「一から作成」すると、ハンドラーの初期値は `lambda_function.lambda_handler` になっています。ところが `app.py` の関数名は `lambda_handler` ではなく `handler` です。このままでは Lambda が関数を見つけられず、実行時に `Runtime.HandlerNotFound` のエラーになります。次の手順で `lambda_function.handler` に書き換えてください。

1. **コード** タブの下の **ランタイム設定** → **編集**
2. **ハンドラー** が初期値の `lambda_function.lambda_handler` になっていることを確認する
3. **ハンドラー** を次のように書き換える（`lambda_` を消して `handler` だけにする）

   | タイミング | ハンドラー |
   |---|---|
   | 初期値（書き換え前） | `lambda_function.lambda_handler` |
   | 書き換え後 | `lambda_function.handler` |

   ```
   lambda_function.handler
   ```

4. **保存**

> `lambda_function.handler` は「ファイル名 `lambda_function.py` の関数 `handler`」という意味です。詳しくは [README の「Lambda のハンドラとは？」](README.md#補足lambda-のハンドラとは) を見てください。

### 確認ポイント

- [ ] **コード** タブに `lambda_function.py` が表示されている
- [ ] **ランタイム設定** のハンドラーが、コンソールでコードを書く場合は `lambda_function.handler`（初期値の `lambda_function.lambda_handler` のままではない）、zip をアップロードした場合は `app.handler`
- [ ] ランタイムが Python 3.12

## 2-5. 環境変数を設定する

プログラムが読み書きするテーブル名を、Lambda に教えます。

1. **設定** タブ → **環境変数** → **編集**
2. **環境変数を追加** をクリックし、次を入力する

| キー | 値 |
|---|---|
| `TABLE_NAME` | `users-table-<名前>` |

3. **保存**

> **環境変数とは？**
> プログラムの中に値を直接書かず、外から渡す設定です。テーブル名を変えるときに、プログラムを書き換えずに済みます。

## 2-6. 実行ロールに DynamoDB の権限を付ける

関数を作成すると、Lambda の実行ロールが自動で作られています。そのロールに、DynamoDB を操作する権限を付けます。

1. **設定** タブ → **アクセス権限**
2. **ロール名** のリンクをクリック（IAM の画面が開きます）
3. **許可を追加** → **ポリシーをアタッチ**
4. 検索欄に `AmazonDynamoDBFullAccess` と入力し、チェックを付ける
5. **許可を追加** をクリック

> **注意**: `AmazonDynamoDBFullAccess` は、アカウント内のすべての DynamoDB テーブルを操作できる権限です。この教材は練習用のアカウントで使う前提です。本番環境では、対象テーブルだけに絞ったポリシーを使ってください。

### 確認ポイント

- [ ] 環境変数 `TABLE_NAME` が `users-table-<名前>`
- [ ] 実行ロールに `AmazonDynamoDBFullAccess` が付いている

## 2-7. テストしてみる（Lambda 単体）

API を作る前に、Lambda が正しく動くかを確かめます。

1. Lambda の画面 → **テスト** タブ → **テストイベント** → **新しいイベント**
2. **イベント名**: `create-user`
3. `Session2/test-events/create-user.json` の中身を貼り付ける（このフォルダ内のファイル）
4. **保存** → **テスト** をクリック
5. 結果の **実行結果** に、次のような表示が出れば成功です。

   ```json
   {
     "statusCode": 201,
     "headers": { "Content-Type": "application/json; charset=utf-8" },
     "body": "{\"message\": \"登録が完了しました\", ...}"
   }
   ```

6. 同じように `list-users`（一覧）のイベントも試す（`Session2/test-events/list-users.json`）。`"users"` の中に、先ほど登録した会員が出れば成功です。

> **エラーが出たら**: 画面の **実行結果** と **ログ出力**（CloudWatch Logs へのリンク）を確認します。`AccessDeniedException` が出たら 2-6 の権限を、`ResourceNotFoundException` が出たら テーブル名（`TABLE_NAME`）を確認してください。

### 確認ポイント

- [ ] `create-user` のテストが `statusCode: 201` で成功
- [ ] `list-users` のテストで、登録した会員が表示される

## 次へ

[../Session3/README.md](../Session3/README.md) に進んでください。
