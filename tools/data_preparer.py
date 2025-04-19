import csv
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# --- 認証設定 ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
key_path = os.path.join("config", "tehai-reader-key.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
client = gspread.authorize(creds)

# --- スプレッドシートからデータ取得（先に記憶情報を準備） ---
spreadsheet_id = "1wmG17XpaEJlO36uofjDm9bdw2DAwEbsV2EQ4uw_yzho"
sh = client.open_by_key(spreadsheet_id)

# 顧客リスト
customer_sheet = sh.worksheet("顧客リスト")
customer_df = pd.DataFrame(customer_sheet.get_all_records())

# 人物データ
person_sheet = sh.worksheet("人物データ")
person_df = pd.DataFrame(person_sheet.get_all_records())

# --- ローカルCSV読み込み（手配データ） ---
with open("input/plan_date.csv", encoding="utf-8") as f:
    plan_date = f.read().strip()

with open("input/project_data.csv", encoding="utf-8") as f:
    project_data = list(csv.reader(f))

def read_workers_flat(csv_path: str) -> list[str]:
    """
    『行ごと・セルごと』に散らばっている名前を
    すべて 1 次元のリストにまとめて返すユーティリティ。
    縦並び・横並びどちらで書かれていても取得できる。
    """
    names: list[str] = []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.reader(f):
            # 空セルを除外して伸ばす
            names.extend(name.strip() for name in row if name.strip())
    return names

# --- 出勤者 CSV を読み込む ---
am_workers = read_workers_flat("input/am_workers.csv")
pm_workers = read_workers_flat("input/pm_workers.csv")

# --- 顧客ジャンルの抽出（略称ベース） ---
unique_customers = set([row[0].strip() for row in project_data])
customer_info = []
for customer in unique_customers:
    match = customer_df[customer_df["略称"] == customer]
    if not match.empty:
        genre = match.iloc[0]["お仕事ジャンル"]
        customer_info.append(f"- {customer}：{genre}")
    else:
        customer_info.append(f"- {customer}：（ジャンル不明）")

# --- 出勤希望者プロフィール抽出 ---
def parse_worker(raw_name):
    return raw_name.replace("◎", "").replace("○", "").replace("●", "").strip()

def format_profile(name):
    match = person_df[person_df["略称"] == name]
    if match.empty:
        return f"{name}：データ未登録"
    row = match.iloc[0]
    return (
        f"{name}（{row.get('形態', '－')}）：リーダー資質{row.get('リーダーとしての資質', '－')}／"
        f"建築一式{row.get('建築一式', '－')} 内装{row.get('内装', '－')} 金属建具{row.get('金属建具', '－')} 防水{row.get('防水', '－')} その他{row.get('その他', '－')} "
        f"リフォーム{row.get('リフォーム', '－')} 木工・木製建具{row.get('木工・木製建具', '－')} 同業他社{row.get('同業他社', '－')}"
        f"／特性：{row.get('備考', '')}"
    )

unique_workers = set([parse_worker(n) for n in am_workers + pm_workers if n.strip()])
worker_profiles = [format_profile(name) for name in sorted(unique_workers)]

# --- 人数構成カウント ---
required_am = sum(int(row[3]) for row in project_data)
required_pm = sum(int(row[4]) for row in project_data)
required_nt = sum(int(row[5]) for row in project_data)

attendance_am = len(am_workers)
attendance_pm = len(pm_workers)
attendance_nt = 0

# --- 出力形式を整えてファイル保存 ---
test_input_path = "latest_input_plan.txt"
with open(test_input_path, "w", encoding="utf-8") as f:
    f.write("【手配検討日】\n")
    f.write(f"手配検討日：{plan_date}\n\n")

    f.write("【人数構成サマリー】\n")
    f.write(f"必要＞ 午前：{required_am}/午後：{required_pm}/夜間：{required_nt}\n")
    f.write(f"出勤＞ 午前：{attendance_am}/午後：{attendance_pm}/夜間：{attendance_nt}\n\n")

    f.write("【案件データ】\n")
    for row in project_data:
        f.write(",".join(row) + "\n")

    f.write("\n【午前希望】\n")
    f.write(",".join(am_workers) + "\n")

    f.write("\n【午後希望】\n")
    f.write(",".join(pm_workers) + "\n")

    f.write("\n【顧客ジャンル一覧】\n")
    f.write("\n".join(customer_info))

    f.write("\n\n【出勤希望者プロファイル】\n")
    f.write("\n".join(worker_profiles))
