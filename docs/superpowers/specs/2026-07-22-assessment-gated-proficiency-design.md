# 熟练度「考核验证制」设计修订

- **日期**: 2026-07-22
- **作者**: wujiabao（安卓应用开发工程师）
- **状态**: 已确认，待编写实施计划
- **修订对象**: `docs/superpowers/specs/2026-07-22-android-skills-knowledge-base-design.md`（原设计）

## 1. 背景与目标

原设计中，知识点的 `level` 由用户自报，正文用「自评依据」落实"考察"。用户要求改为**考核验证制**：

- 新增知识点**一律初始化为 `了解`**；
- `level` **只能通过一次「考核」来判定/提升**，考核由 AI（Claude）当考官、根据用户表现判定等级；
- level 从「自报」变为「考核验证」，更扎实。

本修订对原设计做增量调整，不推翻原结构。

## 2. 关键决策

| 决策点 | 结论 |
|--------|------|
| 谁当考官 | **AI（Claude）当考官**：用户点名考核某知识点 → AI 按梯度出题 → 用户作答 → AI 判定 level |
| 考核与复习关系 | **并存**：考核决定 level；复习（spaced repetition）只提醒温习、不改 level，两套字段独立 |
| 考核流程形态 | **做成可复用 skill `/考核`**（项目级），内含工作流 + 出题梯度规范 + 文件更新步骤 |
| 出题规范位置 | 直接写进 skill（不另建文档，DRY） |

## 3. 数据模型改动

### 3.1 Frontmatter（在原字段上加 1 个）

| 字段 | 变化 | 说明 |
|------|------|------|
| `level` | 语义变化 | 初始化为 `了解`；**仅考核后由 AI 判定提升** |
| `last_assessed` | **新增** | 上次考核日期 `YYYY-MM-DD`；空 = 待考核（未考核过） |
| `target` | 不变 | 目标级别 |
| `last_reviewed` / `next_review` | 不变（复习） | 复习独立于考核，不改 level |
| `title`/`domain`/`importance`/`tags`/`related` | 不变 | — |

用 `last_assessed` 是否为空判断「已考核/待考核」，**不另加布尔字段**（YAGNI）。

### 3.2 正文：必填段由「自评依据」改为「考核记录」

把原必填的 `## 自评依据` 改为 `## 考核记录`。每次考核由 skill 追加一条：

```markdown
## 考核记录
- **2026-07-22** 判定：熟悉 → 掌握 ✅ ｜ 考官：AI
  - 表现：能独立讲清结构化并发与作用域取消；排障题答出 2/3
  - 依据：调度器源码未答全，未达精通，故判掌握
- **2026-06-10** 判定：了解 → 熟悉 ✅ ｜ 考官：AI
  - 表现：概念题全对，照做题基本写出
```

首次考核前该段显示「（尚未考核）」。

## 4. 考核 skill 设计（`.claude/skills/考核/SKILL.md`）

项目级 skill，用户输入 `/考核 <知识点>` 触发。skill 内容（由实施计划给出完整文本）包含：

### 4.1 skill frontmatter
```yaml
---
name: 考核
description: Use when the user wants to 考核/assess a knowledge point's proficiency. Conducts a graduated assessment (AI as examiner), judges the level from performance, and updates the knowledge-point file. Trigger: 考核、assess、测试熟练度、考察熟练度.
---
```

### 4.2 skill 工作流
1. 解析参数 `<知识点>`，在 `skills/**/*.md` 中按 `title`（或文件名）定位文件；找不到则列出候选并让用户选。
2. 读该文件：当前 `level`、`target`、`last_assessed`，以及正文「概述/核心原理/考核记录」。
3. **按出题梯度规范出题**：从当前 level 起逐档向上出题（先验证当前档是否仍成立，再逐级往上探），每档出 1–2 题，用户作答。新知识点当前 level 为了解，故从了解起。
4. **判定 level**：用户能稳稳答到的最高档 = 判定 level；答不上则停在上一档。
5. **更新文件**（用 Edit）：
   - frontmatter：`level` → 判定值；`last_assessed` → 今天；`last_reviewed` → 今天（考核也算一次温习）；`next_review` → 今天 + 新 level 的复习间隔。
   - 正文：在「考核记录」段最上方追加一条（日期、判定变化、表现、依据）。
6. 重新生成看板：`python3 scripts/build_dashboard.py`。
7. 回报判定结果（旧 level → 新 level，以及下一步建议）。

### 4.3 出题梯度规范（写入 skill）
| 目标档位 | 考核题型 | 通过标准 |
|---------|---------|---------|
| 了解 | 概念题：是什么 / 解决什么 / 核心术语 / 与替代方案区别 | 能讲清即通过 |
| 熟悉 | 照做题：给场景或 API，写出基本用法 | 能照着写出可行用法 |
| 掌握 | 独立实现 + 排障：设计小实现 / 给问题代码找 bug | 能独立给出可行方案 |
| 精通 | 架构设计 / 原理深挖 / 性能权衡 / 能否讲透 | 能做设计、讲清权衡 |

### 4.4 复习间隔（skill 据此设 `next_review`）
了解 +30 天 ｜ 熟悉 +60 天 ｜ 掌握 +90 天 ｜ 精通 +180 天（与 README 一致）。

### 4.5 skill 的 git 跟踪
`.claude/skills/` 需提交；`.claude/state/` 与 `.claude/sessions/` 是运行时状态，加入 `.gitignore`。

## 5. 看板 / 脚本改动（`scripts/build_dashboard.py`）

DASHBOARD.md 在现有四部分前**新增第 0 部分「考核进度」**：
- 已考核 N / 待考核 M（待考核 = `last_assessed` 为空）。
- 列出**待考核清单**（候选考核项：title、领域、target）。

其余四部分（熟练度分布 / 领域分布 / 复习清单 / 目标进度）保留。熟练度分布表下加一行说明：「含待考核知识点（默认了解）」。

脚本校验新增：`last_assessed` 若非空，必须为 `YYYY-MM-DD` 格式，否则告警。

`level`/`target` 平均与差距计算不变（待考核点 level=了解=1 自然计入）。

## 6. 对现有 8 个示范点的处理

按「初始化为了解」规则重置每个示范文件：
- `level` → `了解`；
- `last_assessed` → 空（待考核）；
- 正文「自评依据」段 → 改为「考核记录」并标注「（尚未考核）」；
- `last_reviewed`/`next_review` 保留（复习字段不变，体现复习与考核独立）。

重置后示范数据如实反映新基线：8 个知识点全部 `了解` / 待考核，复习清单仍按 `next_review` 呈现逾期/该复习/正常。

## 7. README 改动

- 新增「**考核流程**」一节：说明 `/考核 <知识点>` 用法、AI 当考官、level 仅考核后提升、初始化为了解。
- 新增「**复习 vs 考核**」说明：考核改 level，复习只提醒温习。
- 熟练度四档标准补充：level 为考核验证、新增知识点初始化为了解。
- 「新增一个知识点」步骤更新：复制模板后 level 默认了解、`last_assessed` 留空。
- 模板示例的 frontmatter 同步：`level: 了解`、加 `last_assessed:`（空）。

## 8. 文件清单

| 操作 | 文件 |
|------|------|
| 新建 | `.claude/skills/考核/SKILL.md`（考核 skill） |
| 修改 | `templates/skill-template.md`（level 默认了解、加 last_assessed、自评依据→考核记录） |
| 修改 | `scripts/build_dashboard.py`（加「考核进度」部分 + last_assessed 校验） |
| 修改 | `skills/*/*.md` ×8（重置为了解/待考核、自评依据→考核记录） |
| 修改 | `README.md`（考核流程、复习 vs 考核、初始化说明） |
| 修改 | `DASHBOARD.md`（脚本重新生成） |
| 修改 | `.gitignore`（忽略 `.claude/state/`、`.claude/sessions/`） |

## 9. 验收标准

- [ ] `/考核 <知识点>` skill 存在于 `.claude/skills/考核/SKILL.md` 且已被 git 跟踪。
- [ ] 模板 frontmatter 默认 `level: 了解`、含 `last_assessed:`（空），正文为「考核记录」段。
- [ ] 8 个示范点全部 `level: 了解`、`last_assessed` 为空、正文为「考核记录（尚未考核）」。
- [ ] 脚本生成 DASHBOARD.md 含「考核进度」部分（已考核 0 / 待考核 8）。
- [ ] 脚本校验：`last_assessed` 非空且格式错时告警（用临时坏文件验证，随后删除）。
- [ ] README 含考核流程与「复习 vs 考核」说明。
- [ ] 手动走一遍 `/考核` 对某示范点：能出题、判定、更新 level/last_assessed/考核记录、重置 next_review、刷新看板。
