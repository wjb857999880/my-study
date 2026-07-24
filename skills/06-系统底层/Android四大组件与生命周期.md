---
title: Android 四大组件与生命周期
domain: 06-系统底层
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [四大组件, 生命周期, Activity]
related: [Handler 消息机制]
---

# Android 四大组件与生命周期

## 概述
Android 应用的基石:**Activity**(界面,完整生命周期 onCreate→onStart→onResume→onPause→onStop→onDestroy,及配置变更 / 异常重建)、**Service**(后台,started / bound 两种模式,Android 8+ 后台限制严)、**BroadcastReceiver**(广播,静态 / 动态注册)、**ContentProvider**(跨进程数据共享)。`Context` 是访问系统资源的入口。生命周期管理是高级开发的核心——内存泄漏、状态恢复、进程优先级都与之相关。Android 10+ 还有作用域存储、后台启动限制等演变。

## 考核记录
（尚未考核）
