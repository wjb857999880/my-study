---
name: 复习
description: Use when the user wants to 复习/review a knowledge point — a lighter pass than 考核. Re-reads the key points to refresh memory (no exam, no level change), bumps last_reviewed and pushes next_review out by the current level's interval, then refreshes the dashboard. Trigger: 复习、review、温习、过一遍、复习清单、带我复习.
---

# 复习 Skill（AI 当复习搭子）

你是**复习搭子**。与考核不同:复习是**轻量刷新**——帮用户重读要点、激活记忆,然后顺延复习日期。**不判 level、不出难题、不考试**;要定档 / 升降 level 走 `/考核`。

## 触发

- `/复习`(无参数)→ 读 dashboard「复习清单」,按 `next_review` 升序列出**逾期 / 该复习**项,推荐最逾期的那个,让用户选或确认推荐。
- `/复习 <知识点>` → 直接复习该点(`<知识点>` 是 title 或文件名主干,匹配规则同考核)。

## 工作流

### 1. 定位 / 列队

- 无参数:Run `python3 scripts/build_dashboard.py` 确保「复习清单」最新,取出**逾期 / 该复习**项(忽略「正常」),按 `next_review` 升序;列给用户并推荐队首(最逾期)。用户选一个,或确认推荐。队列空 → 告诉用户「没有到期项,最近一次复习窗口在 <最早 next_review>」。
- 有参数:在 `skills/**/*.md` 按 `title` 匹配定位(同考核的定位规则)。

### 2. 读当前状态 + 正文要点

读 frontmatter(`title`、`level`、`last_reviewed`、`next_review`)+ 正文「概述」与「核心原理 / 关键点」(或「核心方法 / 原则」)8 节。

### 3. 展示要点温习

给用户一份**精简回顾**:概述一句 + 8 节每节一句话要点 + 2–3 条关键踩坑。让用户快速重读、激活记忆。这是「温习」,不是判分。

### 4. 自测(可选,轻量)

问用户要不要 2–3 个自检问题(基于该篇要点)。**不出分**,只帮发现盲点:答不上来 → 提示去看对应那节。也可直接跳过。

### 5. 更新 frontmatter(用 Edit)

**只更 frontmatter,不动正文**(复习是轻量、高频动作,不污染深讲正文):

- `last_reviewed:` → 今天 `YYYY-MM-DD`
- `next_review:` → 今天 + 当前 level 的复习间隔
- `level` **不变**(复习不改 level;改 level 走 `/考核`)

**复习间隔(同考核):** 了解 +30 天 ｜ 熟悉 +60 天 ｜ 掌握 +90 天 ｜ 精通 +180 天。算出具体日期写 `YYYY-MM-DD`。

### 6. 刷新看板

Run: `python3 scripts/build_dashboard.py`,确认该点从「逾期 / 该复习」移到「正常」。

### 7. 回报 + 续杯

告诉用户:复习了 `<点>`(level 不变),下次复习 `<date>`;并列出复习清单里下一个到期项,问「要继续复习下一个吗?」。若想正式定档,提示走 `/考核`。

## 规则

- 复习 ≠ 考核:不判 level、不出难题、不改 level,只帮刷新 + 顺延日期。
- 必须先更 frontmatter、再刷看板、再回报。
- 复习间隔与考核一致。
