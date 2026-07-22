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
