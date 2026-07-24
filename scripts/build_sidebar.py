#!/usr/bin/env python3
"""扫描 skills/ 生成 docsify 的 _sidebar.md(按领域分组的左侧导航)。

零依赖。读取每个知识点的 frontmatter title 作为显示名;读不到则用文件名。
运行:python3 scripts/build_sidebar.py
"""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
OUT = REPO_ROOT / "_sidebar.md"


def parse_title(md: Path) -> str:
    """读 frontmatter 的 title 字段;读不到就用文件名主干。"""
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return md.stem
    if not text.startswith("---"):
        return md.stem
    # frontmatter 是第一个 --- 与第二个 --- 之间
    body = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("title:"):
            return line[len("title:"):].strip().strip('"').strip("'")
    return md.stem


def main() -> None:
    lines = [
        "- 📊 [总看板](DASHBOARD.md)",
        "- 📖 [项目说明](README.md)",
        "",
    ]
    domains = sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir())
    total = 0
    for d in domains:
        files = sorted(d.glob("*.md"))
        if not files:
            continue
        lines.append(f"- **{d.name}**")
        for f in files:
            total += 1
            title = parse_title(f)
            rel = f"skills/{d.name}/{f.name}"
            lines.append(f"  - [{title}]({rel})")
        lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成 _sidebar.md({len(domains)} 领域 / {total} 篇)")


if __name__ == "__main__":
    main()
