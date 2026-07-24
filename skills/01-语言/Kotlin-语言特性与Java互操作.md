---
title: Kotlin 语言特性与 Java 互操作
domain: 01-语言
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [Kotlin, 语法, 互操作]
related: [Kotlin 协程]
---

# Kotlin 语言特性与 Java 互操作

## 概述
Kotlin 是 Android 官方首选语言,核心特性:**空安全**(类型系统区分可空 / 非空,编译期防空指针)、**扩展函数**(给已有类加方法)、**数据类**(自动生成 equals/hashCode/toString/copy)、**密封类 / sealed interface**(受限类型层级,配合 when 穷举)、**作用域函数**(let/run/apply/also)、**默认参数 + 命名参数**、**智能类型转换**。与 Java 互操作:Kotlin 可无缝调 Java,但要注意可空性**平台类型(platform type)**、`@JvmStatic`/`@JvmField`/`@JvmOverloads` 供 Java 调用方、集合可变性差异。

## 考核记录
（尚未考核）
