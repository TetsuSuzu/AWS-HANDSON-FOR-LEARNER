# Session0 — 教材を手元に入手する

この手順では、ハンズオンの教材（このリポジトリ）を自分のパソコンに入手します。入手方法は **git clone** と **zip ダウンロード** の 2 通りです。どちらか一方を選んでください。

> 教材の内容は、GitHub 上の次のリポジトリにあります。
>
> `https://github.com/TetsuSuzu/AWS-HANDSON-FOR-LEARNER`

## 事前準備

- インターネットに接続できること
- GitHub のアカウントは不要です（公開リポジトリのため、ログインせずに入手できます）

---

## 方法 A：git clone で入手する（おすすめ）

Git を使うと、あとから教材の更新を取り込めます。

### A-1. Git がインストールされているか確認する

1. Windows の **PowerShell** を開く（スタートメニューで `PowerShell` と入力して開く）
2. 次のコマンドを入力し、Enter を押す

   ```powershell
   git --version
   ```

3. `git version 2.xx.x` のように表示されれば、インストール済みです。次の A-2 に進みます
4. `git` が見つからないと表示された場合は、[Git for Windows](https://git-scm.com/download/win) をインストールしてから、PowerShell を開き直してください。インストール中の選択肢は、すべて既定のままで構いません

### A-2. 教材を clone する

1. 教材を置きたい場所に移動する。例: デスクトップ

   ```powershell
   cd $HOME\Desktop
   ```

2. 次のコマンドを入力し、Enter を押す

   ```powershell
   git clone https://github.com/TetsuSuzu/AWS-HANDSON-FOR-LEARNER.git
   ```

3. `AWS-HANDSON-FOR-LEARNER` というフォルダができれば成功です

### A-3. 講師が指定したブランチに切り替える（必要な場合のみ）

講師から特定のブランチ名を指定された場合は、clone したフォルダの中で次のコマンドを実行します。

```powershell
cd AWS-HANDSON-FOR-LEARNER
git checkout <ブランチ名>
```

`<ブランチ名>` は講師の指示どおりに置き換えます（`<` と `>` は入力しません）。指示がない場合は、このまま次に進んでください。

### A-4. 教材を更新する（あとから）

教材が更新されたときは、`git pull` で GitHub の最新を取り込みます。講師から「教材を更新しました」と案内があったときに行ってください。

**1. 手元の変更を確かめる**

```powershell
cd $HOME\Desktop\AWS-HANDSON-FOR-LEARNER
git status
```

- `nothing to commit, working tree clean` と出たら、手元に変更はありません。**3 に進みます**
- `modified: Session1/config.js` のように、ファイルの名前が出たら、手元で書き換えたファイルがあります。**2 に進みます**。Session3・4 で `config.js` に API の URL を書いたあとは、たいていこの状態です

**2. 書き換えたファイルを退避する（変更がある場合）**

変更があるまま `git pull` を実行すると、次のようなエラーで止まります。

```text
error: Your local changes to the following files would be overwritten by merge:
        Session1/config.js
Please commit your changes or stash them before you merge.
```

これは、自分の書き換えを守るための動きです。次の手順で、書き換えた内容を別の場所に退避し、教材を最新にしてから、書き換えを戻します。

```powershell
# 自分の config.js をデスクトップにコピーしておく（API の URL などが入っている）
Copy-Item Session1\config.js $HOME\Desktop\config.js.bak

# 教材の config.js を、書き換える前の状態に戻す
git restore Session1/config.js
```

ほかにも `modified:` と出たファイルがあれば、同じように退避してから `git restore <ファイルのパス>` を実行します。

**3. 最新を取り込む**

```powershell
git pull
```

`Already up to date.` と出たら、すでに最新です。ファイルの名前がいくつか並んだら、更新を取り込めています。

**4. 退避した内容を戻す（2 を行った場合）**

1. `$HOME\Desktop\config.js.bak` を、メモ帳などで開く
2. 更新後の `Session1\config.js` を開き、`.bak` に書いてあった API の URL などを、同じ項目に書き写す

   ```javascript
   window.API_ENDPOINT = "（.bak の値）";
   window.ADMIN_API_ENDPOINT = "（.bak の値）";
   ```

   更新で**新しい項目が増えている**場合があります（例: `COGNITO_REGION`、`COGNITO_CLIENT_ID`）。新しい項目は、そのまま残します。`.bak` を丸ごと上書きコピーしないでください。新しい項目が消えます。

**5. 更新できたかを確かめる**

```powershell
git log -1 --oneline
```

最新の更新の説明が 1 行出ます。講師が伝えた内容と合っていれば、更新できています。

> **ブランチを指定されていた場合**（A-3）は、そのブランチの上で `git pull` します。ブランチを変えたいときは、`git checkout <ブランチ名>` のあとに `git pull` を実行します。
>
> **更新で Session の番号や内容が変わる**ことがあります。更新したあとは、講師が案内する Session の番号を確かめてから、手順書を開いてください。

---

## 方法 B：zip でダウンロードする

Git を使わずに入手する方法です。更新を取り込むときは、もう一度 zip をダウンロードしてください。

### B-1. zip をダウンロードする

1. ブラウザーで次の URL を開く

   `https://github.com/TetsuSuzu/AWS-HANDSON-FOR-LEARNER`

2. 緑色の **Code** ボタンをクリック
3. **Download ZIP** をクリックする

   > 講師から特定のブランチを指定された場合は、ブランチ名を選んでから **Code** → **Download ZIP** を行います。

### B-2. zip を展開する

1. ダウンロードした `AWS-HANDSON-FOR-LEARNER-main.zip`（または `...-<ブランチ名>.zip`）を探す。通常は「ダウンロード」フォルダにあります
2. ファイルを右クリックし、**「すべて展開」** を選ぶ
3. 展開先に **デスクトップ** などを指定し、**展開** をクリックする
4. `AWS-HANDSON-FOR-LEARNER-main` というフォルダができれば成功です

> フォルダ名の末尾の `-main` は、ダウンロードしたブランチによって異なります。手順の中では、どちらのフォルダを使っても構いません。


### B-3. 教材を更新する（あとから）

zip には、更新を取り込む機能（`git pull`）がありません。教材が更新されたときは、新しい zip をダウンロードして、置き換えます。**古いフォルダは、すぐには削除しないでください。**

1. B-1・B-2 と同じ手順で、最新の zip をダウンロードして展開する（古いフォルダとは別の場所か、別の名前にする。例: デスクトップに `AWS-HANDSON-FOR-LEARNER-new`）
2. 古いフォルダの `Session1\config.js` を、メモ帳などで開く（API の URL などが書いてあります）
3. 新しいフォルダの `Session1\config.js` を開き、古い `config.js` に書いてあった API の URL などを、同じ項目に書き写す

   ```javascript
   window.API_ENDPOINT = "（古い config.js の値）";
   window.ADMIN_API_ENDPOINT = "（古い config.js の値）";
   ```

   更新で**新しい項目が増えている**場合があります（例: `COGNITO_REGION`、`COGNITO_CLIENT_ID`）。新しい項目は、そのまま残します。古い `config.js` を丸ごとコピーして上書きしないでください。新しい項目が消えます。
4. ほかにも自分で書き換えたファイルがあれば、同じように内容を写す
5. 以降は、**新しいフォルダ**を使う。古いフォルダは、動作を確かめてから削除する

### B-4. zip から git に切り替える（おすすめ）

zip で入手した人も、あとから git に切り替えると、次回からは `git pull` で更新できます。

1. 方法 A の A-1・A-2 で、教材を **別の場所に clone** する（zip を展開したフォルダとは別のフォルダ）
2. 古い（zip の）フォルダの `Session1\config.js` の内容を、clone した `Session1\config.js` に書き写す（B-3 の 3 と同じです。新しい項目は残します）
3. 以降は、clone したフォルダを使う

---

## 入手できたかを確認する

入手したフォルダの中に、次のフォルダとファイルがあるか確認してください。

- [ ] `Session1` フォルダ（`index.html`、`app.js`、`styles.css`、`photo1.png`、`photo2.png` を含む）
- [ ] `Session2` フォルダ（`lambda_function.py` を含む）
- [ ] `Session3` フォルダ（`README.md` を含む）
- [ ] `Session4` フォルダ（`lambda_function.py` を含む）
- [ ] `Session5` フォルダ（`README.md`、`lambda_function.py`、`admin_lambda_function.py` を含む）
- [ ] `Session6` フォルダ（`lambda_function.py` を含む）
- [ ] `Session7` フォルダ（`lambda_function.py`、`shops.txt` を含む）
- [ ] `README.md`（教材の全体案内）

---

## 注意事項

- 教材フォルダには、パスワード、アクセスキー、秘密鍵などの **秘密情報は含まれていません**。ハンズオンの途中で、自分の認証情報を教材フォルダに保存しないでください。
- 教材フォルダの中のファイルを、AWS の S3 にアップロードして Amplify で公開するときは、`Session1` フォルダの中身だけを対象にします。
- 手順書の中の `<名前>` や `<アカウントID>` などは、自分の値に置き換えてから使います。

## 次へ

[Session1](../Session1/README.md) に進んでください。S3 と Amplify で静的ウェブサイトを公開します。
