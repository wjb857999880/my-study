# 熟练度「考核验证制」实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把熟练度 `level` 从自报改为考核验证——新知识点初始化为了解，level 只能通过 `/考核` skill（AI 当考官）按表现判定提升；考核与复习并存。

**Architecture:** 改数据模型（frontmatter 加 `last_assessed`、正文「自评依据」→「考核记录」）+ 新建项目级 `/考核` skill（含出题梯度规范与文件更新步骤）+ 脚本加「考核进度」部分 + 重置 8 个示范点 + 更新 README。纯文档 + 一个零依赖 Python 脚本 + 一个 Claude Code skill。

**Tech Stack:** Markdown / YAML frontmatter / Python3（零依赖）/ Claude Code 项目级 skill。

**对应设计文档：** `docs/superpowers/specs/2026-07-22-assessment-gated-proficiency-design.md`

**执行分支：** `feature/assessment-gated-proficiency`（设计文档已在此分支提交）

---

## Task 1: 更新知识点模板

**Files:**
- Modify: `templates/skill-template.md`

- [ ] **Step 1: 整体替换 `templates/skill-template.md` 为以下内容**

```markdown
---
title: 知识点名称                # 必填，如 Kotlin 协程
domain: 01-语言                 # 必填，对应 skills/ 下的目录名
level: 了解                     # 必填，初始化为了解；仅考核后由 AI 判定提升
target: 掌握                    # 必填，目标：了解/熟悉/掌握/精通
importance: 高                  # 必填，优先级：高/中/低
last_assessed:                  # 上次考核日期 YYYY-MM-DD；空 = 待考核
last_reviewed: 2026-07-22       # 必填，上次复习日期 YYYY-MM-DD
next_review: 2026-08-22         # 必填，下次复习日期 YYYY-MM-DD
tags: [标签1, 标签2]            # 可选
related: [关联知识点]           # 可选
---

# 知识点名称

## 概述
一两句话：是什么、解决什么问题。（按需）

## 考核记录
（尚未考核）

> level 仅在 `/考核 <知识点>` 后由 AI 根据表现判定；每次考核在此追加一条：
> - **YYYY-MM-DD** 判定：旧level → 新level ✅ ｜ 考官：AI
>   - 表现：<概括>
>   - 依据：<为什么是这个 level>

## 核心原理 / 关键点
深挖时再补。

## 实践经验 / 踩坑
做过什么、遇到过什么问题。

## 待深入 / 下一步
- [ ] 下一步学习项

## 参考资料
- 链接
```

- [ ] **Step 2: 验证**

Run: `head -10 templates/skill-template.md`
Expected: 含 `level: 了解`、`last_assessed:`（空）、`last_reviewed:`。

Run: `grep -q "## 考核记录" templates/skill-template.md && grep -q "## 自评依据" templates/skill-template.md && echo "FAIL: 自评依据仍在" || echo "OK: 考核记录已替换自评依据"`
Expected: `OK: 考核记录已替换自评依据`

- [ ] **Step 3: 提交**

```bash
git add templates/skill-template.md
git commit -m "refactor: template uses assessment-verified level (init 了解, last_assessed, 考核记录)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: 重置 8 个示范知识点

对 `skills/*/*.md` 的每个文件做 3 处改动（同一套变换）：
1. frontmatter `level: <旧值>` → `level: 了解`
2. 在 `importance:` 行**之后**插入一行 `last_assessed:`（空值）
3. 正文 `## 自评依据  ★必填` 这一整段（标题 + 其下到下一个 `##` 之前的全部内容）替换为：
   ```
   ## 考核记录
   （尚未考核）
   ```

**Files (8):**
- `skills/01-语言/Kotlin-协程.md`
- `skills/02-框架与Jetpack/Jetpack-Compose.md`
- `skills/03-UI/RecyclerView-缓存.md`
- `skills/04-性能优化/启动优化.md`
- `skills/05-架构/MVVM.md`
- `skills/06-系统底层/Binder-原理.md`
- `skills/07-工程化/Gradle-构建.md`
- `skills/08-网络与存储/OkHttp-拦截器.md`

**目标 frontmatter 形态（以 Kotlin-协程 为例）：**
```yaml
---
title: Kotlin 协程
domain: 01-语言
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-06-01
next_review: 2026-07-01
tags: [并发, 异步]
related: [RxJava, Handler]
---
```
（其余 7 个同理：保留各自原有 domain/target/importance/last_reviewed/next_review/tags/related，仅 level→了解、插入空的 last_assessed、自评依据→考核记录。`last_reviewed`/`next_review` 不动。）

- [ ] **Step 1: 对 8 个文件逐一应用上述 3 处变换**

逐个文件读取 → 修改 frontmatter（level、插 last_assessed）→ 替换「自评依据」段为「考核记录」。

- [ ] **Step 2: 验证**

Run: `grep -h "^level:" skills/*/*.md | sort | uniq -c`
Expected: `8 了解`（全部为了解，无其他值）

Run: `grep -L "^last_assessed:" skills/*/*.md`
Expected: 无输出（每个文件都有 last_assessed 字段）

Run: `for f in skills/*/*.md; do grep -q "## 考核记录" "$f" || echo "缺考核记录: $f"; done`
Expected: 无输出（每个文件都有「考核记录」段）

Run: `grep -rl "## 自评依据" skills/ || echo "OK: 无残留自评依据"`
Expected: `OK: 无残留自评依据`

- [ ] **Step 3: 提交**

```bash
git add skills
git commit -m "refactor: reset 8 samples to 了解/待考核 (assessment-gated baseline)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: 脚本加「考核进度」部分 + last_assessed 校验

**Files:**
- Modify: `scripts/build_dashboard.py`

三处精确修改：

- [ ] **Step 1: `validate()` —— 把 `last_assessed` 纳入日期校验**

找到：
```python
    for f in ("last_reviewed", "next_review"):
        v = fields.get(f)
        if v and not _is_date(v):
            warns.append("%s 日期格式错误: %s（应为 YYYY-MM-DD）" % (f, v))
```
替换为：
```python
    for f in ("last_reviewed", "next_review", "last_assessed"):
        v = fields.get(f)
        if v and not _is_date(v):
            warns.append("%s 日期格式错误: %s（应为 YYYY-MM-DD）" % (f, v))
```

- [ ] **Step 2: `render()` —— 在校验告警块之后、`total = len(entries)` 之前插入「考核进度」部分**

找到：
```python
    else:
        lines.append("## ✅ 校验通过（无告警）")
    lines.append("")

    total = len(entries)
```
替换为：
```python
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
```

- [ ] **Step 3: `render()` —— 熟练度分布表后加一行说明**

找到：
```python
        lines.append("| %s | %d | %s |" % (lvl, n, pct))
    lines.append("")

    # 2. 领域分布
```
替换为：
```python
        lines.append("| %s | %d | %s |" % (lvl, n, pct))
    lines.append("")
    lines.append("> 注：含待考核知识点（默认为了解）；level 仅考核后由 AI 判定。")
    lines.append("")

    # 2. 领域分布
```

- [ ] **Step 4: 内联断言验证 last_assessed 校验**

Run:
```bash
python3 -c "import sys; sys.path.insert(0,'scripts'); from pathlib import Path; import build_dashboard as b; \
w=b.validate({'title':'X','domain':'01-语言','level':'熟悉','target':'掌握','importance':'高','last_reviewed':'2026-07-22','next_review':'2026-08-22','last_assessed':'bad'}, Path('skills/01-语言/X.md')); \
assert any('last_assessed' in x for x in w), w; print('last_assessed validation OK')"
```
Expected: `last_assessed validation OK`

- [ ] **Step 5: 运行脚本，确认含「考核进度」且计数正确**

Run: `python3 scripts/build_dashboard.py`
Expected: `知识点数：8；告警：0`

Run: `grep -E "^## (考核进度|1\. 熟练度分布|2\. 领域分布|3\. 复习清单|4\. 目标进度)" DASHBOARD.md`
Expected: 5 行全部命中（新增考核进度 + 原四部分）。

Run: `grep "已考核 0 / 待考核 8" DASHBOARD.md`
Expected: 命中一行（8 个示范点全部待考核）。

- [ ] **Step 6: 提交**

```bash
git add scripts/build_dashboard.py
git commit -m "feat: add 考核进度 section and last_assessed validation to dashboard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: 创建 `/考核` skill

**Files:**
- Create: `.claude/skills/考核/SKILL.md`

- [ ] **Step 1: 创建目录与 skill 文件**

```bash
mkdir -p .claude/skills/考核
```

写入 `.claude/skills/考核/SKILL.md`：

````markdown
---
name: 考核
description: Use when the user wants to 考核/assess a knowledge point's proficiency. Conducts a graduated assessment with AI as examiner, judges the level from demonstrated performance (not self-report), and updates the knowledge-point file + dashboard. Trigger: 考核、assess、测试熟练度、考察熟练度、考我.
---

# 考核 Skill（AI 当考官）

你是**考官**。用户要考核某个 Android 知识点的熟练度，由你**根据其作答表现判定 level**——不是让用户自报。

## 触发

用户运行 `/考核 <知识点>`，`<知识点>` 是知识点标题（如 `Kotlin 协程`）或文件名（如 `Kotlin-协程`）。

## 工作流

### 1. 定位知识点
- 在 `skills/**/*.md` 中按 frontmatter `title` 匹配 `<知识点>`（也接受文件名主干）。
- 唯一匹配 → 用之；无匹配 → 列出相近项让用户选；多个匹配 → 让用户选。

### 2. 读取当前状态
读 frontmatter：`title`、`level`（当前）、`target`、`last_assessed`、`domain`；正文「概述/核心原理」如有也读。

### 3. 按梯度逐档出题
**从当前 `level` 起逐档向上**（先验证当前档是否仍成立，再逐级往上探），每档出 1–2 题，用户作答后再判是否继续上探。**逐档问，不要一次抛出所有题。**

**出题梯度规范：**

| 目标档位 | 题型 | 通过标准 |
|---------|------|---------|
| 了解 | 概念题：是什么 / 解决什么问题 / 核心术语 / 与替代方案区别 | 能讲清 |
| 熟悉 | 照做题：给场景或 API，写出基本用法 | 能照着写出可行用法 |
| 掌握 | 独立实现 + 排障：设计小实现 / 给问题代码找 bug | 能独立给出可行方案 |
| 精通 | 架构设计 / 原理深挖 / 性能权衡 / 能否讲透 | 能做设计、讲清权衡 |

### 4. 判定 level
判定 level = **用户能稳稳答到的最高档**。某一档答不上就停在该档之下一档。判定可低于当前 level（当前档守不住就下调）——要诚实。若概念题（了解档）就答不出，判为了解并提示「建议先学习再考核」。

### 5. 更新文件（用 Edit）
frontmatter：
- `level:` → 判定值
- `last_assessed:` → 今天 `YYYY-MM-DD`
- `last_reviewed:` → 今天 `YYYY-MM-DD`（考核也算一次温习）
- `next_review:` → 今天 + 新 level 的复习间隔（见下）

正文：在 `## 考核记录` 段最上方追加一条（首次考核时把「（尚未考核）」替换掉）：
```
- **YYYY-MM-DD** 判定：旧level → 新level ✅ ｜ 考官：AI
  - 表现：<一两句概括答得好的与不足>
  - 依据：<为什么是这个 level>
```
（level 上升或持平用 ✅，下调用 ⬇️；首次考核旧level 写「(待考核)」。）

**复习间隔（`next_review` = 今天 + ）：** 了解 +30 天 ｜ 熟悉 +60 天 ｜ 掌握 +90 天 ｜ 精通 +180 天。算出具体日期写 `YYYY-MM-DD`。

### 6. 刷新看板
Run: `python3 scripts/build_dashboard.py`，确认计数更新。

### 7. 回报
告诉用户：旧 level → 判定 level、一句依据、下一步建议（如「差 X 档到 target，建议补 Y 后再考」）。

## 规则
- 按**表现**判定，绝不让用户自报 level。
- 严谨但建设性，目标是给一个诚实的熟练度信号。
- 必须先更新文件、再刷新看板，才能回报完成。
````

- [ ] **Step 2: 验证 skill 文件结构与 frontmatter**

Run: `head -4 .claude/skills/考核/SKILL.md`
Expected: `---`、`name: 考核`、`description: ...`、`---`

Run: `grep -cE "^### [1-7]\. " .claude/skills/考核/SKILL.md`
Expected: `7`（工作流 7 步全在）

Run: `grep -q "出题梯度规范" .claude/skills/考核/SKILL.md && grep -q "复习间隔" .claude/skills/考核/SKILL.md && echo "OK"`
Expected: `OK`

- [ ] **Step 3: 提交（skill 需纳入 git；运行时状态在 Task 6 忽略）**

```bash
git add .claude/skills/考核/SKILL.md
git commit -m "feat: add /考核 assessment skill (AI examiner + rubric + file update)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: 更新 README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 在「熟练度四档标准」表后加一句说明**

找到「脚本内部数值映射」那一段，在其后追加一段：
```markdown

> **level 为考核验证**：新增知识点初始化为「了解」；熟练度只在通过 `/考核`（AI 当考官、按表现判定）后提升，不是自报。
```

- [ ] **Step 2: 更新「新增一个知识点」步骤**

把该节的第 2、3 步替换为：
```markdown
2. 填写 frontmatter（`title`/`domain`/`target`/`importance`/`last_reviewed`/`next_review` 必填）；`level` 保持模板默认「了解」、`last_assessed` 留空（待考核）。
3. 正文写「概述」即可；「考核记录」段初始为「（尚未考核）」，考核后由 skill 自动填写。
```

- [ ] **Step 3: 在「生成总看板」一节之后插入「考核流程」与「复习 vs 考核」两节**

插入：
```markdown
## 考核流程（提升熟练度）

```
/考核 <知识点>
```

例如 `/考核 Kotlin 协程`。我（AI）当考官，按四档梯度出题，你作答，我根据表现判定 level、更新该知识点的 `level`/`last_assessed`/「考核记录」、重置复习日期并刷新看板。**只有考核能改变 level。**

出题梯度：了解=概念题 / 熟悉=照做题 / 掌握=独立实现+排障 / 精通=架构设计。

## 复习 vs 考核

- **考核**：决定 `level`，由 `/考核` 触发，记录在 `last_assessed` 与「考核记录」段。
- **复习**：基于 `next_review` 的温习提醒，不改 level；到期了重看一遍（或重新考核冲下一档）。
- 看板的「考核进度」展示已考核/待考核；「复习清单」展示到期温习。
```

- [ ] **Step 4: 更新「长期跟进工作流」加入考核步骤**

把该节列表替换为：
```markdown
1. 新增/复习一个知识点 → 更新对应 `.md`（`last_reviewed`/`next_review`/概述）。
2. 想提升 level → 跑 `/考核 <知识点>`，由 AI 判定。
3. 跑 `python3 scripts/build_dashboard.py` 刷新看板。
4. 看「考核进度」安排要考核的；看「复习清单」安排温习。
5. 每季度在 `plans/` 立目标，达成后用 `/考核` 把 level 升上去。
```

- [ ] **Step 5: 验证**

Run: `grep -q "考核流程（提升熟练度）" README.md && grep -q "复习 vs 考核" README.md && grep -q "level 为考核验证" README.md && echo OK`
Expected: `OK`

- [ ] **Step 6: 提交**

```bash
git add README.md
git commit -m "docs: document 考核 flow and 复习 vs 考核 in README

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: .gitignore 运行时状态 + 重新生成看板 + 端到端验证

**Files:**
- Modify: `.gitignore`
- Modify: `DASHBOARD.md`（脚本重新生成）

- [ ] **Step 1: .gitignore 增加 Claude 运行时状态忽略**

在 `.gitignore` 末尾追加：
```
# Claude Code 运行时状态（不提交），.claude/skills/ 保留提交
.claude/state/
.claude/sessions/
```

- [ ] **Step 2: 确认只跟踪 skill、忽略运行时状态**

Run: `git status --short`
Expected: 列出 `.gitignore`、`DASHBOARD.md` 改动；**不应**出现 `.claude/state/` 或 `.claude/sessions/`（已被忽略）；`.claude/skills/考核/SKILL.md` 应已在 Task 4 提交、不再出现。

- [ ] **Step 3: 端到端验证考核计数（用临时文件模拟一次考核结果）**

创建 `skills/01-语言/_test-assessed.md`（模拟考核后状态）：
```markdown
---
title: 测试-已考核
domain: 01-语言
level: 熟悉
target: 掌握
importance: 低
last_assessed: 2026-07-22
last_reviewed: 2026-07-22
next_review: 2026-09-20
---

# 测试-已考核

## 考核记录
- **2026-07-22** 判定：(待考核) → 熟悉 ✅ ｜ 考官：AI
  - 表现：概念题全对，照做题基本写出
  - 依据：排障题未答，未达掌握
```

Run: `python3 scripts/build_dashboard.py`
Expected: `知识点数：9；告警：0`

Run: `grep "已考核 1 / 待考核 8" DASHBOARD.md`
Expected: 命中（1 个已考核 = 测试文件，8 个待考核 = 示范点）。

Run: `grep -q "测试-已考核" DASHBOARD.md && echo "assessed listed OK"`
Expected: `assessed listed OK`（已考核的知识点应从「待考核清单」消失；可在「目标进度」等处出现）。

- [ ] **Step 4: 删除临时文件并重新生成干净看板**

```bash
rm skills/01-语言/_test-assessed.md
python3 scripts/build_dashboard.py
```
Expected: `知识点数：8；告警：0`，DASHBOARD 恢复 `已考核 0 / 待考核 8`。

- [ ] **Step 5: 确认临时文件未提交、工作区干净**

Run: `git status --short skills/`
Expected: 无输出（临时文件已删）。

- [ ] **Step 6: 提交 .gitignore（DASHBOARD 内容应与基线一致，若脚本输出使其变化也一并提交）**

```bash
git add .gitignore
git status --porcelain DASHBOARD.md | grep -q . && git add DASHBOARD.md || true
git commit -m "chore: ignore Claude runtime state, regenerate dashboard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: 全量验收 + 收尾

对照设计文档第 9 节验收标准逐项核对。

- [ ] **Step 1: 验收清单逐项核对**

Run:
```bash
echo "== skill 存在且被跟踪 =="; git ls-files .claude/skills/考核/SKILL.md
echo "== 模板 =="; grep -q "level: 了解" templates/skill-template.md && grep -q "last_assessed:" templates/skill-template.md && grep -q "## 考核记录" templates/skill-template.md && echo OK
echo "== 8 示范点 =="; grep -h "^level:" skills/*/*.md | sort -u; echo "last_assessed 空值数: $(grep -h "^last_assessed:$" skills/*/*.md | wc -l | tr -d ' ')"
echo "== 看板考核进度 =="; grep -c "## 考核进度" DASHBOARD.md; grep "已考核 0 / 待考核 8" DASHBOARD.md
echo "== 脚本零依赖 =="; python3 -c "import ast; ast.parse(open('scripts/build_dashboard.py').read()); print('parses OK')"
echo "== README =="; grep -q "考核流程（提升熟练度）" README.md && grep -q "复习 vs 考核" README.md && echo OK
echo "== gitignore 运行时 =="; grep -q ".claude/state/" .gitignore && grep -q ".claude/sessions/" .gitignore && echo OK
```
Expected：
- skill 路径被列出（已跟踪）
- 模板 `OK`
- level 只有 `了解`；`last_assessed:` 空值数 `8`
- 考核进度计数 `1`（一节）；命中 `已考核 0 / 待考核 8`
- 脚本 `parses OK`
- README `OK`
- gitignore `OK`

- [ ] **Step 2: 确认 /考核 端到端可执行性**

真实交互式 `/考核`（出题→作答→判定）需**重启会话**后由用户触发——项目级 skill 在新会话才注册为命令。本计划已验证它依赖的整条管线：
- **文件更新产物正确**：Task 6 Step 3 的临时「已考核」文件被脚本正确计入 `已考核 1 / 待考核 8`，证明 frontmatter（`level`/`last_assessed`）+「考核记录」→ 看板「考核进度」的链路畅通。
- **skill 文件完整**：Task 4 已确认 7 步工作流 + 出题梯度 + 文件更新步骤齐全，且 skill 内含 `python3 scripts/build_dashboard.py` 刷新步骤。

Run: `test -f .claude/skills/考核/SKILL.md && grep -q "python3 scripts/build_dashboard.py" .claude/skills/考核/SKILL.md && grep -q "出题梯度规范" .claude/skills/考核/SKILL.md && echo "skill ready; restart session to use /考核"`
Expected: `skill ready; restart session to use /考核`

- [ ] **Step 3: 最终提交（若有未提交改动）**

Run: `git status --porcelain`
若 `skills/` 或 `DASHBOARD.md` 有改动（还原后应干净；若日期推移导致 DASHBOARD 变化则提交）：
```bash
git add -A
git commit -m "chore: finalize assessment-gated proficiency verification

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```
Expected: 工作区干净。

- [ ] **Step 4: 确认分支提交历史**

Run: `git log --oneline main..HEAD`
Expected: 看到 Task 1–6 的提交 + 设计文档提交。

---

## 完成后

- level 改为考核验证制：新点默认了解，仅 `/考核` 后提升。
- `/考核 <知识点>` skill 就位（项目级，已纳入 git）；用户重启会话后即可用 `/考核` 调用。
- 看板新增「考核进度」；8 示范点重置为基线。
- 后续真实使用：用户对某知识点跑 `/考核`，skill 出题、判定、更新文件、刷新看板。
