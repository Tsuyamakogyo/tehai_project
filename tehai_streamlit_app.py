import sys
import os
import csv
import subprocess
from datetime import datetime
import pandas as pd  # pandasをインポート
import streamlit as st
from app.data_formatter import parse_output_result
from app.input_handler import parse_input_data
from app.adapter import prepare_assignment_input
from app.assignment_core import run_assignment_engine
from app.validation import validate_assignments
from app.data_formatter import format_output

# 相対パスでappモジュールを参照できるようにする
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# --- 保存先フォルダ ---
INPUT_FOLDER = os.path.join(os.path.dirname(__file__), '.streamlit_storage', 'input')  # 修正: input フォルダへのパス

# --- CSV保存処理 ---
def save_to_csv(file_name, data):
    """データをCSVに保存する関数"""
    try:
        with open(file_name, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data)
    except Exception as e:
        st.error(f"ファイル保存エラー: {e}")

# --- ログ保存処理（save_log_from_parsed_outputの代わり） ---
def save_log(assignments, summary, genre_map):
    """ログをCSVファイルに保存する関数"""
    tehai_date = summary.get("date", "")

    # tehai_dateが空の場合にエラーメッセージを表示して処理を中断
    if not tehai_date:
        st.error("手配検討日が指定されていません。データが不完全な可能性があります。")
        return  # 空の場合は処理を中断

    # 日付を正しい形式（YYYY/MM/DD）で解析
    try:
        log_month = datetime.strptime(tehai_date, "%Y/%m/%d").strftime("%Y-%m")
    except ValueError:
        st.error(f"無効な日付形式です: {tehai_date}. 正しい形式（YYYY/MM/DD）で入力してください。")
        return  # 無効な形式の場合は処理を中断

    log_path = f'.streamlit_storage/output/log_{log_month}.csv'
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    if os.path.exists(log_path):
        log_df = pd.read_csv(log_path)
        log_df = log_df[log_df["日付"] != tehai_date]  # 同日削除
    else:
        log_df = pd.DataFrame(columns=["日付", "案件名", "顧客名", "ジャンル", "シフト", "スタッフ名", "記号"])

    new_rows = []
    for a in assignments:
        shift = "午前" if a['shift'] == 'morning' else "午後" if a['shift'] == 'afternoon' else "終日"
        genre = genre_map.get(a['customer'], "その他")
        staff_list = a['assigned_morning'] if shift == "午前" else a['assigned_afternoon']
        for s in staff_list:
            if s['name']:
                new_rows.append({
                    "日付": tehai_date,
                    "案件名": a['project_name'],
                    "顧客名": a['customer'],
                    "ジャンル": genre,
                    "シフト": shift,
                    "スタッフ名": s['name'],
                    "記号": s.get('shift_mark', '')
                })

    new_df = pd.DataFrame(new_rows)
    log_df = pd.concat([log_df, new_df], ignore_index=True)
    log_df.to_csv(log_path, index=False)

def save_log_from_parsed_output(parsed_rows, genre_map):           # ★ 追加
    """
    『出力結果テキストを手動編集 → 統計に再反映』用。
    main.py にあった処理を Streamlit 版へ移植。
    """
    if not parsed_rows:
        return

    tehai_date = parsed_rows[0]['日付']
    try:
        log_month = datetime.strptime(tehai_date, "%Y/%m/%d").strftime("%Y-%m")
    except ValueError:
        st.error(f"無効な日付形式です: {tehai_date}")
        return

    log_path = f'.streamlit_storage/output/log_{log_month}.csv'
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    if os.path.exists(log_path):
        log_df = pd.read_csv(log_path)
        log_df = log_df[log_df["日付"] != tehai_date]   # 同日の旧行を除去
    else:
        log_df = pd.DataFrame(columns=[
            "日付", "案件名", "顧客名", "ジャンル", "シフト", "スタッフ名", "記号"
        ])

    # ジャンル列を補完
    for row in parsed_rows:
        row['ジャンル'] = genre_map.get(row['顧客名'], "その他")

    log_df = pd.concat([log_df, pd.DataFrame(parsed_rows)], ignore_index=True)
    log_df.to_csv(log_path, index=False)

def write_result_file(result_text: str, validated: str) -> None:
    """.streamlit_storage/output/output_result.txt に結果を書き出す"""
    out_path = os.path.join(os.path.dirname(__file__),
                            ".streamlit_storage", "output", "output_result.txt")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("=== 出力結果 ===\n")
        f.write(result_text)
        f.write("\n\n=== バリデーション ===\n")
        f.write(validated)

# --- Streamlit UI ---
st.title("手配検討支援ツール")

# 手配検討日
date_input = st.text_input("手配検討日（YYYY/MM/DD）", key="date_input")

# 案件情報
project_input = st.text_area("案件情報（CSV形式）", key="project_input", height=200)

# 午前出勤者（カンマ区切り）
am_input = st.text_area("午前出勤者（カンマ区切り）", key="am_input")

# 午後出勤者（カンマ区切り）
pm_input = st.text_area("午後出勤者（カンマ区切り）", key="pm_input")

input_file_path = os.path.join(os.path.dirname(__file__), '.streamlit_storage', 'input', 'latest_input_plan.txt')

# ① －－－－ セッション変数の初期化 －－－－
if 'show_output' not in st.session_state:
    st.session_state['show_output'] = False   # 表示するかどうか
    st.session_state['output_content'] = ''   # 表示する内容
# －－－－－－－－－－－－－－－－－－－－

# 実行ボタン
if st.button('実行', key="execute_button"):
    if not date_input or not project_input or not am_input or not pm_input:
        st.warning("すべての項目を入力してください")
    else:
        try:
            parsed_date = datetime.strptime(date_input, "%Y/%m/%d")
            formatted_date = parsed_date.strftime("%Y/%m/%d")  # ← スラッシュ表記で保持
        except ValueError:
            st.error("日付は YYYY/MM/DD 形式で入力してください")
            st.stop()

        # データ保存処理
        try:
            # 保存先フォルダが存在しない場合は作成する
            os.makedirs(INPUT_FOLDER, exist_ok=True)

            # 入力内容をCSVに保存
            save_to_csv(os.path.join(INPUT_FOLDER, "plan_date.csv"), [[formatted_date]])

            # 案件情報の保存
            project_input_data = [[col.strip() for col in line.split(",")] for line in project_input.splitlines()]
            save_to_csv(os.path.join(INPUT_FOLDER, "project_data.csv"), project_input_data)

            # 午前・午後出勤者の保存
            am_input_data = [[w.strip()] for w in am_input.split(",")]
            pm_input_data = [[w.strip()] for w in pm_input.split(",")]
            save_to_csv(os.path.join(INPUT_FOLDER, "am_workers.csv"), am_input_data)
            save_to_csv(os.path.join(INPUT_FOLDER, "pm_workers.csv"), pm_input_data)

            # データを保存した後、次の処理（data_preparer.py、main.py）の実行
            python_executable = sys.executable
            try:
                # data_preparer.pyの実行
                result = subprocess.run([python_executable, "tools/data_preparer.py"], check=True, capture_output=True, text=True)
                st.write(result.stdout)  # 標準出力の内容を表示
            except subprocess.CalledProcessError as e:
                st.error(f"処理中にエラーが発生しました：\n{e.stderr}")

            # 最新の入力計画が存在しない場合にエラーメッセージ
            if not os.path.exists(input_file_path):
                st.error("latest_input_plan.txt の生成に失敗しました。データが不完全な可能性があります。")
                st.stop()  # ここで処理を停止する

            # `prepare_assignment_input`を呼び出して、スタッフプロフィールやプロジェクトを整形
            with open(input_file_path, encoding="utf-8") as f:
                raw_text = f.read()
            parsed = parse_input_data(raw_text)  # 読み込んだファイルからデータを解析
            assignment_input = prepare_assignment_input(parsed)  # スタッフや案件情報を整形

            # 割り当て処理
            assignments = run_assignment_engine(
                assignment_input['projects'],
                assignment_input['staff_profiles'],
                assignment_input['genre_map']
            )
            
            # ====== 文字列作成 & バリデーション ======
            validated_result = validate_assignments(assignments, assignment_input)
            result_text      = format_output(assignments, assignment_input['summary'])

            # 結果を保存
            save_log(assignments, assignment_input['summary'], assignment_input['genre_map'])  # 保存処理を行う

            # ② ★追加 : ファイル出力
            write_result_file(result_text, validated_result)
            
            out_path = os.path.join(os.path.dirname(__file__),
                            ".streamlit_storage", "output", "output_result.txt")

            with open(out_path, "r", encoding="utf-8") as f:
                st.session_state['output_content'] = f.read()
            st.session_state['show_output'] = True
            try:
                st.rerun()                  # 新バージョン
            except AttributeError:
                st.experimental_rerun()     # 旧バージョン（～1.24）

        except subprocess.CalledProcessError as e:
            st.error(f"処理中にエラーが発生しました：\n{e}")

# --- 結果表示 ---
output_path = ".streamlit_storage/output/output_result.txt"
if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    if st.session_state.get('show_output'):
        content = st.session_state['output_content']
        st.text_area("出力結果", value=content, height=300)

        # ▼▼▼ ❷ 「結果を再反映」ボタン内だけ引数を修正 ▼▼▼
        if st.button('結果を再反映', key="refresh_button"):
            parsed_rows = parse_output_result(content)
            try:
                with open(input_file_path, encoding="utf-8") as tf:
                    raw_text  = tf.read()
                parsed     = parse_input_data(raw_text)
                genre_map  = parsed['genre_map']
            except Exception as e:
                st.error(f"ジャンル取得失敗: {e}")
            try:
                save_log_from_parsed_output(parsed_rows, genre_map)    # ★ 呼び出し修正
                st.success("編集後の内容を統計に反映しました")
            except Exception as e:
                st.error(f"統計保存失敗: {e}")

# ④ －－－－ クリアボタン －－－－
if st.button('クリア', key="clear_button"):
    st.session_state['show_output'] = False
    st.session_state['output_content'] = ''
    try:
        st.rerun()                  # 新バージョン
    except AttributeError:
        st.experimental_rerun()     # 旧バージョン（～1.24）
# －－－－－－－－－－－－－－－－
