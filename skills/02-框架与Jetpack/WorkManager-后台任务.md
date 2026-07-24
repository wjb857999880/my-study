---
title: WorkManager 后台任务
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [WorkManager, 后台, 任务]
related: [Android 四大组件与生命周期]
---

# WorkManager 后台任务

## 概述
Jetpack 的**可靠后台任务**方案:适合「需要保证执行、但可延迟」的任务(上传日志、同步数据、定期清理)。系统会根据电量 / 网络 / 约束择机执行,即使 App 退出或重启也能补跑(持久化 + 重启恢复)。替代了 Service + AlarmManager 的碎片化方案,适配 Android 后台限制。区分:即时任务用协程 / 前台服务,可靠延迟任务用 WorkManager。支持约束(网络 / 充电)、链式任务、周期任务。

## 考核记录
（尚未考核）
