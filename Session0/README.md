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

教材が更新されたときは、フォルダの中で次のコマンドを実行します。

```powershell
cd $HOME\Desktop\AWS-HANDSON-FOR-LEARNER
git pull
```

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
