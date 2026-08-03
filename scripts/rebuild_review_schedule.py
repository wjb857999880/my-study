#!/usr/bin/env python3
"""重新计算所有知识点 next_review，在 2027-01-01 前均匀分布（每条目约 2.0 有效学习日间隔）。"""
from pathlib import Path
import datetime as dt
from collections import defaultdict

SKILLS_DIR = Path("/Users/wujiabao/my_projects/my-study/skills")
LEVEL_ORDER = ["了解", "熟悉", "掌握", "精通"]
LEVEL_VALUE = {name: i + 1 for i, name in enumerate(LEVEL_ORDER)}
TODAY = dt.date(2026, 8, 3)
DEADLINE = dt.date(2027, 1, 1)

total_days = (DEADLINE - TODAY).days + 1
wd = sum(1 for i in range(total_days) if (TODAY + dt.timedelta(days=i)).weekday() < 5)
we = total_days - wd
total_study = wd + we * 0.6
INTERVAL = total_study / 66

def study_to_date(start, study_days):
    d = start
    remaining = study_days
    while remaining > 0.001:
        d += dt.timedelta(days=1)
        remaining -= 1.0 if d.weekday() < 5 else 0.6
    return d

def parse_fm(text):
    lines = text.splitlines()
    fm_start = next((i for i, l in enumerate(lines) if l.strip() == "---"), None)
    if fm_start is None:
        return None, None, {}
    fm_end = next((i for i, l in enumerate(lines[fm_start+1:], fm_start+1) if l.strip() == "---"), None)
    if fm_end is None:
        return None, None, {}
    fields = {}
    for raw in lines[fm_start+1:fm_end]:
        s = raw.strip()
        if not s or s.startswith(("#", "-")) or ":" not in s:
            continue
        k, _, v = s.partition(":")
        fields[k.strip()] = v.strip()
    return fm_start, fm_end, fields

# Collect entries
entries = []
for md in sorted(SKILLS_DIR.rglob("*.md")):
    if md.name == "_index.md":
        continue
    fm_start, fm_end, fields = parse_fm(md.read_text(encoding="utf-8"))
    if fm_start is None or not fields.get("title"):
        continue
    lv = LEVEL_VALUE.get(fields.get("level", ""), 0)
    tv = LEVEL_VALUE.get(fields.get("target", ""), 0)
    gap = (tv - lv) if (tv and lv) else 0
    entries.append({
        "path": md,
        "title": fields["title"],
        "domain": fields.get("domain", ""),
        "gap": gap,
        "is_assessed": bool(fields.get("last_assessed")),
        "fm_start": fm_start,
        "fm_end": fm_end,
    })

print(f"读取了 {len(entries)} 个条目")

# Sort by gap desc
sorted_entries = sorted(entries, key=lambda x: (-x["gap"], x["title"]))
for i, e in enumerate(sorted_entries):
    e["raw_date"] = study_to_date(TODAY, INTERVAL * i)

# Handle overflow
by_date = defaultdict(list)
for e in sorted_entries:
    by_date[e["raw_date"]].append(e)

overflow = []
for d in list(by_date.keys()):
    if d > DEADLINE:
        overflow.extend(by_date.pop(d))
overflow.extend(by_date.pop(DEADLINE, []))

if overflow:
    d = DEADLINE - dt.timedelta(days=1)
    oi = 0
    while oi < len(overflow) and d >= TODAY:
        if len(by_date.get(d, [])) < 2 and d.weekday() < 5:
            overflow[oi]["raw_date"] = d
            by_date[d].append(overflow[oi])
            oi += 1
        d -= dt.timedelta(days=1)
        while d.weekday() >= 5 and d >= TODAY:
            d -= dt.timedelta(days=1)

# Write back
changed = 0
for e in entries:
    d = e.get("raw_date", DEADLINE)
    if d > DEADLINE:
        d = DEADLINE
    lines = e["path"].read_text(encoding="utf-8").splitlines()
    updated = False
    for i in range(e["fm_start"] + 1, e["fm_end"]):
        s = lines[i].strip()
        if not s or s.startswith(("#", "-")) or ":" not in s:
            continue
        k, _, _ = s.partition(":")
        if k.strip() == "next_review":
            lines[i] = f"next_review: {d.isoformat()}"
            updated = True
            break
    if updated:
        e["path"].write_text("\n".join(lines), encoding="utf-8")
        changed += 1

print(f"更新了 {changed}/{len(entries)} 个文件")

# Print schedule
final = defaultdict(list)
for e in sorted_entries:
    final[e["raw_date"]].append(e["title"])

print("\n复习计划（🟢工作日 🔵周末）：")
print("=" * 60)
cur = TODAY
while cur <= DEADLINE:
    if cur in final:
        icon = "🟢" if cur.weekday() < 5 else "🔵"
        dn = ["一", "二", "三", "四", "五", "六", "日"][cur.weekday()]
        print(f"\n{icon} {cur.isoformat()}（周{dn}）")
        for t in sorted(final[cur]):
            print(f"   • {t}")
    cur += dt.timedelta(days=1)

multi = {d: items for d, items in final.items() if len(items) > 1}
past = sum(1 for d in final if d > DEADLINE)
print(f"\n截止日后溢出: {past}条 | 同日多条目: {len(multi)}天")
if past == 0 and not multi:
    print("✅ 全部均匀分布，无堆积")
