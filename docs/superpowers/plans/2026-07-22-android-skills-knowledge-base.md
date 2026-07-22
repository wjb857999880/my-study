# Android 技术知识库 + 熟练度台账 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建一个纯 Markdown 的 Android 技术知识库 + 熟练度台账：8 大领域目录、知识点模板、熟练度四档标准、示范内容，以及一个零依赖 Python 脚本生成总看板。

**Architecture:** 文档为主（目录 + 模板 + 示范知识点 + 阶段目标），外加一个 `scripts/build_dashboard.py` 扫描 `skills/**/*.md` 的 frontmatter、校验、生成 `DASHBOARD.md`。脚本拆为纯函数（`parse_frontmatter` / `validate` / `review_status` / `render`）+ `main`，便于将来按需加测试；本期按 spec 第 11 节「YAGNI：不引入测试框架」，验证方式为**运行脚本 + 检查输出 + 内联 `python3 -c` 断言**。

**Tech Stack:** Markdown / YAML frontmatter（手写解析）/ Python3（零依赖，macOS 自带）/ Git。

**对应设计文档：** `docs/superpowers/specs/2026-07-22-android-skills-knowledge-base-design.md`

**执行分支：** `setup/android-skills-knowledge-base`（设计文档已在此分支提交）

---

## Task 1: 搭建目录骨架 + 写 README

**Files:**
- Create: `skills/01-语言/`, `skills/02-框架与Jetpack/`, `skills/03-UI/`, `skills/04-性能优化/`, `skills/05-架构/`, `skills/06-系统底层/`, `skills/07-工程化/`, `skills/08-网络与存储/`（各放 `.gitkeep`）
- Create: `templates/`, `scripts/`, `plans/`（各放 `.gitkeep`）
- Modify: `README.md`（当前仅占位内容，整体改写）

- [ ] **Step 1: 创建目录骨架**

```bash
mkdir -p skills/01-语言 skills/02-框架与Jetpack skills/03-UI skills/04-性能优化 \
         skills/05-架构 skills/06-系统底层 skills/07-工程化 skills/08-网络与存储 \
         templates scripts plans
```

- [ ] **Step 2: 各空目录放 `.gitkeep`（让 git 跟踪空目录）**

```bash
touch skills/01-语言/.gitkeep skills/02-框架与Jetpack/.gitkeep skills/03-UI/.gitkeep \
      skills/04-性能优化/.gitkeep skills/05-架构/.gitkeep skills/06-系统底层/.gitkeep \
      skills/07-工程化/.gitkeep skills/08-网络与存储/.gitkeep \
      templates/.gitkeep scripts/.gitkeep plans/.gitkeep
```

- [ ] **Step 3: 改写 `README.md` 为完整内容**

写入以下内容（完整覆盖：简介 / 目录结构 / 熟练度标准 / 新增知识点 / 生成看板 / 工作流 / 复习周期）：

````markdown
# Android 技术知识库 + 熟练度台账

个人 Android 开发技能的**分类管理 + 熟练度考察 + 学习进度长期跟进**。纯 Markdown，零系统、零依赖，能长期维护。

## 目录结构

```
my-study/
├── README.md                  # 本文件（说明 + 熟练度标准 + 使用方式）
├── DASHBOARD.md               # 总看板（脚本自动生成，勿手改）
├── skills/                    # 8 大技术领域，每个知识点一个 .md
│   ├── 01-语言/               ├── 02-框架与Jetpack/
│   ├── 03-UI/                 ├── 04-性能优化/
│   ├── 05-架构/               ├── 06-系统底层/
│   ├── 07-工程化/             └── 08-网络与存储/
├── plans/                     # 阶段目标/里程碑（每季度一个文件）
├── templates/
│   └── skill-template.md      # 新建知识点时复制此模板
└── scripts/
    └── build_dashboard.py     # 生成总看板
```

## 熟练度四档标准

| 档位 | 判定标准 |
|------|---------|
| **了解** | 知道是什么、解决什么问题，但未实操 |
| **熟悉** | 能照着文档/示例独立完成 |
| **掌握** | 能脱离文档独立开发并排查问题 |
| **精通** | 能做架构设计、性能优化、给别人讲明白 |

脚本内部数值映射：了解=1，熟悉=2，掌握=3，精通=4（用于计算平均熟练度、判断 `level < target`）。

## 新增一个知识点

1. 复制 `templates/skill-template.md` 到对应领域目录，命名 `主题-子主题.md`（如 `Kotlin-协程.md`）。
2. 填写 frontmatter（`title`/`domain`/`level`/`target`/`importance`/`last_reviewed`/`next_review` 必填）。
3. 正文至少写「自评依据」——为什么评这个 level，举一个做过的项目/排查过的问题。

## 生成总看板

```bash
python3 scripts/build_dashboard.py
```

生成 `DASHBOARD.md`，含：① 熟练度分布 ② 领域分布 ③ 复习清单（🚨逾期 / ⏰该复习 / ✅正常）④ 目标进度（level < target）。同时校验缺字段/非法枚举/错误日期并报警。

## 复习周期建议

复习后据此更新该文件的 `next_review`（level 越熟、间隔越长；可在文件里手动覆盖）：

| level | 建议下次复习间隔 |
|-------|----------------|
| 了解 | +30 天 |
| 熟悉 | +60 天 |
| 掌握 | +90 天 |
| 精通 | +180 天 |

## 长期跟进工作流

1. 学/复习一个知识点 → 更新对应 `.md`（`level`/`last_reviewed`/`next_review`/`自评依据`）。
2. 跑 `python3 scripts/build_dashboard.py` 刷新看板。
3. 看看「复习清单」安排本周复习内容。
4. 每季度在 `plans/` 立目标，学完勾选、达成后把对应 `level` 升上去。
````

- [ ] **Step 4: 验证目录与文件就位**

Run: `ls -d skills/*/ templates scripts plans && echo "---" && head -5 README.md`
Expected: 列出 8 个 `skills/` 子目录 + `templates` + `scripts` + `plans`，且 README 前几行是新内容（标题 + 简介）。

- [ ] **Step 5: 提交**

```bash
git add skills templates scripts plans README.md
git commit -m "feat: scaffold 8-domain structure and write README

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: 写知识点模板

**Files:**
- Create: `templates/skill-template.md`

- [ ] **Step 1: 写模板文件**

写入以下内容（frontmatter 字段与设计文档第 4.1 节一致，正文仅「自评依据」标★必填）：

````markdown
---
title: 知识点名称                # 必填，如 Kotlin 协程
domain: 01-语言                 # 必填，对应 skills/ 下的目录名
level: 熟悉                     # 必填，现状：了解/熟悉/掌握/精通
target: 掌握                    # 必填，目标：了解/熟悉/掌握/精通
importance: 高                  # 必填，优先级：高/中/低
last_reviewed: 2026-07-22       # 必填，上次自评/复习日期 YYYY-MM-DD
next_review: 2026-08-22         # 必填，下次复习日期 YYYY-MM-DD
tags: [标签1, 标签2]            # 可选
related: [关联知识点]           # 可选
---

# 知识点名称

## 概述
一两句话：是什么、解决什么问题。（按需）

## 自评依据  ★必填
为什么给自己评这个 level？举一个做过的项目 / 排查过的问题 / 能讲清的点，
说明它支撑当前 level、又差在哪所以不到更高一档。

## 核心原理 / 关键点
深挖时再补。

## 实践经验 / 踩坑
做过什么、遇到过什么问题。

## 待深入 / 下一步
- [ ] 下一步学习项

## 参考资料
- 链接
````

- [ ] **Step 2: 验证**

Run: `cat templates/skill-template.md | head -3`
Expected: 前三行是 `---`、`title: 知识点名称`、`domain: 01-语言`。

- [ ] **Step 3: 提交**

```bash
git add templates/skill-template.md
git commit -m "feat: add knowledge-point template

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: 创建 8 个示范知识点文件（每领域 1 个）

刻意让 8 个文件的 `level` / `target` / `next_review` 有变化，这样生成的看板能同时呈现：各档分布、领域分布、逾期/该复习/正常三组、以及 level<target 的目标进度。日期以 2026-07-22 为"今天"设定。

**Files:**
- Create: `skills/01-语言/Kotlin-协程.md`（熟悉→掌握，next_review 过去=逾期）
- Create: `skills/02-框架与Jetpack/Jetpack-Compose.md`（了解→掌握，正常）
- Create: `skills/03-UI/RecyclerView-缓存.md`（掌握→精通，next_review 今天=该复习）
- Create: `skills/04-性能优化/启动优化.md`（熟悉→掌握，正常）
- Create: `skills/05-架构/MVVM.md`（掌握→掌握，已达目标，不出现在目标进度）
- Create: `skills/06-系统底层/Binder-原理.md`（了解→掌握，next_review 过去=逾期）
- Create: `skills/07-工程化/Gradle-构建.md`（熟悉→熟悉，已达目标）
- Create: `skills/08-网络与存储/OkHttp-拦截器.md`（掌握→精通，正常）

- [ ] **Step 1: 写 `skills/01-语言/Kotlin-协程.md`**

````markdown
---
title: Kotlin 协程
domain: 01-语言
level: 熟悉
target: 掌握
importance: 高
last_reviewed: 2026-06-01
next_review: 2026-07-01
tags: [并发, 异步]
related: [RxJava, Handler]
---

# Kotlin 协程

## 概述
Kotlin 提供的轻量级异步/并发方案，用 suspend 函数把异步代码写成同步样式。

## 自评依据  ★必填
在 XX 项目里用协程 + Retrofit 做过网络请求，能讲清结构化并发和作用域取消，
但没系统读过调度器（Dispatcher）源码、也没在复杂并发场景排过障，所以是"熟悉"非"掌握"。

## 待深入 / 下一步
- [ ] 读 suspend 的 CPS 原理
- [ ] 做一个 Flow 实战
````

- [ ] **Step 2: 写 `skills/02-框架与Jetpack/Jetpack-Compose.md`**

````markdown
---
title: Jetpack Compose
domain: 02-框架与Jetpack
level: 了解
target: 掌握
importance: 高
last_reviewed: 2026-07-10
next_review: 2026-08-10
tags: [UI, 声明式]
related: [RecyclerView]
---

# Jetpack Compose

## 概述
Android 官方声明式 UI 框架，用 Kotlin 函数描述界面，替代传统 View 体系。

## 自评依据  ★必填
跟过几个 Demo、知道 Composable/remember/状态提升的概念，但没在真实项目落地过，
也没处理过复杂列表性能与重组问题，所以是"了解"。

## 待深入 / 下一步
- [ ] 在小项目里用 Compose 重写一个页面
````

- [ ] **Step 3: 写 `skills/03-UI/RecyclerView-缓存.md`**

````markdown
---
title: RecyclerView 四级缓存
domain: 03-UI
level: 掌握
target: 精通
importance: 中
last_reviewed: 2026-06-22
next_review: 2026-07-22
tags: [列表, 缓存]
related: [ListView]
---

# RecyclerView 四级缓存

## 概述
RecyclerView 通过 Scrap/ mAttachedScrap / mCachedViews / ViewCacheExtension / RecycledViewPool 多级复用 ViewHolder，降低滑动时创建/绑定开销。

## 自评依据  ★必填
读过源码、能讲清四级缓存的命中流程和 setHasFixedSize、prefetch 的作用，
也在项目里做过列表性能优化；差在对多类型 + 共享 Pool 的高阶场景还没踩透，所以是"掌握"非"精通"。
````

- [ ] **Step 4: 写 `skills/04-性能优化/启动优化.md`**

````markdown
---
title: 启动优化
domain: 04-性能优化
level: 熟悉
target: 掌握
importance: 高
last_reviewed: 2026-07-01
next_review: 2026-08-31
tags: [启动, 性能]
related: []
---

# 启动优化

## 概述
围绕冷/温/热启动时间，通过异步初始化、延迟初始化、窗口背景、严格模式等手段降低首屏可见耗时。

## 自评依据  ★必填
做过一次启动耗时排查，用过 systrace/Perfetto 定位过阻塞点；
但没系统性拆分启动任务依赖图（如用启动框架），所以是"熟悉"非"掌握"。
````

- [ ] **Step 5: 写 `skills/05-架构/MVVM.md`**

````markdown
---
title: MVVM
domain: 05-架构
level: 掌握
target: 掌握
importance: 高
last_reviewed: 2026-05-01
next_review: 2026-10-29
tags: [架构]
related: [MVI, ViewModel]
---

# MVVM

## 概述
Model-View-ViewModel：View 订阅 ViewModel 暴露的可观察状态，ViewModel 持有业务逻辑与状态，解耦界面与逻辑。

## 自评依据  ★必填
多个项目主力架构都用 MVVM + ViewModel + LiveData/Flow，能独立设计分层与数据流，
也能给别人讲清；已达"掌握"，目标维持。
````

- [ ] **Step 6: 写 `skills/06-系统底层/Binder-原理.md`**

````markdown
---
title: Binder 通信原理
domain: 06-系统底层
level: 了解
target: 掌握
importance: 中
last_reviewed: 2026-06-10
next_review: 2026-07-10
tags: [IPC, 底层]
related: [AIDL]
---

# Binder 通信原理

## 概述
Android 跨进程通信的核心机制，基于内核驱动 + 一次拷贝，配合 ServiceManager 做名称→引用映射。

## 自评依据  ★必填
知道 Binder 是一次拷贝、client/server/ServiceManager 的角色，
但没读过驱动代码、也没手写过跨进程示例，所以是"了解"。
````

- [ ] **Step 7: 写 `skills/07-工程化/Gradle-构建.md`**

````markdown
---
title: Gradle 构建配置
domain: 07-工程化
level: 熟悉
target: 熟悉
importance: 中
last_reviewed: 2026-07-15
next_review: 2026-09-13
tags: [构建, Gradle]
related: []
---

# Gradle 构建配置

## 概述
Android 工程的构建系统，通过 build.gradle 配置依赖、构建变体、签名、产物等。

## 自评依据  ★必填
能写常规依赖、productFlavors、自定义构建任务，处理过依赖冲突；
还没深入 Gradle 插件开发与构建源码，维持"熟悉"。
````

- [ ] **Step 8: 写 `skills/08-网络与存储/OkHttp-拦截器.md`**

````markdown
---
title: OkHttp 拦截器
domain: 08-网络与存储
level: 掌握
target: 精通
importance: 中
last_reviewed: 2026-07-05
next_review: 2026-10-03
tags: [网络, 拦截器]
related: [Retrofit]
---

# OkHttp 拦截器

## 概述
OkHttp 通过责任链模式的拦截器链完成重试、桥接、缓存、连接、网络请求等，用户可插入自定义拦截器统一处理日志/鉴权/重试。

## 自评依据  ★必填
写过自定义拦截器做统一鉴权与日志、读过责任链源码，能讲清调用顺序；
差在连接池/缓存策略的底层细节，所以是"掌握"非"精通"。
````

- [ ] **Step 9: 验证 8 个文件就位且 frontmatter 完整**

Run: `ls skills/*/*.md | wc -l`
Expected: `8`

Run: `grep -L "^level:" skills/*/*.md`
Expected: 无输出（每个文件都有 level 字段）。

- [ ] **Step 10: 提交**

```bash
git add skills
git commit -m "feat: add 8 sample knowledge-point files (one per domain)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: 写示范阶段目标

**Files:**
- Create: `plans/2026-Q3.md`

- [ ] **Step 1: 写阶段目标文件**

````markdown
# 2026 Q3 学习目标

> 周期：2026-07 ~ 2026-09。每个目标关联一个或多个 `skills/` 知识点，达成后把对应 `level` 升上去并更新 `last_reviewed`。

## 目标1：Kotlin 协程 熟悉 → 掌握
- 关联：`skills/01-语言/Kotlin-协程.md`
- 截止：2026-09-30
- [ ] 读结构化并发 + suspend CPS 原理
- [ ] 做一个 Flow 实战项目
- [ ] 能讲清调度器 / 作用域 / 异常传播

## 目标2：Jetpack Compose 了解 → 熟悉
- 关联：`skills/02-框架与Jetpack/Jetpack-Compose.md`
- 截止：2026-09-30
- [ ] 在小项目里用 Compose 重写一个页面
- [ ] 理解重组与 remember/状态提升

## 目标3：Binder 通信原理 了解 → 熟悉
- 关联：`skills/06-系统底层/Binder-原理.md`
- 截止：2026-09-15
- [ ] 手写一个 AIDL 跨进程示例
- [ ] 读一次 Binder 驱动相关资料
````

- [ ] **Step 2: 验证**

Run: `test -f plans/2026-Q3.md && head -1 plans/2026-Q3.md`
Expected: 输出 `# 2026 Q3 学习目标`。

- [ ] **Step 3: 提交**

```bash
git add plans/2026-Q3.md
git commit -m "feat: add sample quarterly plan 2026-Q3

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: 实现 `scripts/build_dashboard.py` 并生成看板

脚本拆为纯函数 + main，完整代码一次性给出。先写好再用真实示范文件验证。

**Files:**
- Create: `scripts/build_dashboard.py`

- [ ] **Step 1: 写完整脚本**

写入 `scripts/build_dashboard.py`：

```python
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
    for f in ("last_reviewed", "next_review"):
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
        entry["_rel"] = str(md.relative_to(REPO_ROOT))
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
```

- [ ] **Step 2: 内联断言验证纯函数（不依赖测试框架）**

Run:
```bash
python3 -c "import sys; sys.path.insert(0,'scripts'); from pathlib import Path; import build_dashboard as b; \
f,e=b.parse_frontmatter('---\ntitle: X\nlevel: 熟悉\ntags: [a, b]\n---\n# body'); \
assert f['title']=='X' and f['level']=='熟悉' and f['tags']==['a','b'] and not e, (f,e); \
w=b.validate({'title':'X','domain':'01-语言','level':'熟悉','target':'掌握','importance':'高','last_reviewed':'2026-07-22','next_review':'bad'}, Path('skills/01-语言/X.md')); \
assert w==['next_review 日期格式错误: bad（应为 YYYY-MM-DD）'], w; \
print('pure-func OK')"
```
Expected: `pure-func OK`（解析正确 + 日期校验告警正确）。

- [ ] **Step 3: 运行脚本，生成 DASHBOARD.md**

Run: `python3 scripts/build_dashboard.py`
Expected: 打印 `已生成 DASHBOARD.md`、`知识点数：8；告警：0`（示范文件全部合法）。

- [ ] **Step 4: 验证看板含四部分且内容正确**

Run: `grep -E "^(## 1\. 熟练度分布|## 2\. 领域分布|## 3\. 复习清单|## 4\. 目标进度)" DASHBOARD.md`
Expected: 4 行全部命中（四个小节标题）。

Run: `awk '/^### 🚨 逾期/{f=1;next} /^### /{f=0} f' DASHBOARD.md | grep -E "Kotlin 协程|Binder"`
Expected: 打印出 `Kotlin 协程` 与 `Binder 通信原理` 两行（它们的 next_review 2026-07-01 / 2026-07-01 都早于今天，落在逾期组）。说明：`awk` 抽取「### 🚨 逾期」小节到下一个 `### ` 之间的行再 grep，避免状态词只出现在标题行导致的误判。

Run: `awk '/^## 4\. 目标进度/{f=1;next} /^## /{f=0} f' DASHBOARD.md | grep -q "MVVM" && echo "FAIL: MVVM in gaps" || echo "MVVM-not-in-gaps: OK"`
Expected: `MVVM-not-in-gaps: OK`（MVVM 的 level==target==掌握，不应出现在目标进度小节）。

> 注：由于「该复习」要求 next_review 恰好等于今天，若执行日 ≠ 2026-07-22，`RecyclerView-缓存`（next_review 2026-07-22）可能落在「逾期」而非「该复习」——这是静态示范日期的正常表现，不影响脚本正确性。

- [ ] **Step 5: 提交脚本与生成的看板**

```bash
git add scripts/build_dashboard.py DASHBOARD.md
git commit -m "feat: add zero-dep dashboard generator and generate DASHBOARD.md

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: 验证脚本校验健壮性（坏文件告警 + 不崩溃）

设计文档验收标准要求：给一个故意写错的文件，脚本能报警且不崩溃。

**Files:**
- Create（临时）: `skills/01-语言/_broken-sample.md`（用完删除）

- [ ] **Step 1: 写一个多处错误的临时文件**

写入 `skills/01-语言/_broken-sample.md`：

````markdown
---
title: 坏样本
domain: 03-UI
level: 专家
target: 掌握
last_reviewed: 2026/07/22
next_review: not-a-date
---

# 坏样本
````

> 故意埋 4 个问题：①缺 `importance` ②`level=专家` 非法 ③`domain=03-UI` 与所在目录 `01-语言` 不一致 ④两个日期格式错误。

- [ ] **Step 2: 运行脚本，确认告警列出且不崩溃**

Run: `python3 scripts/build_dashboard.py`
Expected: 正常退出（退出码 0），`知识点数：9；告警：N`（N 为上述问题数，≥4）。stdout「告警明细」中包含：`缺必填字段: importance`、`level 非法: 专家`、`domain(03-UI) 与文件所在目录(01-语言)不一致`、两条 `日期格式错误`。

Run: `python3 scripts/build_dashboard.py > /dev/null 2>&1; echo "exit=$?"`
Expected: `exit=0`（告警不中断生成）。

- [ ] **Step 3: 删除临时坏文件并重新生成干净看板**

```bash
rm skills/01-语言/_broken-sample.md
python3 scripts/build_dashboard.py
```
Expected: `知识点数：8；告警：0`，DASHBOARD.md 恢复到无告警状态。

- [ ] **Step 4: 确认坏文件未被提交**

Run: `git status --porcelain skills/`
Expected: 无输出（临时文件已删，工作区干净）。

- [ ] **Step 5: 提交（本任务无新增跟踪文件，跳过提交；若 DASHBOARD.md 因日期推移有变化则提交）**

```bash
git status --porcelain || true
```
Expected: 干净（无需提交）。本任务仅做验证，不产生持久改动。

---

## Task 7: 全量验收 + 收尾

对照设计文档第 12 节验收标准逐项核对。

- [ ] **Step 1: 验收清单逐项核对**

Run（一次性核对）:
```bash
echo "== README =="; test -f README.md && grep -q "熟练度四档标准\|了解" README.md && echo OK
echo "== 8 domains with samples =="; ls skills/*/*.md | wc -l
echo "== template =="; test -f templates/skill-template.md && grep -q "自评依据" templates/skill-template.md && echo OK
echo "== plan =="; test -f plans/2026-Q3.md && echo OK
echo "== script zero-dep =="; python3 -c "import ast,sys; ast.parse(open('scripts/build_dashboard.py').read()); print('parses OK')"
echo "== dashboard 4 sections =="; grep -cE "^## [1-4]\. " DASHBOARD.md
```
Expected：
- `README` → `OK`
- 知识点文件数 → `8`
- `template` → `OK`
- `plan` → `OK`
- `script` → `parses OK`
- dashboard 小节数 → `4`

- [ ] **Step 2: 重新生成看板确保最新**

Run: `python3 scripts/build_dashboard.py`
Expected: `知识点数：8；告警：0`。

- [ ] **Step 3: 清理 `.gitkeep`（可选）**

各领域目录现在都有 `.md` 文件，`.gitkeep` 不再必要但保留也无害。**保留不动**（避免无谓改动）。

- [ ] **Step 4: 最终提交（如有未提交改动）**

Run: `git status --porcelain`
若有改动：
```bash
git add -A
git commit -m "chore: finalize dashboard and verify acceptance criteria

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```
Expected: 工作区干净（前面任务已逐步提交）。

- [ ] **Step 5: 确认分支提交历史**

Run: `git log --oneline main..HEAD`
Expected: 看到 Task 1/2/3/4/5 的提交（设计文档那次在 main..HEAD 之外？——设计文档提交在本分支，应也可见）。确认所有功能提交都在 `setup/android-skills-knowledge-base` 分支上。

---

## 完成后

- 知识库骨架、模板、8 个示范知识点、阶段目标、看板脚本、生成的 DASHBOARD.md 全部就位。
- 用户可立即开始：复制模板新增知识点 → 跑脚本刷新看板 → 按季度立 plans。
- 后续可选（设计文档第 11 节 YAGNI 项）：熟练度历史趋势（`reviews/history.csv`）、领域 `_index.md`、双向链接。
