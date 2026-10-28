-- 会員テーブル（Aurora PostgreSQL）
-- Query Editor v2 で、データベース kakeibo に接続してから実行します。

CREATE TABLE IF NOT EXISTS users (
  id         TEXT PRIMARY KEY,                       -- 主キー（同じ ID は登録できない）
  name       TEXT NOT NULL,
  email      TEXT NOT NULL UNIQUE,                   -- 同じメールアドレスも登録できない
  age        INTEGER NOT NULL CHECK (age >= 0),      -- 0 以上の整数だけ入る
  address    TEXT NOT NULL,
  tel        TEXT NOT NULL CHECK (tel ~ '^[0-9]+$'), -- 数字だけ入る
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
