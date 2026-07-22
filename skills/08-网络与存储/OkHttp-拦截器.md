---
title: OkHttp 拦截器
domain: 08-网络与存储
level: 掌握
target: 精通
importance: 中
last_reviewed: 2026-07-05
next_review: 2026-10-03
tags: [网络, 拦截器]
related: [Retrofit]
---

# OkHttp 拦截器

## 概述
OkHttp 通过责任链模式的拦截器链完成重试、桥接、缓存、连接、网络请求等，用户可插入自定义拦截器统一处理日志/鉴权/重试。

## 自评依据  ★必填
写过自定义拦截器做统一鉴权与日志、读过责任链源码，能讲清调用顺序；
差在连接池/缓存策略的底层细节，所以是"掌握"非"精通"。
