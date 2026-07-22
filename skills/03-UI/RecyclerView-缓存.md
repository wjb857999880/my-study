---
title: RecyclerView 四级缓存
domain: 03-UI
level: 掌握
target: 精通
importance: 中
last_reviewed: 2026-06-22
next_review: 2026-07-22
tags: [列表, 缓存]
related: [ListView]
---

# RecyclerView 四级缓存

## 概述
RecyclerView 通过 Scrap/ mAttachedScrap / mCachedViews / ViewCacheExtension / RecycledViewPool 多级复用 ViewHolder，降低滑动时创建/绑定开销。

## 自评依据  ★必填
读过源码、能讲清四级缓存的命中流程和 setHasFixedSize、prefetch 的作用，
也在项目里做过列表性能优化；差在对多类型 + 共享 Pool 的高阶场景还没踩透，所以是"掌握"非"精通"。
