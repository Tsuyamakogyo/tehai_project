# === assignment_core.py ===

GENRE_SCORE_MAP = {'◎': 3, '○': 2, '△': 1, '✕': 0}
REVERSE_GENRE_SCORE_MAP = {v: k for k, v in GENRE_SCORE_MAP.items()}

def assign_priority_staff(projects, staff_profiles):
    """
    事前に最優先・優先スタッフを配置
    """
    used_staff_morning = set()
    used_staff_afternoon = set()

    for proj in projects:
        proj.setdefault('assigned_morning', [])
        proj.setdefault('assigned_afternoon', [])

        for staff in staff_profiles:
            note_pref = staff.get('note_preference', {})
            if proj['customer'] in note_pref:
                preference_level = note_pref[proj['customer']]
                print(f"[DEBUG] {staff['name']} is {preference_level} for {proj['customer']}")
                
                if preference_level == '最優先':
                    # 最優先スタッフを午前または午後に配置
                    if proj['shift'] == 'morning' and staff['am_ok'] and staff['name'] not in used_staff_morning:
                        used_staff_morning.add(staff['name'])
                        proj['assigned_morning'].append(staff)
                        print(f"[DEBUG] Assigned {staff['name']} to morning (最優先) for project {proj['project_name']}")

                    elif proj['shift'] == 'afternoon' and staff['pm_ok'] and staff['name'] not in used_staff_afternoon:
                        used_staff_afternoon.add(staff['name'])
                        proj['assigned_afternoon'].append(staff)
                        print(f"[DEBUG] Assigned {staff['name']} to afternoon (最優先) for project {proj['project_name']}")
                
                elif preference_level == '優先':
                    # 優先スタッフを午前または午後に配置
                    if proj['shift'] == 'morning' and staff['am_ok'] and staff['name'] not in used_staff_morning:
                        used_staff_morning.add(staff['name'])
                        proj['assigned_morning'].append(staff)
                        print(f"[DEBUG] Assigned {staff['name']} to morning (優先) for project {proj['project_name']}")

                    elif proj['shift'] == 'afternoon' and staff['pm_ok'] and staff['name'] not in used_staff_afternoon:
                        used_staff_afternoon.add(staff['name'])
                        proj['assigned_afternoon'].append(staff)
                        print(f"[DEBUG] Assigned {staff['name']} to afternoon (優先) for project {proj['project_name']}")

    return used_staff_morning, used_staff_afternoon


def run_assignment_engine(projects, staff_profiles, genre_map):
    assignments = []
    
    # スタッフの午前シフト・午後シフトの割り当て状況を追跡するセットを定義
    used_staff_morning = set()
    used_staff_afternoon = set()

    # full_day_staffの定義（午前と午後両方に対応できるスタッフ）
    full_day_staff = [s for s in staff_profiles if s['am_ok'] and s['pm_ok']]  
    
    # 最優先・優先スタッフを事前に配置
    used_staff_morning, used_staff_afternoon = assign_priority_staff(projects, staff_profiles)

    print("[PASS2] Start - Normal assignment engine")
    projects = sort_projects_by_fit(projects, staff_profiles, genre_map)

    for proj in projects:
        shift = proj['shift']
        required_morning = proj['required_morning']
        required_afternoon = proj['required_afternoon']
        assigned_morning = proj.get('assigned_morning', [])
        assigned_afternoon = proj.get('assigned_afternoon', [])
        
        # スタッフカテゴリーの定義 (午前、午後、終日)
        morning_only_staff = [s for s in staff_profiles if s['am_ok'] and not s['pm_ok']]
        afternoon_only_staff = [s for s in staff_profiles if not s['am_ok'] and s['pm_ok']]
        full_day_staff = [s for s in staff_profiles if s['am_ok'] and s['pm_ok']]

        # ==================
        # morning only staff
        # ==================
        if shift == 'morning':
            morning_candidates = prioritize_by_genre(morning_only_staff, proj['customer'], genre_map)
            for staff in morning_candidates:
                if staff['name'] not in used_staff_morning and len(assigned_morning) < required_morning:
                    assigned_morning.append(staff)
                    used_staff_morning.add(staff['name'])
                    print(f"[DEBUG] Assigned {staff['name']} to morning for project {proj['project_name']}")

        # ==================
        # afternoon only staff
        # ==================
        elif shift == 'afternoon':
            afternoon_candidates = prioritize_by_genre(afternoon_only_staff, proj['customer'], genre_map)
            for staff in afternoon_candidates:
                if staff['name'] not in used_staff_afternoon and len(assigned_afternoon) < required_afternoon:
                    assigned_afternoon.append(staff)
                    used_staff_afternoon.add(staff['name'])
                    print(f"[DEBUG] Assigned {staff['name']} to afternoon for project {proj['project_name']}")

        # ==================
        # full_day staff (after morning/afternoon)
        # ==================
        elif shift == 'full_day':
            print(f"[DEBUG] Before assigning full_day: used_staff_morning={used_staff_morning}, used_staff_afternoon={used_staff_afternoon}")
            
            print(f"[DEBUG] Project: {proj['project_name']} (shift={shift})")

            full_day_candidates = prioritize_by_genre(full_day_staff, proj['customer'], genre_map)
            print(f"[DEBUG] Top full_day_candidates: {[c['name'] for c in full_day_candidates[:5]]}")
            
            # 午前補充
            for staff in full_day_candidates:
                if staff['name'] not in used_staff_morning and staff['name'] not in used_staff_afternoon and len(assigned_morning) < required_morning:
                    assigned_morning.append(staff)
                    used_staff_morning.add(staff['name'])  # 午前のみ used に追加
                    print(f"[DEBUG] Assigned {staff['name']} to morning for project {proj['project_name']}")

            # 午後補充
            for staff in full_day_candidates:
                if staff['name'] not in used_staff_afternoon and len(assigned_afternoon) < required_afternoon:
                    assigned_afternoon.append(staff)
                    used_staff_afternoon.add(staff['name'])  # 午後のみ used に追加
                    print(f"[DEBUG] Assigned {staff['name']} to afternoon for project {proj['project_name']}")

            print(f"[DEBUG] After assigning full_day: used_staff_morning={used_staff_morning}, used_staff_afternoon={used_staff_afternoon}")

        # ==================
        # 午前シフトに終日スタッフを配置 (午前のみusedにする)
        # ==================
        if shift == 'morning':
            # 午前シフトに終日スタッフを配置 (午前のみusedにする)
            full_day_candidates = prioritize_by_genre(full_day_staff, proj['customer'], genre_map)
            for staff in full_day_candidates:
                if staff['name'] not in used_staff_morning and len(assigned_morning) < required_morning:
                    assigned_morning.append(staff)
                    used_staff_morning.add(staff['name'])  # 午前のみ used に追加
                    print(f"[DEBUG] Assigned {staff['name']} to morning for project {proj['project_name']}")

        # ==================
        # 午後シフトに終日スタッフを配置 (午後のみusedにする)
        # ==================
        if shift == 'afternoon':
            # 午後シフトに終日スタッフを配置 (午後のみusedにする)
            full_day_candidates = prioritize_by_genre(full_day_staff, proj['customer'], genre_map)
            for staff in full_day_candidates:
                if staff['name'] not in used_staff_afternoon and len(assigned_afternoon) < required_afternoon:
                    assigned_afternoon.append(staff)
                    used_staff_afternoon.add(staff['name'])  # 午後のみ used に追加
                    print(f"[DEBUG] Assigned {staff['name']} to afternoon for project {proj['project_name']}")

        # ==================
        # 終日シフトに午前スタッフを配置
        # ==================
        if shift == 'full_day':
            morning_candidates = prioritize_by_genre(morning_only_staff, proj['customer'], genre_map)
            for staff in morning_candidates:
                if staff['name'] not in used_staff_morning and len(assigned_morning) < required_morning:
                    assigned_morning.append(staff)
                    used_staff_morning.add(staff['name'])
                    print(f"[DEBUG] Assigned {staff['name']} to morning (full_day project) for project {proj['project_name']}")

        # ==================
        # 終日シフトに午後スタッフを配置
        # ==================
        if shift == 'full_day':
            afternoon_candidates = prioritize_by_genre(afternoon_only_staff, proj['customer'], genre_map)
            for staff in afternoon_candidates:
                if staff['name'] not in used_staff_afternoon and len(assigned_afternoon) < required_afternoon:
                    assigned_afternoon.append(staff)
                    used_staff_afternoon.add(staff['name'])
                    print(f"[DEBUG] Assigned {staff['name']} to afternoon (full_day project) for project {proj['project_name']}")

        # === 結果を assignments に格納 ===
        assignments.append({
            'project_name': proj['project_name'],
            'customer': proj['customer'],
            'time': proj['start_time'],
            'shift': shift,
            'required_morning': required_morning,
            'required_afternoon': required_afternoon,
            'assigned_morning': assigned_morning,
            'assigned_afternoon': assigned_afternoon
        })

    print("[PASS2] Done.\n")
    return assignments

def prioritize_by_genre(candidates, customer_name, genre_map, project_name=None):
    """
    指定ジャンルに対して最適なスタッフを優先順位でソートする。
    スキル（◎→3）や限定適性、特性ワードによるブーストを考慮。
    顧客名・ジャンル名・現場名をnote_preferenceにマッチさせる。
    """
    import json
    import re

    def normalize(s):
        # 仮称や記号、スペースを除去し、小文字化する
        s = re.sub(r'\(仮称\)', '', s)  # (仮称)削除
        s = re.sub(r'[（）\(\)\s・\-：:,、]', '', s)  # 記号・空白除去
        s = s.lower()
        # よく使われる略称や省略表現の補完（必要に応じて追加可能）
        s = s.replace('三郷物流開発計画', '三郷物流')
        return s

    with open("config/rules.json", encoding="utf-8") as f:
        rules = json.load(f)
    preference_score_map = rules.get("preference_score_map", {"最優先": 100, "優先": 50})

    genre = genre_map.get(customer_name, "")

    # フィルタ：ジャンルスキルありの人優先（なければ全員）
    filtered_candidates = [s for s in candidates if genre and s['skills'].get(genre, 0) > 0]
    if not filtered_candidates:
        filtered_candidates = candidates

    def sort_key(staff):
        skill_val = staff['skills'].get(genre, 0)
        total_top_skills = sum(1 for v in staff['skills'].values() if v == 3)
        is_exclusive = skill_val == 3 and total_top_skills == 1
        trend_val = staff.get('trend_scores', {}).get(genre, 0)
        lead_val = staff.get('leadership_score', 0)

        note_pref = staff.get('note_preference', {})
        note_boost = 0

        # 顧客名 / 現場名 / ジャンル名 をマッチ対象にする
        match_targets = [customer_name]
        if project_name:
            match_targets.append(project_name)

        norm_targets = [normalize(t) for t in match_targets if t]

        # 顧客名や現場名に対する最優先・優先ブーストをマッチさせる
        for key, pref_level in note_pref.items():
            if key and key.strip():
                norm_key = normalize(key)
                if any(norm_key in norm_target for norm_target in norm_targets):
                    # 顧客名や現場名にマッチする場合、ジャンルに関係なく最優先・優先を適用
                    note_boost += preference_score_map.get(pref_level, 0)

        if note_boost > 0:
            print(f"[DEBUG] note_boost={note_boost} for {staff['name']} (genre={genre}, project={project_name})")

        # ジャンル特性に基づくブースト（例えば、スキルが◎の人など）を追加
        exclusive_boost = 100 if is_exclusive else 0

        print(f"[SCORE BREAKDOWN] {staff['name']}: "
            f"exclusive={exclusive_boost}, "
            f"note_boost={note_boost}, "
            f"skill_val={skill_val * 3}, "
            f"trend_val={trend_val}, "
            f"lead_val={lead_val}")

        return (
            exclusive_boost + note_boost,  # note_boostを優先
            skill_val * 3,  # skill_valに基づくスコア
            trend_val,  # トレンドスコア
            lead_val  # リーダーシップスコア
        )

    sorted_list = sorted(filtered_candidates, key=sort_key, reverse=True)
    print(f"[DEBUG] Sorted candidate list for {customer_name} ({project_name}): {[c['name'] for c in sorted_list]}")
    return sorted_list

def sort_projects_by_fit(projects, staff_profiles, genre_map):
    def project_score(project):
        genre = genre_map.get(project['customer'], '')
        if not genre:
            print(f"[DEBUG] No genre found for customer {project['customer']}")
            return 0
        count = sum(1 for s in staff_profiles if s['skills'].get(genre, 0) == 3)
        print(f"[DEBUG] Project '{project['project_name']}' (genre={genre}) has {count} staff with ◎")
        return -count
    
    sorted_projects = sorted(projects, key=project_score)
    
    print("\n[DEBUG] Sorted project list (◎少ない順):")
    for p in sorted_projects:
        genre = genre_map.get(p['customer'], '')
        count = sum(1 for s in staff_profiles if s['skills'].get(genre, 0) == 3)
        print(f"  - {p['project_name']} [{genre}]：◎={count}人")

    return sorted_projects