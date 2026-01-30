# 💰 支出・収入 & 📅 スケジュール管理アプリ（Streamlit + Supabase）

このアプリは **Streamlit** と **Supabase** を用いて作成した  
「支出・収入管理」と「スケジュール管理」を一体化した Web アプリです。

Streamlit Cloud 上で動作し、**Supabase のデータベースを利用することで、アプリ停止後もデータが永続的に保存** されます。

---

## ✨ 主な機能

### 1️⃣ 支出・収入管理
- 支出・収入の登録（正負で管理）
- 金額・カテゴリ・日付・メモを保存
- Supabase による永続保存

### 2️⃣ スケジュール管理
- 日付ごとの予定を登録
- タイトル・内容を保存
- Supabase テーブルで管理

### 3️⃣ カレンダー表示ページ（対応済み）
- 日付ごとに  
  - 📅 予定  
  - 💰 その日の収支合計  
  を一覧表示
- 「いつ・何があって・お金がいくら動いたか」が一目で分かる

---

## 🛠 使用技術

- Python
- Streamlit
- Supabase（PostgreSQL）
- supabase-py

---

## 📦 データベース構成（Supabase）

### expenses テーブル（支出・収入）
| 列名 | 型 | 説明 |
|----|----|----|
| id | bigint | 主キー |
| date | date | 日付 |
| amount | int | 金額（収入は正、支出は負） |
| category | text | カテゴリ |
| memo | text | メモ |

### schedules テーブル（予定）
| 列名 | 型 | 説明 |
|----|----|----|
| id | bigint | 主キー |
| date | date | 日付 |
| title | text | 予定タイトル |
| detail | text | 詳細 |

※ RLS（Row Level Security）は **OFF** にしています。

---

## 🔑 secrets.toml の設定（重要）

Supabase の接続情報は **Streamlit の secrets** に保存します。

### ① ローカルの場合
以下のフォルダとファイルを作成してください。

