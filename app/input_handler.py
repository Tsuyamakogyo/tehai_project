import re
import json
import os

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'rules.json')
with open(config_path, "r", encoding="utf-8") as f:
    RULES = json.load(f)

LEADERSHIP_SCORE_MAP = RULES["leadership_score"]
SHAPE_PRIORITY_MAP = RULES["employment_type_score"]
GENRE_SCORE_MAP = RULES["genre_score_map"]
ALLOWED_GENRES = set(RULES["allowed_genres"])

def parse_input_data(raw_text):
    lines = raw_text.strip().split('\n')
    section = None
    parsed = {
        'projects': [],
        'staff': {},
        'genre_map': {},
        'summary': {
            'date': '',
            'required': '',
            'available': ''
        }
    }

    for line in lines:
        line = line.strip()
        if line.startswith('手配検討日：'):
            parsed['summary']['date'] = line.replace('手配検討日：', '').strip()
            print(f"Debug: Handwritten date found: {parsed['summary']['date']}")  # デバッグ用
            continue
        elif line.startswith('必要＞'):
            parsed['summary']['required'] = line.replace('必要＞', '').strip()
            continue
        elif line.startswith('出勤＞'):
            parsed['summary']['available'] = line.replace('出勤＞', '').strip()
            continue

        if line.startswith('【案件データ】'):
            section = '案件'
            continue
        elif line.startswith('【午前希望】'):
            section = '午前'
            continue
        elif line.startswith('【午後希望】'):
            section = '午後'
            continue
        elif line.startswith('【顧客ジャンル一覧】'):
            section = 'ジャンル'
            continue
        elif line.startswith('【出勤希望者プロファイル】'):
            section = 'プロファイル'
            continue

        if section == '案件' and line:
            parts = line.split(',')
            parsed['projects'].append({
                '顧客名': parts[0],
                '案件名': parts[1],
                '時間': parts[2],
                '午前人数': int(parts[3]),
                '午後人数': int(parts[4]),
                '夜間人数': int(parts[5])
            })

        elif section in ('午前', '午後') and line:
            tokens = line.split(',')
            for t in tokens:
                t = t.strip()
                if not t:
                    continue
                symbol = t[0]  # ◎、○、● の記号を取得
                name = t[1:].strip()  # 名前を取得
                if name not in parsed['staff']:
                    parsed['staff'].setdefault(name, {
                        '午前': '',
                        '午後': '',
                        '午前記号': '',
                        '午後記号': '',
                        'ジャンル': {},
                        '特性': '',
                        'note_preference': {},
                        'shape': '',
                        'shape_score': 0,
                        'leadership': '',
                        'leadership_score': 0
                    })
                if section == '午前':
                    parsed['staff'][name]['午前記号'] = symbol
                if section == '午後':
                    parsed['staff'][name]['午後記号'] = symbol
                parsed['staff'][name][section] = symbol

        elif section == 'ジャンル' and line:
            if '：' in line:
                line2 = line.replace('- ', '')
                company, genre = line2.split('：', 1)
                genre = genre.strip()
                if genre not in ALLOWED_GENRES:
                    genre = "その他"
                parsed['genre_map'][company.strip()] = genre

        elif section == 'プロファイル' and '：' in line:
            print("[DEBUG] Raw profile line:", line)
            left, rest = line.split('：', 1)
            match = re.match(r'^(.*?)（(.*?)）', left.strip())
            if match:
                staff_name = match.group(1).strip()
                shape_str = match.group(2).strip()
            else:
                staff_name = left.strip()
                shape_str = ""

            if staff_name not in parsed['staff']:
                parsed['staff'][staff_name] = {
                    '午前': '',
                    '午後': '',
                    '午前記号': '',
                    '午後記号': '',
                    'ジャンル': {},
                    '特性': '',
                    'note_preference': {},
                    'shape': '',
                    'shape_score': 0,
                    'leadership': '',
                    'leadership_score': 0
                }

            parsed['staff'][staff_name]['shape'] = shape_str
            parsed['staff'][staff_name]['shape_score'] = SHAPE_PRIORITY_MAP.get(shape_str, 0)

            sub_parts = rest.split('／')
            for sub in sub_parts:
                print("[DEBUG] sub=", sub)
                sub = sub.strip()

                if 'リーダー資質' in sub:
                    val = sub.replace('リーダー資質', '').strip()
                    val_score = LEADERSHIP_SCORE_MAP.get(val, 0)
                    parsed['staff'][staff_name]['leadership'] = val
                    parsed['staff'][staff_name]['leadership_score'] = val_score

                elif sub.startswith("特性："):
                    note_text = sub.replace("特性：", "").strip()
                    parsed['staff'][staff_name]['特性'] = note_text

                    # ✨ note_preference の構造化（カンマ区切り / | 区切りに対応）
                    note_dict = {}
                    for note_pair in re.split(r'[|,]', note_text):
                        if '：' in note_pair:
                            key, level = note_pair.split('：', 1)
                            key = key.strip()
                            level = level.strip()
                            if key and level:
                                note_dict[key] = level
                    parsed['staff'][staff_name]['note_preference'] = note_dict

                elif any(g in sub for g in ALLOWED_GENRES):
                    tokens = sub.split()
                    print("[DEBUG] tokens=", tokens)
                    for token in tokens:
                        base = token[:-1].strip()
                        symbol = token[-1]
                        print(f"[DEBUG] base={base}, symbol={symbol}")
                        if base in ALLOWED_GENRES:
                            parsed['staff'][staff_name]['ジャンル'][base] = symbol

                else:
                    if parsed['staff'][staff_name]['特性']:
                        parsed['staff'][staff_name]['特性'] += f"|{sub}"
                    else:
                        parsed['staff'][staff_name]['特性'] = sub

    return parsed
