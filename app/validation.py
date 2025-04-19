# validator.py

def validate_assignments(assignments, input_data):
    valid = True
    messages = []

    used_names_morning = set()
    used_names_afternoon = set()

    for a in assignments:
        # 午前の重複チェック
        for s in a['assigned_morning']:
            name = s['name']
            mark = s['am_symbol']  # 修正: 'shift_mark' を 'am_symbol' に変更
            if name and name in used_names_morning:
                valid = False
                messages.append(f"❌ {a['project_name']} 午前 で {name} ({mark}) が重複配置")
            used_names_morning.add(name)

        # 午後の重複チェック
        for s in a['assigned_afternoon']:
            name = s['name']
            mark = s['pm_symbol']  # 修正: 'shift_mark' を 'pm_symbol' に変更
            if name and name in used_names_afternoon:
                valid = False
                messages.append(f"❌ {a['project_name']} 午後 で {name} ({mark}) が重複配置")
            used_names_afternoon.add(name)

        # 必要数 vs 実際割当数
        if len([s for s in a['assigned_morning'] if s['name']]) > a['required_morning']:
            valid = False
            messages.append(f"❌ {a['project_name']} 午前で過剰割当")
        if len([s for s in a['assigned_afternoon'] if s['name']]) > a['required_afternoon']:
            valid = False
            messages.append(f"❌ {a['project_name']} 午後で過剰割当")

    if valid:
        messages.append("✅ 検算OK：重複なし・人数整合あり")

    return "\n".join(messages)
