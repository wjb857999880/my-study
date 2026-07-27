---
title: MVI 与 Clean Architecture
domain: 05-架构
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-27
next_review: 2026-08-26
tags: [MVI, Clean Architecture, 单向数据流, 分层架构]
related: [MVVM, 组件化与模块化, Kotlin Flow 与响应式编程]
---

# MVI 与 Clean Architecture

## 概述
**MVI(Model-View-Intent)** 是 MVVM 的纪律化变体:用**单一不可变 `UiState`** 收敛「散落的多 LiveData/Flow」,用户操作抽象成 **Intent**,经纯函数 reducer 产出新 state,形成**单向数据流(UDF)**——状态可预测、可序列化、易回放易测。**Clean Architecture** 是整体分层方案:presentation/domain/data 三层,**依赖方向恒指向 domain**,domain 为纯 Kotlin 不依赖任何框架,可独立测试与多端复用。两者正交可叠加:MVI 管 presentation 层的状态纪律,Clean 管全工程的分层与依赖规则。大厂(规模化团队、多模块工程)常以此标配,换取**可测、可协作、可演进**。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 为什么需要 MVI(MVVM 的状态散落/事件歧义)
- MVVM 实践中常见**多个 LiveData/StateFlow 散落**(`isLoading`、`data`、`error`、`showDialog`…):状态组合可能产生**非法中间态**(loading=true 同时有 data),UI 渲染依赖多个流的时序,**竞态难复现**。
- **事件 vs 状态混淆**:Toast/导航这种「一次性」塞进 `StateFlow`,旋转后**重复触发**(conflate 最新值重放);分不清就出 bug。
- MVI 主张**唯一可信状态(single source of truth)**:整屏一个不可变 `UiState`,任何变化都由 **Intent** 经 reducer 显式推导 → 状态如**状态机**,可序列化、可回放、可单测。
- 收益:**可预测**(状态流转唯一路径)、**可调试**(打日志即 timeline)、**易测**(reducer 纯函数 `assert(state+intent == newState)`)。

### 2. MVI 三要素与单向数据流
- **Model** = 不可变 `UiState`(整屏一个 `data class`,字段覆盖全部 UI);用 `val` + `copy` 保证不可变。
- **Intent** = 用户意图,**纯数据**(sealed class),如 `LoadClick` / `SubmitClick(text)` / `RetryClick`;**不含逻辑**,只描述「想要做什么」。
- **View** = 渲染当前 `UiState` + 把用户操作包装成 Intent 发给 VM/Store。
- **单向数据流(UDF)** 一个闭环,无反向:
  - 用户操作 → View 发 **Intent**
  - VM/Store 处理 Intent → 经 reducer 产出**新 state**
  - 新 state → View 渲染
- 禁止 View 直接改 state、禁止 state 反向回流;所有变更**必须过 Intent**。

```kotlin
data class LoginUiState(              // Model:整屏唯一不可变状态
    val email: String = "",
    val password: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
)

sealed interface LoginIntent {        // Intent:纯数据,sealed 穷尽
    data class EmailChanged(val v: String) : LoginIntent
    data class Submit(val email: String, val pwd: String) : LoginIntent
}
```

### 3. Reducer 与副作用 Effect
- **reducer** = 纯函数 `(state, intent) -> state`:给定旧 state + intent,确定地算出新 state,**无副作用、不发网络、不弹 UI**。逻辑收敛于此,极易单测。
- 实操中 reducer 常分两层:**纯状态转移**(同步 `when`)+ **异步处理**(suspend 拉数据后再次 reducer);Hannes Dorfmann 的 Mosby MVI 即 `(state, intent) -> state` 风格。
- **副作用 Effect** = 一次性事件(导航、Toast、弹窗、滚动),**不能放进 `UiState`**——否则状态重放会重复触发。常用 `SharedFlow<Effect>`(replay=0)或 `Channel` 暴露,View 订阅消费。
- **MVI vs MVVM**:MVI 更可预测、可测、易回放,代价是**样板多**(每个操作一个 Intent + reducer 分支);MVVM 更灵活轻量。简单页 MVVM,复杂状态机/强一致性页 MVI。

```kotlin
private fun reduce(state: LoginUiState, intent: LoginIntent) = when (intent) {
    is LoginIntent.EmailChanged -> state.copy(email = intent.v, error = null)
    is LoginIntent.Submit       -> state.copy(isLoading = true)
}
```

### 4. Clean Architecture 分层与依赖规则
- **三层**:
  - **presentation**:Activity/Fragment/Compose/ViewModel/UiState —— 知道 Android,消费 domain。
  - **domain**:`Entity`(业务实体)+ `UseCase`(用例)+ `Repository` **接口** —— **纯 Kotlin,无 Android/DB/Retrofit 依赖**。
  - **data**:`Repository` 实现 + `DataSource`(网络/DB/缓存)+ mapper —— 实现 domain 定义的接口。
- **依赖规则(dependency rule)**:依赖方向**恒指向内层**,外层(data/presentation)依赖内层(domain),**domain 不依赖任何外层**。箭头永远朝 domain。
- **为何 domain 纯 Kotlin**:不被 Android/框架绑架 → 可被多端(后端/KMP/测试)复用、可脱离设备纯 JVM 单测、框架可替换(换网络库/DB 不动 domain)。
- **Entity vs DTO/UiState**:Entity 是领域业务实体(domain),DTO 是网络/DB 传输对象(data),UiState 是视图状态(presentation);层间用 mapper 转换,不串味。

### 5. 落地:模块化 + Hilt + UseCase + Repository
- **多模块(modularization)**:按层/feature 拆模块(`:feature:login`、`:domain`、`:data`、`:core`),**依赖方向由 Gradle 编译期强制**(data 依赖 domain,domain 不依赖任何东西)——架构错误编译就失败,比纯约定可靠。
- **Hilt** 注入 `Repository`/`UseCase`:`@Module` 提供 Repository 实现绑定到 domain 接口,`@HiltViewModel` 注入 UseCase。
- **UseCase 编排**:单一职责(一个用例一件业务)、`suspend operator fun invoke(...): T`、可组合(一个用例调多个 Repository)、返回 domain Entity;VM 只编排 UseCase 不碰数据源细节。
- **Repository 模式**:data 层屏蔽来源(网络优先 / 缓存回退 / DB 单一来源),对 domain 暴露稳定接口。
- **MVI 与 Clean 的关系**:正交。MVI 是 **presentation 模式**(管 VM/状态),Clean 是**整体分层**(管依赖);可叠加 = Clean 分层 + presentation 层用 MVI。MVVM+Repository 是其简化子集(少 domain 纯模块、少 reducer 纪律)。
- **大厂标配原因**:规模化(多团队并行)、可测(domain 纯单测)、可演进(框架可换)、依赖编译期约束降低腐化速度。

### 6. 与 Compose / Flow 结合
- VM 暴露 `StateFlow<UiState>`(唯一状态源);Compose 端 `collectAsStateWithLifecycle()` 订阅,**生命周期感知、配置变更自动恢复**。
- Intent 通过 VM 公开函数触发:`fun onIntent(i: LoginIntent)`,内部 reducer + 异步处理。
- **副作用**:导航/一次性事件用 `SharedFlow<Effect>`,Compose 端 `LaunchedEffect` 收集;**不要塞 `StateFlow`**(旋转重放)。
- MVI 的「状态驱动」天然契合 **Compose 声明式**:`@Composable (state) -> UI`,无 imperative `setText/setVisibility`,reducer 出新 state → Compose 自动重组。

### 7. 权衡与反模式
- **过度设计**:小项目/简单页套 MVI + Clean,样板(Intent/reducer/mapper/三层)远超收益 → CRUD 页用 MVVM+Repository 即可,按页复杂度选模式。
- **状态过大**:整屏一个巨型 `UiState`,Compose 局部重组浪费(任一字段变都 copy 整对象)→ **拆分 feature state** 或用 Compose 的 `derivedStateOf`/局部状态;大 state 用 `copy` 也要注意。
- **巨型 reducer**:`when (intent)` 几百分支 → 按功能拆 reducer、或部分操作直接走 VM 函数不经 reducer。
- **一次性事件放 StateFlow**:旋转后重放/丢失 → 事件走 `SharedFlow`(replay=0)/`Channel`。
- **无脑套 Clean**:每层一堆 mapper、Entity/DTO/UiState 三套模型,样板爆炸 → 简单域允许 Entity 当 UiState 字段直传,领域复杂再分层。
- **domain 引入 Android 类**(如 `Context`/`Uri`)→ 破坏纯 Kotlin,丧失可测/可复用,严禁。

## 实践经验 / 踩坑
1. **整屏一个巨 state 导致重组浪费** —— 拆 feature state 或局部 `remember`,避免无谓 copy/重组。
2. **一次性事件塞 StateFlow** —— 旋转重放。导航/Toast 走 `SharedFlow`(replay=0)。
3. **domain 模块依赖了 Android/Room/Retrofit** —— 立刻丧失纯 Kotlin 价值;依赖反转,用 domain 接口 + data 实现。
4. **每层全套 mapper 样板爆炸** —— 简单域允许直传,复杂域再分层;mapper 可用映射扩展函数收敛。
5. **reducer 里发网络/弹 UI** —— reducer 不纯,难测、难回放。副作用剥离到 Effect/异步处理。
6. **小项目无脑 MVI+Clean** —— 样板 > 收益。按页/工程复杂度选,简单页 MVVM+Repository 够用。
7. **Intent 携带逻辑**(如在 Intent 里算值) —— Intent 只描述意图,纯数据,逻辑放 reducer/UseCase。

## 待深入 / 下一步
- [ ] 读 Hannes Dorfmann **Mosby MVI** 与 `MviBasePresenter` / `MviReducer` 设计
- [ ] 读 Robert C. Martin **Clean Architecture** 依赖反转章节,对比实体用例边界
- [ ] 实战:Clean 多模块工程 + Hilt 注入 domain 接口 + presentation MVI

## 参考资料
- Guide to app architecture(单向数据流 / UI 层):https://developer.android.com/topic/architecture
- Guide to app architecture(数据层 / domain):https://developer.android.com/jetpack/guide
- Clean Architecture — Robert C. Martin(依赖规则、实体/用例边界)
- Mosby MVI(Hannes Dorfmann):https://github.com/sockeqwe/mosby
- Kotlin Flow / StateFlow:https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/
