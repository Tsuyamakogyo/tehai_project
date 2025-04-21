# 手配検討支援ツール（Streamlit版）

このアプリは、建設現場の人材手配を効率化する社内向けのツールです。
ローカル環境でもWeb環境（Heroku）でも実行可能で、
ジャンルスキル・特性・傾向・実績に基づいて最適な人員割り当てを行います。

---

## 主な機能

- **スタッフ割り当てエンジン**  
  スキル評価（◎○△✕）・傾向スコア・note_preferenceによる特性優先ブーストなどを反映して最適なスタッフを自動提案

- **Streamlit アプリでの編集機能**  
  Webブラウザで手配情報を入力、結果表示をリアルタイムで確認できる。  
  将来的にはモバイル対応を検討しています。

- **傾向スコアロジック**  
  過去の配置履歴からジャンルごとの傾向スコアを算出・活用

- **note_preferenceマッチ**  
  備考欄に記載された「花岡金属：最優先」などのワードに基づいて配置優先度を自動ブースト

- **バリデーション機能**  
  重複配置や人数整合性エラーをチェックし、アラート表示

---

## ローカルでの実行方法

### 1. 仮想環境の作成と有効化（Windows）

```bash
cd tehai_project
python -m venv venv
.venv\Scripts\activate
```

### 2. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 3. アプリの起動

```bash
streamlit run tehai_streamlit_app.py
```

---

## **Gitの初期化とリモート登録**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<yourname>/tehai_project.git
```
---

## 実行URL

https://tehai-project.onrender.com/

---

## ファイル構成

```
tehai_project/
├── tehai_streamlit_app.py      # Streamlitアプリ本体
├── app/
│   ├── assignment_core.py      # 割当ロジック
│   ├── input_handler.py        # 入力CSVパース
│   ├── data_formatter.py       # 出力整形処理
│   ├── adapter.py              # 入出力データ変換
│   ├── trend_analyzer.py       # 傾向スコア処理
│   └── validation.py           # データチェック処理
├── tools/
│   └── data_preparer.py        # Googleスプレッドシート→入力整形
├── config/
│   ├── .env
│   └── rules.json              # スコアルール設定
├── .streamlit_storage/
│   ├── input/                  # 入力CSVフォルダ
│   │   ├──plan_date.csv
│   │   ├──project_data.csv
│   │   ├──am_workers.csv
│   │   ├──pm_workers.csv
│   │   └──latest_input_plan.txt
│   └── output/                 # 結果CSV・ログ
│       ├──log.csv
│       └──output_result.txt
├── .streamlit/        
│   └── secrets.toml
├── .gitignore
├── .python-version
├── bfg-1.15.0.jar
├── LICENSE
├── Procfile
├── requirements.txt
└── README.md
```

---

## スコアの意味（スキル記号）

スキル欄に使われる「◎○△✕」の記号は、以下のように数値化されます。

| 記号 | スコア | 意味           |
|------|--------|----------------|
| ◎   | 3      | 得意           |
| ○   | 2      | できる         |
| △   | 1      | 不慣れ・補佐可 |
| ✕   | 0      | 不可           |

このスコアが、ジャンル適正評価や傾向スコアと組み合わさり、スタッフの選定に利用されます。

---

## note_preference の記述ルール（特性ワード）

スタッフの備考欄に記載されたキーワードにより、特定案件への割り当てを優先ブーストできます。

### 書き方例：

```
備考：花岡金属：最優先|金属建具：優先|(仮称)三郷物流開発計画：最優先
```

### 対応項目：

- **ジャンル名**（例：`金属建具：優先`）
- **顧客名や現場名**（例：`花岡金属：最優先`）
- **案件名（表記ゆれ含め対応）**

### スコア換算（rules.jsonより）：

| 優先度ワード | 加点 |
|--------------|------|
| 最優先       | 100  |
| 優先         | 50   |

> normalize 処理により `(仮称)` や空白、記号の差異は無視してマッチします。

---

## ライセンス

MIT License