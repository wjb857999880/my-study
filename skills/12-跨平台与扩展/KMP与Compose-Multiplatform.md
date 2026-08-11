---
title: Kotlin Multiplatform 与 Compose Multiplatform
domain: 12-跨平台与扩展
level: 了解
target: 精通
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-12-27
tags: [KMP, Compose Multiplatform, 跨平台]
related: [Kotlin 语言特性与 Java 互操作, Jetpack Compose]
---

# Kotlin Multiplatform 与 Compose Multiplatform

## 概述
**KMP**(Kotlin Multiplatform)把业务逻辑(网络 / 数据 / 领域层)用 Kotlin 写一次、编译到多端(iOS / Android / 桌面 / Web),UI 各端原生;**Compose Multiplatform** 进一步把 UI 也用 Compose 跨端(iOS / Desktop / Web)。定位:KMP 共享逻辑、Compose MP 共享 UI,介于「纯原生」与「Flutter / RN」之间。2026 外企与新项目强加分。需理解共享模块架构、**expect / actual** 机制、各端差异处理与原生互操作。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 跨平台谱系与 KMP 定位
跨平台方案谱系:**纯原生**(体验最佳、多端成本高)→ **KMP**(共享逻辑、UI 各端原生)→ **Compose Multiplatform**(共享 UI)→ **Flutter / RN**(共享 UI,自绘或桥接)→ Web 容器。KMP 走「共享业务逻辑」路线,是 Kotlin 团队 + Google 官方支持的方向。

### 2. KMP:共享逻辑,UI 各端原生
把**网络、数据、领域逻辑**用 Kotlin 写在 `commonMain`,编译到 Android(ART)、iOS(Native)、Desktop(JVM)、Web(Wasm / JS);UI 层各端用原生(Android Compose、iOS SwiftUI)。减少重复逻辑、保留各端原生体验。

### 3. 共享模块架构
KMP 工程用 source set 分层:`commonMain`(公共)、`androidMain` / `iosMain` / …(平台特定)。共享代码尽量下沉 commonMain,平台差异用 expect / actual 或依赖注入隔离。KMP 已被 Google 官方支持、**生产就绪**。

### 4. expect / actual 机制
`commonMain` 用 `expect fun` / `expect class` 声明「期望」的 API,各平台在 `actual` 里提供真实实现(如 `expect fun now(): Long`,各端各自 actual)。编译期保证每个 expect 都有匹配的 actual,链接安全。

### 5. Compose Multiplatform:共享 UI
把 Jetpack Compose 跨端到 iOS / Desktop / Web。**重要里程碑:Compose Multiplatform for iOS 自 1.8.0(2025-05)起 Stable**,Android / iOS / Desktop 均生产就绪,Web 仍在推进。一套 Compose UI 多端渲染。

### 6. 与原生互操作
- 各端调用原生 API:iOS 用 interop / `@ObjCName`、Android 直接用。
- 依赖库需提供 KMP 变体(multiplatform);非 KMP 库只能在平台侧用。
- 状态 / 协程跨平台:KMP 支持 kotlinx.coroutines / Flow 多端。

### 7. KMP vs Flutter/RN vs 纯原生
- **纯原生**:体验 / 性能 / 生态最佳,成本最高。
- **KMP(+ 各端原生 UI)**:共享逻辑、原生体验,Kotlin 单语言、与 Android 团队技能契合。
- **Compose MP**:进一步共享 UI,iOS 仍是自绘(非原生控件)。
- **Flutter / RN**:一套 UI 多端,生态独立(Dart / JS)。

### 8. 何时用 / 风险与成熟度
适合「多端、逻辑复杂、团队有 Kotlin 基础」的项目(尤其 Android + iOS)。风险:iOS Compose 自绘与原生控件细节差异、工具链学习成本、部分库缺 KMP 支持。新项目 / 外企强加分;存量原生项目宜逐步引入共享模块。

## 实践经验 / 踩坑

1. **共享不是零成本**:KMP 共享逻辑,但各端仍有差异(UI、平台 API),别期望「一份代码完全无差别」。
2. **expect / actual 编译约束**:每个 expect 必须有匹配 actual,签名不符编译报错;改名要同步。
3. **依赖库支持**:引入库要看是否提供 multiplatform 变体;只支持 JVM 的库不能进 commonMain。
4. **Compose iOS 自绘**:非原生 UI 控件,无障碍、输入法、系统主题适配需额外处理。
5. **调试链路长**:跨端问题定位成本高,Xcode + Android Studio 工具链学习曲线陡。

## 待深入 / 下一步
- [ ] KMP 的并发 / 协程跨平台(kotlinx.coroutines Native)
- [ ] Skiko(Compose 多平台渲染后端)原理
- [ ] KMP 依赖管理(版本目录、cocoapods / SPM 互操作)
- [ ] 企业级落地:渐进式迁移存量原生项目

## 参考资料
- Kotlin Multiplatform:https://kotlinlang.org/docs/multiplatform.html
- KMP 支持平台与稳定度:https://kotlinlang.org/docs/multiplatform/supported-platforms.html
- Compose Multiplatform:https://github.com/JetBrains/compose-multiplatform
- Compose MP 1.8(iOS Stable,2025-05):https://blog.jetbrains.com/kotlin/2025/05/compose-multiplatform-1-8-0-released-compose-multiplatform-for-ios-is-stable-and-production-ready/