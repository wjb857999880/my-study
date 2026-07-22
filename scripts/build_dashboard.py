#!/usr/bin/env python3
"""扫描 skills/ 下的知识点 Markdown，生成 DASHBOARD.md 总看板。

零依赖：手写简易 YAML frontmatter 解析（仅扁平 key: value 与 list）。
仅读 skills/**/*.md（跳过 _index.md），仅写 DASHBOARD.md，不改任何知识点文件。
"""

from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

# --- 配置 ---
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
DASHBOARD_FILE = REPO_ROOT / "DASHBOARD.md"

LEVEL_ORDER = ["了解", "熟悉", "掌握", "精通"]
LEVEL_VALUE = {name: i + 1 for i, name in enumerate(LEVEL_ORDER)}  # 了解=1..精通=4
VALUE_LEVEL = {v: k for k, v in LEVEL_VALUE.items()}
IMPORTANCE_ORDER = ["高", "中", "低"]
REQUIRED_FIELDS = ["title", "domain", "level", "target",
                   "importance", "last_reviewed", "next_review"]
DATE_FORMAT = "%Y-%m-%d"

DOMAIN_LABEL = {
    "01-语言": "语言",
    "02-框架与Jetpack": "框架与Jetpack",
    "03-UI": "UI",
    "04-性能优化": "性能优化",
    "05-架构": "架构",
    "06-系统底层": "系统底层",
    "07-工程化": "工程化",
    "08-网络与存储": "网络与存储",
}


def parse_frontmatter(text):
    """解析 Markdown 顶部 --- 之间的 frontmatter（扁平 key: value 与 list）。

    返回 (fields_dict, parse_errors)。
    """
    fields = {}
    errors = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fields, ["缺少 frontmatter 起始标记 '---'"]
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return fields, ["frontmatter 缺少结束标记 '---'"]
    fm_lines = lines[1:end]

    current_list_key = None
    for raw in fm_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key is not None:
            fields[current_list_key].append(stripped[2:].strip())
            continue
        if ":" not in stripped:
            errors.append("frontmatter 行无法解析: '%s'" % raw)
            current_list_key = None
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            fields[key] = [x.strip() for x in inner.split(",") if x.strip()] if inner else []
            current_list_key = None
            continue
        if value == "":
            fields[key] = []
            current_list_key = key
            continue
        fields[key] = value
        current_list_key = None
    return fields, errors


def _is_date(s):
    try:
        _dt.datetime.strptime(str(s), DATE_FORMAT)
        return True
    except (ValueError, TypeError):
        return False


def validate(fields, source):
    """返回该知识点的校验告警列表（空 = 无问题）。"""
    warns = []
    for f in REQUIRED_FIELDS:
        v = fields.get(f)
        if f not in fields or v == [] or (isinstance(v, str) and not v.strip()):
            warns.append("缺必填字段: %s" % f)
    if fields.get("level") and fields["level"] not in LEVEL_VALUE:
        warns.append("level 非法: %s（应为 %s）" % (fields["level"], LEVEL_ORDER))
    if fields.get("target") and fields["target"] not in LEVEL_VALUE:
        warns.append("target 非法: %s（应为 %s）" % (fields["target"], LEVEL_ORDER))
    if fields.get("importance") and fields["importance"] not in IMPORTANCE_ORDER:
        warns.append("importance 非法: %s（应为 %s）" % (fields["importance"], IMPORTANCE_ORDER))
    for f in ("last_reviewed", "next_review", "last_assessed"):
        v = fields.get(f)
        if v and not _is_date(v):
            warns.append("%s 日期格式错误: %s（应为 YYYY-MM-DD）" % (f, v))
    if fields.get("domain") and source.parent.name != fields["domain"]:
        warns.append("domain(%s) 与文件所在目录(%s)不一致"
                     % (fields["domain"], source.parent.name))
    return warns


def load_entries():
    """扫描 skills/，返回 (entries, global_warns)。每个 entry 含解析字段 + _meta。"""
    entries = []
    global_warns = []
    if not SKILLS_DIR.exists():
        return entries, ["skills/ 目录不存在: %s" % SKILLS_DIR]
    for md in sorted(SKILLS_DIR.rglob("*.md")):
        if md.name == "_index.md":
            continue
        text = md.read_text(encoding="utf-8")
        fields, parse_errors = parse_frontmatter(text)
        entry = dict(fields)
        entry["_source"] = md
        entry["_warns"] = parse_errors + validate(fields, md)
        entries.append(entry)
        title = entry.get("title") or md.name
        global_warns.extend("%s: %s" % (title, w) for w in entry["_warns"])
    return entries, global_warns


def _level_value(entry, key):
    v = entry.get(key)
    return LEVEL_VALUE.get(v, 0) if isinstance(v, str) else 0


def review_status(entry, today):
    v = entry.get("next_review")
    if not v or not _is_date(v):
        return "未知"
    d = _dt.datetime.strptime(v, DATE_FORMAT).date()
    if d < today:
        return "逾期"
    if d == today:
        return "该复习"
    return "正常"


def render(entries, global_warns, today):
    lines = []
    lines.append("<!-- AUTO-GENERATED by scripts/build_dashboard.py -->")
    lines.append("<!-- 请勿手工编辑；运行 python3 scripts/build_dashboard.py 重新生成 -->")
    lines.append("")
    lines.append("# 技能熟练度总看板")
    lines.append("")
    lines.append("> 数据日期：%s　|　知识点总数：%d" % (today.isoformat(), len(entries)))
    lines.append("")

    # 校验告警
    if global_warns:
        lines.append("## ⚠️ 校验告警")
        lines.append("")
        for w in global_warns:
            lines.append("- %s" % w)
    else:
        lines.append("## ✅ 校验通过（无告警）")
    lines.append("")

    # 考核进度
    assessed = [e for e in entries
                if e.get("last_assessed") and _is_date(e.get("last_assessed"))]
    pending = [e for e in entries if e not in assessed]
    lines.append("## 考核进度")
    lines.append("")
    lines.append("> 已考核 %d / 待考核 %d（待考核默认为了解）"
                 % (len(assessed), len(pending)))
    lines.append("")
    if pending:
        lines.append("**待考核清单：**")
        lines.append("")
        lines.append("| 知识点 | 领域 | 目标 |")
        lines.append("|--------|------|------|")
        for e in sorted(pending, key=lambda e: e.get("title") or ""):
            dom = DOMAIN_LABEL.get(e.get("domain", ""), e.get("domain", "") or "?")
            lines.append("| %s | %s | %s |"
                         % (e.get("title", "?"), dom, e.get("target", "?")))
        lines.append("")
    else:
        lines.append("_（所有知识点均已考核）_")
        lines.append("")

    total = len(entries)

    # 1. 熟练度分布
    lines.append("## 1. 熟练度分布")
    lines.append("")
    lines.append("| 档位 | 数量 | 占比 |")
    lines.append("|------|------|------|")
    for lvl in LEVEL_ORDER:
        n = sum(1 for e in entries if e.get("level") == lvl)
        pct = ("%.0f%%" % (n / total * 100)) if total else "0%"
        lines.append("| %s | %d | %s |" % (lvl, n, pct))
    lines.append("")
    lines.append("> 注：含待考核知识点（默认为了解）；level 仅考核后由 AI 判定。")
    lines.append("")

    # 2. 领域分布
    lines.append("## 2. 领域分布")
    lines.append("")
    lines.append("| 领域 | 知识点数 | 平均熟练度 |")
    lines.append("|------|----------|-----------|")
    for d in DOMAIN_LABEL:
        items = [e for e in entries if e.get("domain") == d]
        if not items:
            continue
        vals = [_level_value(e, "level") for e in items]
        vals = [v for v in vals if v]
        if vals:
            avg = sum(vals) / len(vals)
            avg_label = VALUE_LEVEL.get(int(avg + 0.5), "—")
            lines.append("| %s | %d | %s（%.1f） |"
                         % (DOMAIN_LABEL[d], len(items), avg_label, avg))
        else:
            lines.append("| %s | %d | — |" % (DOMAIN_LABEL[d], len(items)))
    lines.append("")

    # 3. 复习清单
    lines.append("## 3. 复习清单")
    lines.append("")
    groups = {"逾期": [], "该复习": [], "正常": []}
    for e in entries:
        groups.setdefault(review_status(e, today), []).append(e)
    icon = {"逾期": "🚨", "该复习": "⏰", "正常": "✅"}
    for status in ("逾期", "该复习", "正常"):
        items = sorted(groups.get(status, []), key=lambda e: e.get("next_review") or "")
        lines.append("### %s %s（%d）" % (icon.get(status, ""), status, len(items)))
        lines.append("")
        if not items:
            lines.append("_（无）_")
            lines.append("")
            continue
        lines.append("| 知识点 | 领域 | 现状 | 下次复习 |")
        lines.append("|--------|------|------|----------|")
        for e in items:
            dom = DOMAIN_LABEL.get(e.get("domain", ""), e.get("domain", "") or "?")
            lines.append("| %s | %s | %s | %s |"
                         % (e.get("title", "?"), dom, e.get("level", "?"),
                            e.get("next_review", "?")))
        lines.append("")

    # 4. 目标进度
    lines.append("## 4. 目标进度（level < target）")
    lines.append("")
    gaps = []
    for e in entries:
        lv = _level_value(e, "level")
        tv = _level_value(e, "target")
        if lv and tv and lv < tv:
            gaps.append((e, tv - lv))
    if not gaps:
        lines.append("_（所有知识点均已达成目标，或未设目标）_")
        lines.append("")
    else:
        lines.append("| 知识点 | 领域 | 现状 | 目标 | 差距 |")
        lines.append("|--------|------|------|------|------|")
        for e, gap in sorted(gaps, key=lambda x: -x[1]):
            dom = DOMAIN_LABEL.get(e.get("domain", ""), e.get("domain", "") or "?")
            lines.append("| %s | %s | %s | %s | %d 档 |"
                         % (e.get("title", "?"), dom, e.get("level", "?"),
                            e.get("target", "?"), gap))
        lines.append("")

    return "\n".join(lines) + "\n"


def main():
    today = _dt.date.today()
    entries, global_warns = load_entries()
    content = render(entries, global_warns, today)
    DASHBOARD_FILE.write_text(content, encoding="utf-8")
    print("已生成 %s" % DASHBOARD_FILE.relative_to(REPO_ROOT))
    print("知识点数：%d；告警：%d" % (len(entries), len(global_warns)))
    if global_warns:
        print("告警明细：")
        for w in global_warns:
            print("  - %s" % w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
