# === data_formatter.py ===

def format_output(assignments, summary=None):
    output_lines = []

    if summary:
        output_lines.append(f"手配検討日：{summary.get('date', '')}")
        output_lines.append(f"必要＞ {summary.get('required', '')}")
        output_lines.append(f"出勤＞ {summary.get('available', '')}")
        output_lines.append("")  # 空行

    output_lines.append("🔴終日🔴")
    for a in assignments:
        if a['shift'] == 'full_day':
            output_lines.append(f"[{a['customer']}] {a['project_name']}")
            output_lines.append(f"{a['time']}")
            output_lines.append(make_slash_line("午前", a['required_morning'], a['assigned_morning']))
            output_lines.append(make_slash_line("午後", a['required_afternoon'], a['assigned_afternoon']))

    output_lines.append("\n🔵午前🔵")
    for a in assignments:
        if a['shift'] == 'morning':
            output_lines.append(f"[{a['customer']}] {a['project_name']}")
            output_lines.append(f"{a['time']}")
            output_lines.append(make_slash_line("午前", a['required_morning'], a['assigned_morning']))

    output_lines.append("\n🟠午後🟠")
    for a in assignments:
        if a['shift'] == 'afternoon':
            output_lines.append(f"[{a['customer']}] {a['project_name']}")
            output_lines.append(f"{a['time']}")
            output_lines.append(make_slash_line("午後", a['required_afternoon'], a['assigned_afternoon']))

    return "\n".join(output_lines)


def make_slash_line(title, required, assigned_list):
    assigned_strs = [
        f"{s.get('am_symbol','')}{s.get('name','')}" if title == "午前" else f"{s.get('pm_symbol','')}{s.get('name','')}" 
        for s in assigned_list if s.get('name')
    ]
    leftover_count = required - len(assigned_strs)
    if leftover_count < 0:
        leftover_count = 0
    placeholders = assigned_strs + ["" for _ in range(leftover_count)]
    return f"{title} {required}名：{'/'.join(placeholders)}/|"


def parse_output_result(output_text):
    rows = []
    tehai_date = None
    current_project = None
    current_customer = None
    current_time = None
    current_shift = None

    for line in output_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("手配検討日："):
            tehai_date = line.replace("手配検討日：", "").strip()

        elif line in ["🔴終日🔴", "🔵午前🔵", "🟠午後🟠"]:
            if "終日" in line:
                current_shift = "終日"
            elif "午前" in line:
                current_shift = "午前"
            elif "午後" in line:
                current_shift = "午後"

        elif line.startswith("[") and "]" in line:
            try:
                customer = line.split("]")[0].replace("[", "").strip()
                project = line.split("]")[1].strip()
                current_customer = customer
                current_project = project
            except Exception as e:
                print("案件行解析エラー：", e)

        elif ":" in line and ("午前" in line or "午後" in line):
            try:
                title_part, names_part = line.split("：", 1)
                shift = title_part.strip().split()[0]  # "午前" または "午後"
                staff_entries = [n.strip() for n in names_part.split("/") if n.strip() and n.strip() != "|"]

                for s in staff_entries:
                    mark = s[0] if s[0] in ["◎", "○", "●"] else ""
                    name = s[1:] if mark else s
                    rows.append({
                        "日付": tehai_date,
                        "案件名": current_project,
                        "顧客名": current_customer,
                        "ジャンル": "",
                        "シフト": shift,
                        "スタッフ名": name,
                        "記号": mark
                    })
            except Exception as e:
                print("担当行解析エラー：", e)

    return rows


