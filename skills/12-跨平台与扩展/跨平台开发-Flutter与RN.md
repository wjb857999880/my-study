---
title: 跨平台开发(Flutter/RN)
domain: 12-跨平台与扩展
level: 了解
target: 了解
importance: 低
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-12-29
tags: [Flutter, RN, 跨平台]
related: [Kotlin Multiplatform 与 Compose Multiplatform]
---

# 跨平台开发(Flutter/RN)

## 概述
另两类主流跨平台方案:**Flutter**(Google,Dart,自绘引擎,一套代码多端 UI 高度一致、性能接近原生)、**React Native**(Meta,JS / TS,桥接原生组件,生态大、可复用前端技能)。定位:一套代码多端发布,降低多端团队成本;代价是包体积增大、部分原生能力需桥接、性能 / 体验与原生有差距。高级 Android 了解其原理与取舍即可,看岗位方向决定深度。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 跨平台方案谱系
- **自绘 UI**:Flutter(Skia / Impeller)、Compose Multiplatform(Skiko)——不依赖原生控件,一套渲染。
- **原生桥接**:React Native——JS 写逻辑,渲染映射到原生控件。
- **Web 容器**:Ionic / Capacitor——WebView 套壳。

### 2. Flutter 架构
Google 出品,**Dart** 语言 + 自绘引擎(原 Skia,现 Impeller)。Widget 树描述 UI、引擎每帧重绘;JIT(开发热重载)/ AOT(发布)双编译模式。一套代码多端 UI 高度一致、性能接近原生。

### 3. React Native 架构
Meta 出品,**JS / TS** 写逻辑。旧架构靠 **Bridge** 异步在 JS 与原生线程间通信(性能瓶颈);**新架构(Fabric 渲染器 + TurboModule + JSI)** 同步通信、性能大幅改善。渲染映射到原生控件。

### 4. 性能与体验对比
Flutter 自绘性能稳定但与原生控件不一致;RN 新架构改善后接近原生,但依赖桥接与原生模块质量。两者启动需加载引擎 / JS bundle,**冷启动普遍慢于纯原生**。

### 5. 生态与团队技能复用
Flutter 生态由 Google 主导、Dart 门槛中等;RN 生态大(NPM)、可复用前端 / React 技能、招人相对容易。选型常取决于团队既有技能栈。

### 6. 包体积与启动
跨平台框架要内嵌引擎 / runtime / bundle,**包体积通常大于纯原生**(见 [[包体积优化]]);启动需初始化 runtime,冷启动更慢。

### 7. 原生能力与插件
深度原生能力(蓝牙、相机高级特性、平台 SDK)仍需写原生代码 + 插件桥接。插件质量参差是主要维护成本所在。

### 8. 选型(团队 / 岗位方向决定深度)
高级 Android 了解原理与取舍即可。若岗位是 Flutter / RN 团队需深入;若是原生团队,KMP 路线(Kotlin 单语言)可能更契合。国内动态化受限(商店政策)也影响选型。

## 实践经验 / 踩坑

1. **自绘 UI 与原生不一致**:无障碍、输入法、系统手势适配需额外处理。
2. **冷启动慢**:需加载引擎 / JS bundle;用预加载 / 分包优化。
3. **插件质量参差**:深度原生功能仍要写原生代码,维护成本在桥接层。
4. **包体积大**:带引擎 / runtime,需裁剪、按需打包。
5. **性能调优方式不同**:Flutter 用 DevTools / 帧分析;RN 关注 JS bundle 与新架构切换。

## 待深入 / 下一步
- [ ] Flutter Impeller 渲染引擎
- [ ] RN 新架构(Fabric / TurboModule / JSI)
- [ ] Flutter / RN 与 KMP 共享逻辑的对比
- [ ] 动态化与商店政策限制

## 参考资料
- Flutter 官网:https://flutter.dev/
- React Native 官网:https://reactnative.dev/
- RN 新架构:https://reactnative.dev/docs/the-new-architecture/intro
- Flutter 性能:https://docs.flutter.dev/performance