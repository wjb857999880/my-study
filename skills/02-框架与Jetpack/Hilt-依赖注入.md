---
title: Hilt 依赖注入
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [Hilt, DI, Dagger]
related: [MVVM, 移动端架构设计]
---

# Hilt 依赖注入

## 概述
依赖注入(DI)把对象的创建与使用解耦,便于测试与降低耦合。**Hilt 基于 Dagger**、针对 Android 简化:用 `@HiltAndroidApp` + `@AndroidEntryPoint` + `@Inject`/`@Module`/`@Provides` 声明依赖,编译期自动生成装配代码。常见:注入 Repository / ViewModel / Retrofit,替换实现做单元测试。需理解作用域(`@Singleton` / `@ActivityScoped` 等)与组件层次。

## 考核记录
（尚未考核）
