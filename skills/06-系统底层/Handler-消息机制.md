---
title: Handler 消息机制
domain: 06-系统底层
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [Handler, Looper, 消息队列]
related: [Kotlin 协程]
---

# Handler 消息机制

## 概述
Android 主线程消息循环的基础:Handler 发消息 / Runnable → `MessageQueue`(按时间排序的单链表)→ `Looper.loop()` 取出 → 分发回 `Handler.handleMessage`。**线程切换**(子线程 post 到主线程)本质靠它;底层用 epoll(管道唤醒)避免空轮询阻塞。主线程 Looper 在 `ActivityThread.main` 启动。Handler 持 Activity 导致的**内存泄漏**是经典考点(用静态内部类 + 弱引用规避)。

## 考核记录
（尚未考核）
