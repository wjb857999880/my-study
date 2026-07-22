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
