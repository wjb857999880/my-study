---
title: 自定义 View 与绘制流程
domain: 03-UI
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [自定义View, 绘制, measure]
related: [RecyclerView 四级缓存]
---

# 自定义 View 与绘制流程

## 概述
自定义 View 的核心是掌握**三大绘制流程**:`measure`(测量,MeasureSpec)、`layout`(定位)、`draw`(绘制,Canvas/Paint)。进阶:ViewGroup 测量与布局子 View、`onDraw` 性能(避免分配对象)、硬件加速、`invalidate`/`requestLayout` 的区别、滑动(Scroller / 嵌套滑动 NestedScrolling)。是高级 UI、动画与复杂交互的基础。

## 考核记录
（尚未考核）
