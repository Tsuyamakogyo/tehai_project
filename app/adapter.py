import sys
import os
import json
import pandas as pd

# app フォルダのパスを sys.path に追加
sys.path.append(os.path.join(os.getcwd(), 'app'))

def parse_input_files(uploaded_file):
    """
    Streamlitでアップロードされたファイルを処理し、データフレームとして返す
    """
    try:
        # uploaded_fileはBytesIO形式なので、pandasで読み込む
        data = pd.read_csv(uploaded_file)
        return data
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

# rules.jsonの読み込み
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'rules.json')
with open(config_path, encoding="utf-8") as f:
    rules = json.load(f)

# GENRE_SCORE_MAPを設定
GENRE_SCORE_MAP = rules.get("genre_score_map", {"◎": 3, "○": 2, "△": 1, "✕": 0})

# app内のモジュールをインポート
from app.trend_analyzer import load_trend_scores, load_project_history_scores  # 修正済み

def prepare_assignment_input(parsed):
    projects_raw = parsed['projects']
    genre_map   = parsed['genre_map']

    # トレンドスコアとプロジェクト履歴スコアをロード
    trend_scores = load_trend_scores()
    project_scores = load_project_history_scores()

    staff_profiles = []
    for name, info in parsed['staff'].items():
        # 午前・午後OKフラグの判定（今まで通り）
        am_ok = (info['午前'] in ['◎','○'])
        pm_ok = (info['午後'] in ['◎','●'])
        am_symbol = info.get('午前記号','')
        pm_symbol = info.get('午後記号','')

        # ★ ここが最大の変更点 ★
        # すでに 'info["ジャンル"]' に {"建築一式":"◎","内装":"○"} の形で格納されている想定。
        skills_dict = {}
        if "ジャンル" in info:
            for genre_key, symbol in info["ジャンル"].items():
                # symbolが"◎"等の場合、スコアに変換
                score = GENRE_SCORE_MAP.get(symbol, 0)
                skills_dict[genre_key] = score

        profile = {
            'name': name,
            'am_ok': am_ok,
            'pm_ok': pm_ok,
            'am_symbol': am_symbol,
            'pm_symbol': pm_symbol,
            'skills': skills_dict,               # ここに最終数値をセット
            'note': info.get('特性',''),
            'note_preference': parse_note_preference(info.get('特性','')),
            'shape_score': info.get('shape_score', 0),
            'leadership_score': info.get('leadership_score', 0),
            'trend_scores': trend_scores.get(name, {}),
            'project_history_scores': project_scores.get(name, {})
        }
        staff_profiles.append(profile)

    # プロジェクト整形は従来通り
    proj_list = []
    for p in projects_raw:
        r_m = p['午前人数']
        r_a = p['午後人数']
        if r_m > 0 and r_a > 0:
            shift_type = 'full_day'
        elif r_m > 0:
            shift_type = 'morning'
        elif r_a > 0:
            shift_type = 'afternoon'
        else:
            shift_type = 'unknown'

        proj_list.append({
            'project_name': p['案件名'],
            'customer': p['顧客名'],
            'start_time': p['時間'],
            'shift': shift_type,
            'required_morning': r_m,
            'required_afternoon': r_a,
            'project_key_morning': f"{p['案件名']}_午前",
            'project_key_afternoon': f"{p['案件名']}_午後"
        })

    return {
        'projects': proj_list,
        'staff_profiles': staff_profiles,
        'genre_map': parsed['genre_map'],
        'summary': parsed['summary']
    }

def parse_note_preference(note_text):
    result = {}
    parts = note_text.split("|")
    for part in parts:
        if "：" in part:
            key, level = part.split("：", 1)
            result[key.strip()] = level.strip()
    return result
