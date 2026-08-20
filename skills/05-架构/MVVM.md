---
title: MVVM
domain: 05-架构
level: 精通
target: 精通
importance: 高
last_assessed: 2026-08-20
last_reviewed: 2026-08-20
next_review: 2027-02-16
tags: [架构]
related: [MVI, ViewModel]
---

# MVVM

## 概述
**MVVM(Model-View-ViewModel)** 是 Android 主流架构:View 订阅 ViewModel 暴露的**可观察状态**,状态变了 UI 自动刷新;ViewModel 持有 UI 状态与逻辑、**不持有 View 引用**(松耦合),生命周期上跨配置变更存活。数据单向流动——用户操作交给 VM、VM 改状态、状态回灌 View。配合 Repository 数据层与依赖注入,职责清晰、可测试。它是 Kotlin/协程时代以 `StateFlow`/`ViewModel` 为核心的现代形态,也是 MVI 的基础。

## 考核记录
- **2026-08-20** 判定：(待考核) → 精通 ✅ ｜ 考官：AI
  - 表现：四档全通。了解档三件套职责+MVP对比准确；熟悉档写出 Login VM/Repo/Compose 三层骨架、StateFlow 单向暴露、`viewModelScope` 用法正确，配置变更存活机制讲清；掌握档用 SharedFlow 分离一次性事件、三处典型 bug(VM 持 Activity/暴露 MutableStateFlow/暴露 MutableSharedFlow)全部命中；精通档给出单 StateFlow vs 多 StateFlow+combine 的重组粒度取舍与 8–10 维度的 escalate 策略，SavedStateHandle 讲透机制+落盘路径+判断标准(不存网络结果)。
  - 依据：能讲清架构权衡与原理深挖，达到精通档「能做设计、讲清权衡」标准。

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

## 四档考核 Q&A（2026-08-20）

### 了解档
**Q1: MVVM 三个字母各代表什么？每一层的核心职责是什么？它主要为了解决 Android UI 开发的哪个具体痛点？**

A: M=Model（数据层，负责业务数据与持久化，封装 Repository/DataSource）；V=View（Activity/Fragment/Compose，订阅状态、渲染、把用户操作转发给 VM）；VM=ViewModel（管理 UI 状态 + 逻辑，不持有 View 引用，暴露可观察状态）。痛点：把"UI 渲染"与"业务逻辑 + 数据"解耦，让 VM 可独立单测、配置变更不丢状态，避免 MVC Controller 臃肿、MVP Presenter 与 View 接口耦合难测的问题。

**Q2: 把 MVVM 跟 MVP 对比——同样是"VM/Presenter 不持有 View"，MVVM 的解耦点跟 MVP 有什么本质不同？为什么说 MVVM"可测试性"比 MVP 好？**

A: MVP 的 Presenter 通过 **接口** 主动调 `view.setX()/showError()`——命令式反向调用，Presenter 必须知道 View 的存在（虽通过接口，仍是反向依赖）；MVVM 的 VM 只暴露**可观察状态**，View 自己 `subscribe(vm.state)` 触发渲染——**单向依赖**（View 依赖 VM，VM 不依赖 View）。可测试性差异：MVP Presenter 单测要 mock 整个 View 接口（`verify(view).showError(...)`），耦合测试两端；MVVM VM 单测只需断言状态流转（`assertEquals(expectedState, vm.state.value)`），跟 View 零接触。

---

### 熟悉档
**Q1: 写一个登录页的最小 MVVM 代码骨架——Model/Repository/ViewModel/View，VM 用 `StateFlow` 暴露 UI 状态（loading/success/error），对外只读，View 只负责渲染与转发点击事件。**

A: 三层结构：

```kotlin
// Model 层 —— 领域结果
sealed class LoginResult {
    data class Success(val token: String) : LoginResult()
    data class Error(val message: String) : LoginResult()
}

class LoginRepository {
    suspend fun login(username: String, password: String): LoginResult { /* ... */ }
}

// ViewModel 层 —— 对外只读 StateFlow
data class LoginUiState(
    val isLoading: Boolean = false,
    val success: Boolean = false,
    val error: String? = null
)

class LoginViewModel(
    private val repository: LoginRepository = LoginRepository()
) : ViewModel() {
    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()  // 只读对外

    fun onLoginClick(username: String, password: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            _uiState.value = when (val r = repository.login(username, password)) {
                is LoginResult.Success -> _uiState.value.copy(isLoading = false, success = true)
                is LoginResult.Error   -> _uiState.value.copy(isLoading = false, error = r.message)
            }
        }
    }
}

// View 层（Compose）—— 只渲染 + 转发
@Composable
fun LoginScreen(viewModel: LoginViewModel = viewModel()) {
    val uiState by viewModel.uiState.collectAsState()
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    Button(
        onClick = { viewModel.onLoginClick(username, password) },  // 转发
        enabled = !uiState.isLoading && username.isNotBlank() && password.isNotBlank()
    ) { Text(if (uiState.isLoading) "..." else "登录") }
    uiState.error?.let { Text(it, color = Color.Red) }
}
```

关键点：`MutableStateFlow` 私有，`asStateFlow()` 对外只读；`viewModelScope` 自动取消；View 只 `collectAsState` + 调 VM 方法，不持有 VM 的可变引用。

**Q2: Android 框架里的 `androidx.lifecycle.ViewModel` 跟刚才说的"MVVM 里的 ViewModel"概念有什么不同？它在屏幕旋转这种配置变更下是怎么"活下来"的？什么时候触发 `onCleared()`？**

A: Android `ViewModel` 是 MVVM 概念的**框架实现**，自带生命周期感知（`ViewModelStore` + `NonConfigurationInstances` 机制）。旋转时 Activity 重建但 ViewModelStore 跨配置变更保留，VM 实例不变；用户按 Back `finish()` 或 Fragment `detach()` 真正销毁时触发 `onCleared()`。所以 VM 内部启动的协程、持有的状态都不丢；这就是为什么 VM **不能持有 Activity/View 引用**——旧 Activity 已死但 VM 还活着，会泄漏。

---

### 掌握档
**Q1: 当前 Login VM 把 `success=true` 和 `error=...` 都塞进 `LoginUiState`，导致旋转后会重复显示"登录成功！"或重复触发错误提示。请改造：用一次性事件流（如 `SharedFlow`）发 Toast/导航类事件，UI 状态只保留可重放的渲染数据。**

A: 核心改造：状态与事件**分开**。

```kotlin
sealed class LoginEvent {
    object NavigateToHome : LoginEvent()
}

class LoginViewModel(private val repository: LoginRepository) : ViewModel() {
    // ✅ 状态：可重放，旋转后依然渲染
    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    // ✅ 一次性事件：SharedFlow，UI 收到即消费
    private val _events = MutableSharedFlow<LoginEvent>()
    val events: SharedFlow<LoginEvent> = _events.asSharedFlow()

    fun onLoginClick(username: String, password: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val r = repository.login(username, password)) {
                is LoginResult.Success -> {
                    _uiState.value = _uiState.value.copy(isLoading = false)
                    _events.emit(LoginEvent.NavigateToHome)  // 一次性导航
                }
                is LoginResult.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = r.message  // 留在 state 供重试时显示
                    )
                }
            }
        }
    }
}
```

要点：状态进 `StateFlow`（会被 conflate 但保留最新值，重组时 View 自然拿到），事件进 `SharedFlow`/`Channel`（replay=0，旋转不会重发）。`error` 字段保留在 state 是合理设计——重试时要让用户看到上次失败原因。

**Q2: 下面这段"看起来对"的 MVVM 代码有 3 处典型问题，请找出并说明后果：**

```kotlin
class ProfileViewModel(
    private val repo: ProfileRepository,
    private val activity: AppCompatActivity        // ①
) : ViewModel() {

    val state = MutableStateFlow(ProfileUiState())  // ②
    val event = MutableSharedFlow<String>()         // ③

    fun load() = viewModelScope.launch {
        val result = repo.fetchProfile()
        state.value = ProfileUiState(loading = false, data = result)
    }

    fun showToast(msg: String) = viewModelScope.launch { event.emit(msg) }
}
```

A: 三处问题：

1. **① `activity: AppCompatActivity` 注入到 VM** —— VM 在配置变更时存活，旧 Activity 已被销毁，VM 还引用着 → **内存泄漏**；且 VM 不可单测（没法 new 一个 Activity 给测试）。正确做法：通过 `AndroidViewModel(application)` 拿 Application，或更优——**根本不注入 Activity**，把 Activity 相关逻辑交给 View 层。

2. **② `val state = MutableStateFlow(...)` 直接对外暴露 `MutableStateFlow`** —— View 能 `vm.state.value = newState` 直接改，破坏**单向数据流**。正确：`private val _state = MutableStateFlow(...)` + `val state = _state.asStateFlow()`。

3. **③ `val event = MutableSharedFlow<String>()` 同样对外暴露 Mutable** —— View 能 `vm.event.emit(fakeMsg)` 伪造事件，或绕过 VM 业务逻辑。正确：`private val _event = MutableSharedFlow(...)` + `val event = _event.asSharedFlow()`。

核心原则：对外暴露**只读接口**，所有变更必须走 VM 的方法（保留业务规则 + 可追踪）。

---

### 精通档
**Q1: 设计一个新闻列表页的 ViewModel，屏幕有 6 个独立维度（文章列表带分页、筛选条件、已收藏 id 集合、loading/error、列表项选中态）。你是合并成一个大 `NewsUiState` data class 单一 `StateFlow`，还是多个独立 `StateFlow` + `combine`？选哪种，为什么？如果维度膨胀到 8–10 个，怎么取舍？**

A: **选多个独立 `StateFlow` + `combine`**，并按需聚合：

```kotlin
// 各维度独立流
private val _articles = MutableStateFlow<List<Article>>(emptyList())
private val _filter = MutableStateFlow(NewsFilter())
private val _favorites = MutableStateFlow<Set<String>>(emptySet())
private val _loading = MutableStateFlow(LoadingState.Idle)
private val _selectedIds = MutableStateFlow<Set<String>>(emptySet())

// 聚合 + stateIn 收口
val uiState: StateFlow<NewsUiState> = combine(
    _articles, _filter, _favorites, _loading, _selectedIds
) { arts, flt, favs, ld, sel ->
    NewsUiState(arts, flt, favs, ld, sel)
}.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), NewsUiState())
```

**为什么不选单一 data class？**

| 维度 | 单 data class | 多流 + combine |
|------|---------------|----------------|
| 重组粒度 | 任何字段变 → 整个 UI 重组 | 只订阅该流的 Composable 重组 |
| 可测试性 | 需构造完整 state | 每个流可独立单测 |
| 变更隔离 | 改一处要动大 data class | 改一个维度只动一个 StateFlow |
| 分页更新 | `_articles` 变了所有订阅者都重组 | 只 list 相关 Composable 重组 |

**8–10 维度的取舍：**

- combine 参数到 5+ 个就开始**可读性下降**；
- 应对策略 1：**按变更频率分组 combine**（高频组：列表/分页/选中；低频组：筛选/收藏），最后只 combine 两组；
- 应对策略 2：**按功能模块拆分 StateHolder**——把"列表 ViewModel"和"收藏 ViewModel"做内嵌 VM，外层只聚合；
- 原则：**让 recompose 触发范围最小化，同时保持状态一致性**。维度多到 combine 签名碍眼，就是该拆模块的时候。

---

**Q2: ViewModel 解决了配置变更存活，但**进程被杀**（系统回收）呢？`SavedStateHandle` 是怎么配合 ViewModel 救场的？底层存什么容器？ViewModel 里哪些数据该丢给它、哪些不该，判断标准是什么？**

A: **进程被杀重启流程：**

```
用户切走 → 系统内存紧张 → 进程被杀
  ↓
Activity.onSaveInstanceState() 被调（如果进程还有时间）
  ↓
Bundle 写入磁盘（/data/data/<pkg>/files/ 下）
  ↓
用户切回 → Activity 重建 → ViewModelStore 用 Bundle 重建 VM
  ↓
SavedStateHandle 自动恢复
```

**底层容器：** `SavedStateHandle` → `PersistentStateBundle extends BaseBundle` → 经 `ActivityThread$ActivityClientRecord.savedStateStack` → 由 `Activity.onSaveInstanceState` 的 `mContainer.writeToParcel()` 落盘。本质跟 `onSaveInstanceState` 用同一套 Bundle 机制，VM 直接对接，不用在 Activity/Fragment 里手写 `bundle.putString`。

**使用方式：**

```kotlin
class NewsListViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {
    // 推荐：用 StateFlow 形式承载，自动响应恢复
    val keyword: StateFlow<String> = savedStateHandle.getStateFlow("keyword", "")

    fun setKeyword(k: String) { savedStateHandle["keyword"] = k }
}
```

**判断标准：**

| 丢给 SavedStateHandle | 不丢（VM 内存即可） |
|-----------------------|---------------------|
| 用户未提交的输入（搜索框草稿、表单内容） | 网络/DB 已拿到的数据（articles 列表） |
| 本次会话的筛选条件（tab/keyword/sort） | 纯 UI 状态（多选模式开关）——可重建 |
| 滚动位置 / 分页游标（cursor/offset） | 大数据（整个列表、用户资料） |
| 一次性事件的消费状态 | 网络请求 progress——重新请求即可 |
| 影响下次会话的轻量上下文 | 任何可从 Repository 重新拉取的数据 |

**核心判断原则：**

1. **能丢的** = "用户不愿意重新输入/选择的数据"——丢了用户会烦；
2. **不能丢的** = "可重建的数据"——丢了再拉一份就行，丢错了只会撑爆 Bundle（约 1MB 上限）；
3. **最大误区：把网络请求结果塞 SavedStateHandle**。SavedStateHandle 不是缓存，是**用户上下文恢复**。网络数据应该走 Repository + 缓存策略（Room/内存）重建。
- Guide to app architecture:https://developer.android.com/topic/architecture
- ViewModel:https://developer.android.com/topic/libraries/architecture/viewmodel
- StateFlow / SharedFlow:https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/
- Hilt:https://developer.android.com/training/dependency-injection/hilt-android