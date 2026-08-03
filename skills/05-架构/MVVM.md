---
title: MVVM
domain: 05-架构
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-05-01
next_review: 2026-08-26
tags: [架构]
related: [MVI, ViewModel]
---

# MVVM

## 概述
**MVVM(Model-View-ViewModel)** 是 Android 主流架构:View 订阅 ViewModel 暴露的**可观察状态**,状态变了 UI 自动刷新;ViewModel 持有 UI 状态与逻辑、**不持有 View 引用**(松耦合),生命周期上跨配置变更存活。数据单向流动——用户操作交给 VM、VM 改状态、状态回灌 View。配合 Repository 数据层与依赖注入,职责清晰、可测试。它是 Kotlin/协程时代以 `StateFlow`/`ViewModel` 为核心的现代形态,也是 MVI 的基础。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. MVVM 是什么 / 解决什么

- **Model**：数据层(Repository/DataSource),负责业务数据与持久化。
- **View**：UI(Activity/Fragment/Compose),订阅状态、渲染、把用户操作转发给 VM。
- **ViewModel**：持有 UI 状态 + 逻辑,**不持有 View 引用**;暴露可观察状态。

对比 **MVC**(Controller 臃肿、View 难测)和 **MVP**(Presenter 通过接口回调「调 View 方法」,仍是命令式耦合):MVVM 靠「**观察状态**」解耦——View 主动订阅,而非被动被调用。核心收益:可测试(VM 无 View 依赖可单测)、配置变更不丢状态。

### 2. 数据驱动与单向数据流

**UI = f(state)**:View 根据 VM 的状态渲染,状态变化 → View 自动更新。单向数据流:用户操作 → VM → 改 state → 新 state 回灌 View;View 不直接改数据源。区别于 MVP「VM 调 `view.setX()`」,这里是 View「订阅 `vm.state` 自己渲染」。

### 3. ViewModel 生命周期

Android `ViewModel` 存于 `ViewModelStore`(每个 Activity/Fragment 一个),**配置变更(如旋转)时 Activity 重建但 ViewModel 保留**,直到 Activity 真正 finish(或 Fragment detach)才 `onCleared()`。因此:

- **不要在 VM 持有 View/Activity 引用**(旋转时旧 Activity 会被泄漏)。
- `viewModelScope`:绑定 VM 生命周期的协程作用域,VM 销毁时自动取消。
- Compose 用 `viewModel()`(LocalViewModelStoreOwner)获取,同样跨配置变更存活。

### 4. 状态暴露：LiveData → StateFlow / SharedFlow

- **LiveData**:生命周期感知、简单,但不擅长协程/背压/线程切换,有 `postValue` 竞态坑;Kotlin 协程时代退居二线。
- **StateFlow**:热的、持一个最新值、自动 conflate(相同值不重复发)、协程原生 → 适合暴露 **UI 状态**。VM 内 `MutableStateFlow`,对外暴露只读 `StateFlow`。
- **SharedFlow**:热的、向多订阅广播、可配 replay → 适合 **事件**。
- StateFlow 比 LiveData 更搭协程:背压、操作符、与 Flow 生态统一、无 `postValue` 竞态。

### 5. UI State 设计 + 状态 vs 事件

- **单一数据源(single source of truth)**:一个屏幕一个 `UiState`,VM 持有并暴露。
- 用 sealed/data class 表达:`sealed interface UiState { Loading; Success(...); Error(...) }`。
- **状态(可重放)** vs **事件(一次性)** 必须分开:
  - 状态(「加载中」「数据」)→ `StateFlow`,配置变更后 View 拿最新值继续渲染。
  - 事件(「弹一次 toast」「导航一次」)→ **`SharedFlow`/`Channel`**;用 `StateFlow` 会 conflate 最新值、配置变更后**重复触发**(经典坑)。

```kotlin
class MyVm(private val repo: Repo) : ViewModel() {
    private val _state = MutableStateFlow<UiState>(UiState.Loading)
    val state = _state.asStateFlow()                        // 只读对外

    private val _events = MutableSharedFlow<UiEvent>(extraBufferCapacity = 8)
    val events = _events.asSharedFlow()                     // 一次性事件

    fun load() = viewModelScope.launch {
        _state.value = UiState.Loading
        _state.value = try {
            UiState.Success(repo.fetch())
        } catch (e: Exception) {
            _events.emit(UiEvent.Toast(e.message ?: "失败"))
            UiState.Error(e.message ?: "失败")
        }
    }
}
```

### 6. 数据层 Repository + 单向依赖链

- **Repository**:聚合数据源(网络/DB/缓存),提供领域数据、屏蔽来源细节。
- 单向依赖:**View → ViewModel → Repository → DataSource**。VM 不直接碰 Retrofit/Room,只调 Repository。
- Repository 出**领域数据**,VM 把它转成 **UiState**;Repository 不该知道 UI。

### 7. 依赖注入与可测试性

VM 依赖 Repository,通过 **Hilt**(`@HiltViewModel` + `@Inject`)或 Dagger/手动 factory 注入。可测试性是核心收益:VM 无 View 依赖,单测注入 fake Repository 即可测状态流转。

### 8. 单向数据流与 MVI

**MVI(Model-View-Intent)** 是 MVVM 的严格变体:View 发 **intent**(意图)→ 经 **reducer** 纯函数产出**新 state** → 状态单向下;state 不可变、唯一、单向。它把 MVVM「VM 里散落的状态修改」收敛成「intent → reducer → state」,更可预测、易测、易回放,代价是样板代码。MVVM 是基础,MVI 是其纪律化形态;Kotlin 时代用 `StateFlow` + sealed intent 实现 MVI 很自然。

## 实践经验 / 踩坑

1. **VM 持有 View/Activity 引用** —— 配置变更时旧 Activity 泄漏 + 耦合。VM 只暴露状态/事件。
2. **层级错乱** —— UI 逻辑塞进 View、或业务塞进 View。View 只渲染+转发,业务在 VM/Repository。
3. **暴露可变状态** —— 对外暴露 `MutableStateFlow`,View 能直接改、破坏单向。对外暴露只读(`asStateFlow()`)。
4. **一次性事件用 StateFlow** —— 配置变更后重复触发(旋转后 toast 再弹)。事件用 `SharedFlow`(replay=0)/`Channel`。
5. **Repository 混 UI 状态** —— 数据层不纯、难复用。Repository 出领域数据,VM 转 UiState。
6. **VM 里主线程重活** —— 用 `viewModelScope` + 切 IO/Default。
7. **state 散落多个流** —— 难追踪、易不一致。聚合成单一 `UiState`(`combine` 或一个 data class)。

## 待深入 / 下一步
- [ ] 读 `ViewModel` / `ViewModelStore` / `SavedStateHandle` 实现
- [ ] MVI 实战(intent → reducer → state)
- [ ] Hilt 注入链(`@HiltViewModel` 生成 factory)

## 参考资料
- Guide to app architecture:https://developer.android.com/topic/architecture
- ViewModel:https://developer.android.com/topic/libraries/architecture/viewmodel
- StateFlow / SharedFlow:https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/
- Hilt:https://developer.android.com/training/dependency-injection/hilt-android