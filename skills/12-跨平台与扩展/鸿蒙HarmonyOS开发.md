---
title: 鸿蒙 HarmonyOS 开发
domain: 12-跨平台与扩展
level: 了解
target: 熟悉
importance: 高
last_assessed:
last_reviewed: 2026-07-27
next_review: 2026-08-26
tags: [鸿蒙, HarmonyOS, ArkTS, ArkUI, HMS]
related: [Jetpack Compose, Kotlin Multiplatform 与 Compose Multiplatform]
---

# 鸿蒙 HarmonyOS 开发

## 概述
华为自研**全场景分布式操作系统**,面向手机/平板/穿戴/车机/IoT 多端,**一次开发多端部署**是其核心卖点。对 Android 工程师价值有二:一是国内招聘大量出现「Android/鸿蒙复合岗」,属于**刚需扩展**;二是技术栈高度同源——ArkUI 与 Jetpack Compose 同为**声明式 UI**(UI = f(state)),ArkTS 是 TypeScript 超集,迁移心智成本低。关键分水岭是 **HarmonyOS NEXT(纯血鸿蒙)**:彻底去掉 AOSP 与安卓兼容层,全自研内核 + ArkTS 原生,不再能跑安卓 APK;自此鸿蒙不再是「安卓套壳」,而是独立生态。与 KMP/Compose Multiplatform 的区别:鸿蒙是**整套 OS + SDK + IDE + 应用市场**的垂直闭环,而非跨平台框架。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 鸿蒙定位与生态
- **HarmonyOS**:华为商用发行版,含闭源 **HMS Core**、系统服务、专属应用,面向消费者设备。
- **OpenHarmony**:开源底座(捐给开放原子开源基金会),HarmonyOS 基于它构建;其他厂商也可基于 OpenHarmony 做自己的发行版。
- **HarmonyOS NEXT(纯血鸿蒙)**:去 AOSP/去 Java/去安卓兼容,**全自研内核 + ArkTS 原生**,旧版双框架(兼容安卓)逐步退出;这是鸿蒙真正「独立」的标志。
- **一次开发多端部署**:同一套 ArkTS/ArkUI 代码适配多设备,靠**自适应布局/响应式布局 + 多端 Profile**;分布式能力让应用可跨端迁移协同。
- **生态现实**:国内华为设备保有量大,招聘出现大量「Android + 鸿蒙」复合岗;海外份额有限,定位偏国内市场。

### 2. ArkTS 语言
**TypeScript 超集**,在 TS 静态类型基础上加强约束 + 扩展声明式 UI 能力,是鸿蒙 NEXT 的主语言。

- **比 TS 更严格**:禁用 `any`、限制动态对象结构(对象字面量需符合声明类型、不能随意加属性)、禁 `Object` 索引随意访问——为编译期优化与运行时性能。
- **状态驱动装饰器**(核心心智):
  - `@State`:组件内私有状态,变化触发该组件**重新渲染**。
  - `@Prop`:父 → 子**单向**同步(父变子变,子变不回传),值拷贝。
  - `@Link`:父子**双向**同步(引用联动),需父传 `$var`。
  - `@Provide` / `@Consume`:**跨层级**共享(类 CompositionLocal),祖先 Provide、后代 Consume。
  - `@Observed` + `@ObjectLink`:**嵌套对象/数组元素**的深度观测(单独 `@State` 不观测二层属性变化)。
  - `@Watch`:监听状态变化触发回调(类 `SideEffect`/观察)。
- **心智对比**:Kotlin(可空/协程)、Swift UI(`@State` 同名概念、同源思想)、Compose(`remember`/`mutableStateOf` ↔ `@State`)。

### 3. ArkUI 声明式 UI
与 Compose **同源**的声明式框架,UI = f(state),状态变 → 框架刷新受影响部分。

- **核心装饰器**:`@Entry`(页面入口)、`@Component`(自定义组件,类 `@Composable`)、`@Builder`(抽取构建片段,可复用,类小组件)、`@Styles` / `@Extend`(复用样式/扩展原生组件属性)。
- **布局**:`Row` / `Column` / `Stack` / `Flex` / `Grid` / `List` / `RelativeContainer`(类 Row/Column/Box/Flex/LazyColumn)。
- **条件与循环**:`if/else` 条件渲染、`ForEach`(列表渲染,需给 `keyGenerator` 做差分,类 Compose `key`)。
- **动画**:`animateTo`(状态驱动的隐式动画)、显式动画 API;`@AnimatableExtend` 自定义动画属性。
- **与 Jetpack Compose 对照**:

| 概念 | Compose | ArkUI |
|-----|---------|-------|
| 组件单元 | `@Composable` 函数 | `@Component struct` |
| 组件内状态 | `remember { mutableStateOf() }` | `@State` |
| 父→子单向 | 普通参数 + 回调 | `@Prop` |
| 父子双向 | 状态提升 + 回调 | `@Link` |
| 跨层级 | `CompositionLocal` | `@Provide/@Consume` |
| 副作用 | `LaunchedEffect`/`DisposableEffect` | `aboutToAppear`/`aboutToDisappear` 等生命周期回调 |
| 列表渲染 | `LazyColumn` + `items(key)` | `List` + `ForEach` + `keyGenerator` |

- **差异**:ArkUI 组件是 `struct` + 装饰器(非函数),状态用装饰器标注而非 `remember`;重组粒度机制不同(按 `@State` 依赖追踪)。

### 4. Stage 模型与应用结构
HarmonyOS NEXT 主推的应用模型(**FA 模型旧版已弃用**),提供更清晰的生命周期与多 Ability 能力。

- **UIAbility**:UI 界面承载单元,**类比 Activity 但生命周期不同**:
  - `onCreate` → `onWindowStageCreate`(创建窗口、加载页面)→ `onForeground`(前台)→ `onBackground`(后台)→ `onWindowStageDestroy` → `onDestroy`。
  - 与 Activity 区别:窗口与 UI 单元分离,一个 UIAbility 可加载多个页面(靠页面栈 `router`/`Navigation`)。
- **AbilityStage**:HAP 级应用入口,对应一个 **HAP 模块**的加载,可做模块级初始化。
- **ExtensionAbility**:扩展能力(非主 UI),如**服务卡片**、输入法、备份等后台/系统型扩展。
- **包结构**:
  - **HAP**(Harmony Ability Package):**主模块**,可独立安装运行,含一个入口 Ability。
  - **HSP**(Harmony Shared Package):**动态共享包**,多模块/多应用间按需加载(类动态 feature module)。
  - **HAR**(Harmony Archive):**静态共享库**,编译期被依赖方打包进去(类 AAR)。
- **`module.json5`**:模块配置清单(**类比 AndroidManifest.xml**),声明 Ability、权限、设备类型、入口页面等。

### 5. 系统能力与分布式
- **分布式软总线**:设备发现/自组网/高速连接,是鸿蒙分布式底座;上层实现**跨端迁移**(应用从手机迁到平板继续)与**多端协同**(多设备协同操作)。
- **分布式数据 / 调度**:跨设备数据同步与任务调度,App 看到的是「超级终端」而非单机。
- **HMS Core**:华为移动服务(推送/定位/支付/账号/地图等),**类 GMS**;鸿蒙 NEXT 用 **HMOS** 原生服务能力替代部分 HMS。
- **权限模型**:Stage 模型权限更细粒度,分 `normal`/`system_basic`/`system_core` 等级别;部分敏感权限需动态申请 + 用户授权。
- **原子化服务 / 服务卡片**:免安装的轻服务 + 桌面卡片(**类 App Widget / Live Activity**),基于 ExtensionAbility 实现。

### 6. 工具链与发布
- **DevEco Studio**:基于 IntelliJ 的**官方 IDE**(类 Android Studio),含编辑/预览/调试/模拟器。
- **HVigor**:官方构建工具(**类 Gradle**),`hvigor` 命令 + `build-profile.json5` 配置;非 Groovy/KTS。
- **Previewer**:实时 UI 预览(类 Compose Preview),支持多设备尺寸。
- **模拟器与真机**:本地/远程模拟器,真机需开发者账号 + 调试签名。
- **签名与上架**:`.p12`(密钥库)/ `csr`(证书请求)/ **Profile**(描述文件,类 iOS provisioning);经 **AppGallery Connect** 上架华为应用市场。
- **调试**:`hilog`(系统日志,类 `logcat`)、DevEco Profiler、`hdc`(设备命令,类 `adb`)。

### 7. Android 开发者迁移要点
**概念映射表**(迁移速记):

| Android | HarmonyOS |
|---------|-----------|
| `Activity` | `UIAbility` |
| `Application` | `AbilityStage` / `AbilityStage` 中的上下文 |
| `Fragment` / Composable | `@Component` 自定义组件 |
| Compose `@Composable` | `@Component struct` |
| `AndroidManifest.xml` | `module.json5` |
| Gradle | HVigor |
| `adb` | `hdc` |
| `logcat` | `hilog` |
| AAR | HAR |
| GMS | HMS Core / HMOS |

- **常见坑**:
  1. **ArkTS ≠ 普通 TS**:`any` 被禁、对象结构受限、不能随意 `JSON.parse` 后当强类型用——TS 老代码迁移需重构。
  2. **状态管理心智差**:`@State`/`@Prop`/`@Link`/`@Observed` 各管一摊,嵌套对象不 `@Observed` 不刷新(类 Compose 不稳定类型不重组)。
  3. **生命周期对不上**:UIAbility 没有 Activity 的 `onResume`/`onPause` 粒度,窗口与前后台分离,迁移时别硬套。
  4. **生态库少**:三方库远少于 Android/JVM,很多能力要找鸿蒙官方 SDK 或自己写。
  5. **API 版本碎片**:HarmonyOS 与 OpenHarmony API 版本、NEXT 与旧版双框架差异大,选 target API level 要看清兼容矩阵。

## 实践经验 / 踩坑
1. **`@State` 不观测嵌套对象** —— 对象的二层属性变化不触发刷新。给类加 `@Observed`、子组件用 `@ObjectLink` 接收(类 Compose 给类加 `@Immutable`/拆分)。
2. **`ForEach` 忘 `keyGenerator`** —— 列表增删时复用错位、状态串项(同 Compose `LazyColumn` 忘 `key`)。务必给稳定 key。
3. **ArkTS 当 TS 写** —— 用 `any`、动态加属性、`Object` 索引访问,编译期就报错。要按声明式 + 静态强类型思路写。
4. **跨端迁移不可逆假设** —— 分布式迁移依赖数据同步,弱网/数据未就绪会失败;别假设迁移后状态一定一致,要做幂等与校验。
5. **HSP vs HAR 选错** —— HAR 编进每个依赖方(体积膨胀),HSP 动态共享但运行时加载;共用大模块优先 HSP。
6. **权限申请时机** —— 敏感权限在 `module.json5` 声明 + 运行时 `requestPermissionsFromUser`;漏声明直接崩。

## 待深入 / 下一步
- [ ] 用 DevEco Studio 跑通第一个 ArkUI 页面,对照 Compose 写法
- [ ] 实操一个 `@State` + `@Link` + `@Provide` 的状态流案例
- [ ] 看一次分布式跨端迁移的官方 demo,理清软总线调用链
- [ ] 对比 `module.json5` 与 `AndroidManifest.xml` 的权限/组件声明
- [ ] 跟一次 HarmonyOS NEXT 与旧版(双框架)的差异,理清迁移代价

## 参考资料
- 鸿蒙官方开发者:https://developer.huawei.com/consumer/cn/harmonyos/
- ArkTS/ArkUI 文档:https://developer.huawei.com/consumer/cn/arkui/
- OpenHarmony 开源项目:https://www.openharmony.cn/
- AppGallery Connect:https://developer.huawei.com/consumer/cn/agconnect/
- 分布式能力:https://developer.huawei.com/consumer/cn/distributed/
