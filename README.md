# インターンシップ向け Web ハンズオン

GitHub と GitHub Actions を使って、**自分のPCだけ**で Web サイトを作り、世界に公開するハンズオンです。
**AWS アカウントは不要**です。

> サーバー（S3・API Gateway・Lambda・DynamoDB・生成AI）は **事務局が事前に用意** しています。
> みなさんは、配布される **API エンドポイント** を使って、フロントエンド（Web 画面）の開発に集中します。

---

## このハンズオンで学べること

| テーマ | 内容 |
|---|---|
| Git / GitHub | リポジトリの Fork・clone・編集・commit・push |
| Web フロントエンド | HTML / CSS / JavaScript の編集とローカル実行 |
| API 連携 | 配布された REST API（会員登録・生成AI）をブラウザから呼び出す |
| CI/CD | GitHub Actions で push するだけで GitHub Pages に自動公開 |

---

## 完成イメージ

```
　　　　　　　　あなたのPC                          GitHub / クラウド
┌───────────────────────────┐        ┌──────────────────────────────┐
│  web/ を編集                       │        │  GitHub Actions                            │
│   ├ index.html                     │ push   │     └→ GitHub Pages に自動公開             │
│   ├ styles.css        ───────────▶ │        │         https://<ユーザー名>.github.io/... │
│   └ photo*.png                     │        │                                            │
│                                    │        │  ┌── 事務局が用意済み ─────────────┐       │
│  python -m http.server 8000        │  API   │  │ API Gateway → Lambda → DynamoDB │       │
│   → http://localhost:8000  ────────┼────────┼─▶│ API Gateway → Lambda → 生成AI    │       │
└───────────────────────────┘        │  │ S3（公開用バケット）             │       │
                                                │  └──────────────────────────────┘       │
                                                └──────────────────────────────┘
```

---

## セッション一覧

| Session | 内容 | キーワード |
|---|---|---|
| [Session0](Session0/README.md) | 環境セットアップ（GitHub アカウント・Fork・clone・ローカルサーバー起動） | Git / GitHub / Python |
| [Session1](Session1/README.md) | ローカルで Web サイトを動かす・HTML/CSS を編集する | HTML / CSS / localhost:8000 |
| [Session2](Session2/README.md) | 会員登録 API を呼び出す（配布エンドポイントを設定） | REST API / fetch |
| [Session3](Session3/README.md) | AI おすすめ機能を呼び出す（配布エンドポイントを設定） | 生成AI / API |
| [Session4](Session4/README.md) | GitHub Actions で GitHub Pages に自動公開する | CI/CD / GitHub Actions |

---

## フォルダ構成

```
.
├── README.md                 ← このファイル
├── web/                      ← ★みなさんが編集する Web サイト本体
│   ├── index.html
│   ├── styles.css
│   ├── photo1.png
│   └── photo2.png
├── Session0〜4/README.md     ← 各セッションの手順書
├── .github/workflows/        ← GitHub Actions（自動公開の設定）
│   └── deploy-pages.yml
└── staff/                    ← 事務局向け：サーバー構築手順・コード（学生は使いません）
```

---

## 事前に必要なもの

| 必要なもの | 用途 |
|---|---|
| GitHub アカウント（無料） | リポジトリの Fork とサイト公開（GitHub Pages） |
| ブラウザ（Chrome / Edge など） | サイトの表示・動作確認 |
| テキストエディタ（[VS Code](https://code.visualstudio.com/) 推奨） | HTML/CSS の編集 |
| Python 3（多くのPCに標準搭載） | ローカルサーバー（`python -m http.server`）の起動 |

> Python が入っていない場合の代替手段は [Session0](Session0/README.md) で案内します。

---

## まずはここから

➡️ **[Session0：環境セットアップ](Session0/README.md)** から始めてください。
