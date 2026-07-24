---
title: CI/CD 流水线与发布
domain: 07-工程化
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [CI, CD, 发布]
related: [Gradle 构建配置, 自动化测试]
---

# CI/CD 流水线与发布

## 概述
把构建-测试-发布自动化:**CI**(每次提交自动构建 + 跑测试 + 静态检查,GitHub Actions / GitLab CI / Bitrise)、**CD**(自动打包、签名、分发到测试渠道 / 商店)。流水线串联:代码提交 → Lint + 单测 → 构建 APK/AAB → 签名 → 内测分发(Firebase / 蒲公英)→ 灰度 → 商店发布。配合质量门禁(测试通过率、包体积阈值)与产物管理。提升交付速度与质量一致性。

## 考核记录
（尚未考核）
