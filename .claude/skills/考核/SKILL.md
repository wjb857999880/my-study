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
