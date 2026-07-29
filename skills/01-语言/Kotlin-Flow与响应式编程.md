---
title: Kotlin Flow 与响应式编程
domain: 01-语言
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-27
next_review: 2026-08-26
tags: [Flow, StateFlow, SharedFlow, 响应式, RxJava]
related: [Kotlin 协程, Jetpack Compose, MVVM]
---

# Kotlin Flow 与响应式编程

## 概述
**响应式编程**的核心是「数据流 + 变化传播」:把一切看成随时间推进的值序列,声明「A 依赖 B、C」后,B、C 变化时 A 自动重算。**`Flow<T>`** 是 Kotlin 协程提供的响应式流 API——可看作**协程版的 RxJava Observable**:它基于 `suspend`、天然背压、契合结构化并发,替代了 RxJava 一大堆线程调度操作符。核心要分清**冷流**(普通 `Flow`,无人订阅不生产、每个 collector 各跑一遍)和**热流**(`StateFlow`/`SharedFlow`,独立于订阅者、多方共享)。在 MVVM+Compose 中,`StateFlow` 承载 UI 状态(取代 `LiveData`)、`SharedFlow` 承载一次性事件,通过 `collectAsStateWithLifecycle` 驱动 UI。相比 `LiveData`,Flow 线程安全更好、操作符丰富;相比 RxJava,Flow 学习曲线低、与协程一体化。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 响应式与 Flow 基础（冷流、collect 才发射、suspend）

响应式 = **数据流 + 变化传播**:值随时间产生,下游声明式地响应。**`Flow<T>`** 是 Kotlin 协程的冷流 API,由三件套构成:

- **`flow { }` builder**:生产端,在 lambda 里用 `emit(value)` 发射(`emit` 是 suspend)。
- **`collect { }`**:消费端,终端操作符,**suspend**,必须在协程作用域里调用。
- **中间操作符**(`map`/`filter`/...):冷的、惰性的,只是装饰上游 Flow,不触发执行。

`collect` 是挂起点 → 必须有协程作用域;Flow 的取消跟随 collector 所在协程(`viewModelScope` 取消则 collect 终止)。它是**协程版的 `Sequence`**——`Sequence` 是同步冷流,`Flow` 是异步冷流(中间可挂起);也是**协程版 RxJava Observable**,但线程切换用 `flowOn` 而非 `subscribeOn/observeOn`,背压靠协程挂起自然处理。

```kotlin
fun countdown(n: Int): Flow<Int> = flow {
    for (i in n downTo 0) { delay(500); emit(i) }   // 不被 collect 就不跑
}

viewModelScope.launch {            // collect 必须在协程里
    countdown(3).collect { log(it) }
}
```

### 2. 冷流 vs 热流（核心区分）

**面试高频考点**,区分是理解一切的基础:

| | **冷流**(普通 `flow{}`/`channelFlow`) | **热流**(`StateFlow`/`SharedFlow`/`Channel`) |
|---|---|---|
| 生产时机 | 被 `collect` 才生产 | 独立于订阅者,自己跑 |
| 多 collector | **每个各自从头跑一遍**(一对一,各自独立) | **共享同一数据源**(一对多,广播) |
| 订阅者数 | 0 个时根本不生产 | 可有 0~N 个订阅者 |
| 典型 | 网络请求、DB 查询、`flow{}` | UI 状态(`StateFlow`)、事件总线(`SharedFlow`) |

**一句话**:冷流是「按需的视频点播」(每个观众从头看),热流是「直播」(所有观众看同一路信号)。冷流两个 collector → **两次网络请求**;热流两个 collector → **一次生产、两份推送**。

### 3. StateFlow（状态持有、conflate、去重、UI 状态首选、vs LiveData）

**`MutableStateFlow<T>`** 是热流的状态持有者:

- 持有**一个**最新值,**必须有初始值**(`MutableStateFlow(initial)`)。
- **conflate**:新值到来时若旧值还没被消费,只保留最新——天然适合状态,因为 UI 只关心最新状态。
- **`equals` 去重**:连续 `value = x` 同值不发射(`distinctUntilChanged` 内建)。
- 始终活跃,新订阅者立即收到当前值。

是 **UI 状态的首选载体**,替代 `LiveData`。对比 `LiveData`:

- **生命周期感知**:LiveData 自带;StateFlow 需配合 `repeatOnLifecycle` / `collectAsStateWithLifecycle`,否则会在 `STARTED` 之外仍收集(浪费资源)。
- **初始值**:StateFlow 必须有(状态机更明确),LiveData 不要求。
- **线程安全**:StateFlow 的 `value` 赋值线程安全且严格主线程一致;LiveData 的 `postValue` 有合并竞态。
- **操作符**:StateFlow/Flow 有完整操作符生态,LiveData 贫乏。

```kotlin
class UserVm : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()   // 对外只读

    fun load() = viewModelScope.launch {
        _uiState.value = UiState.Loading
        _uiState.value = UiState.Success(repo.fetch())         // 赋值即发射
    }
}
```

### 4. SharedFlow（事件广播、replay/buffer、一次性事件）

**`MutableSharedFlow<T>`** 是热流的事件广播器:

- **可无初始值**;`replay`(新订阅者重放最近 N 条)、`extraBufferCapacity`(缓冲)、`onBufferOverflow`(`DROP_OLDEST`/`DROP_LATEST`/`SUSPEND`)。
- 不 conflate(默认 buffer 满了 SUSPEND 发射方),所以**不会丢中间事件**。
- **一次性事件首选**:导航、Toast、Snackbar、弹窗——这些事件不能被 conflate 成最新一条(否则漏播),也不能旋转后重复。

```kotlin
class CheckVm : ViewModel() {
    private val _events = MutableSharedFlow<UiEvent>()
    val events: SharedFlow<UiEvent> = _events.asSharedFlow()

    fun save() = viewModelScope.launch {
        repo.save()
        _events.emit(UiEvent.ShowToast("已保存"))   // 事件,不丢
    }
}

// Compose 端:Lifecycle-aware 收事件
val events by vm.events.collectAsStateWithLifecycle(initialValue = null)
```

**StateFlow vs SharedFlow 选型**:状态(可重复观察、关心最新值)用 StateFlow;事件(一次性、不丢)用 SharedFlow。把一次性事件塞 StateFlow → 旋转后要么重复要么丢失(见第 7 节)。

### 5. 关键操作符与背压

**转换/过滤**:`map` / `filter` / `take(n)` / `scan`(累积,带历史)/ `distinctUntilChanged` / `debounce`(防抖,搜索框)/ `sample`(周期采样)。

**flatMap 系列区别(面试必考)**——把上游每个值映射成新 Flow 再展平:

- **`flatMapConcat`**:顺序串行,上一个内流跑完才下一个。
- **`flatMapMerge`**:并发发起所有内流,结果乱序汇合(`concurrency` 限并发数)。
- **`flatMapLatest`**:切到新值时**取消上一轮未完成的内流**——搜索联想、`query` 变即丢弃旧请求的标配。

**组合**:`combine(f1, f2) { a, b -> }`(任一变即合,最新值配对)、`zip`(按序严格配对,等齐)。

**异常/重试**:`catch { }`(只捕上游,且只能 `emit` 补偿,不能改下游语义)、`onEmpty { }`(上游空时补发)、`retry(times) { e -> }` / `retryWhen { e, attempt -> }`。

**什么是背压(backpressure)**:当**生产端发射速度 > 消费端处理速度**时,让消费端反过来约束生产端节奏的机制——本质是「流量控制 / 反馈控制」。响应式流是异步、解耦的,生产者与消费者各自独立运行,速率难免失配;若生产快、消费慢又无任何约束,数据就会在中间堆积——要么撑爆缓冲(OOM),要么被迫丢弃,要么延迟越积越大。背压就是让消费端能告诉生产端「我还没准备好,慢一点 / 停一下」。

> 类比「漏斗倒水」:漏斗(消费者)排水慢、你(生产者)倒水快。没有背压 = 照倒不误 → 水溢出(数据丢失 / OOM);有背压 = 看漏斗快满了就停手等它排。这就是「消费端反控生产端」。

**Flow 的天然背压(关键)**:`emit` 与 `collect` 都是 `suspend`。冷流是**拉模式**——`collect` 拿一个值、处理完(挂起期间)上游 `emit` 才返回、才发下一个,**生产者根本跑不到消费者前面**:消费端没处理完,`emit` 就挂起等;消费者慢,生产者自动跟着慢。所以普通 `Flow` 默认**不丢、不堆**,背压由协程挂起自然完成,不需要像 Reactive Streams / RxJava 那样用 `request(n)` 显式申请需求量。

**那为什么还要手动处理?** 天然背压的代价是「生产被 collect 卡死」——collect 慢,生产也跟着慢、吞吐低。当你想**让生产先跑起来**(提高吞吐、解耦上下游)时,就要主动打破这种同步:

- `buffer()` / `buffer(cap)`:生产与 collect 切到不同协程、中间加缓冲,生产不再被 collect 阻塞。
- `conflate()`:合并,只留最新。
- `collectLatest { }`:新值到来时取消上一轮还没跑完的 `collect` lambda。

⚠️ 区分两类策略:`buffer()` 是**无损**(加容量换吞吐,满了仍 SUSPEND 发射方);`conflate()` / `collectLatest()` 是**有损**(主动丢旧值换实时性)。选型看「能不能丢」——状态/最新值能丢(`conflate`),逐条事件不能丢(`buffer` 或 `SharedFlow` 的 `extraBufferCapacity`)。

**终端**:`collect` / `toList()` / `first()` / `single()` / `fold()` / `launchIn(scope)`。

```kotlin
searchQuery
    .debounce(300)                                    // 防抖
    .distinctUntilChanged()
    .flatMapLatest { q -> api.search(q) }             // 新 query 取消旧请求
    .catch { emit(SearchResult.Error(it)) }           // 上游异常兜底
    .collect { render(it) }
```

### 6. 在 Compose 与 MVVM 中使用（collectAsStateWithLifecycle、stateIn、sharingStarted）

**VM 对外暴露只读 `StateFlow`**(内部持有 `MutableStateFlow`,对外 `asStateFlow()`),事件用 `SharedFlow`。Compose 端:

- **`collectAsStateWithLifecycle()`**(需 `lifecycle-runtime-compose`):生命周期感知——只在至少 `STARTED` 时收集,配置变更(旋转)时自动停止、恢复,避免浪费。比旧的 `collectAsState` 更省电。事件流的「只收集一次」用 `LaunchedEffect` + `lifecycle.repeatOnLifecycle(STARTED) { flow.collect {} }`。

**`stateIn`**:把**冷流转成 StateFlow**(共享一份生产,避免每个 collector 重跑):

```kotlin
val users: StateFlow<UiState<List<User>>> = repo.getUsersStream()
    .map { UiState.Success(it) }
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),   // 有订阅者才跑上游
        initialValue = UiState.Loading
    )
```

**`SharingStarted` 三种**:

- `WhileSubscribed(stopTimeoutMillis)`:**有订阅者才启动上游**,最后一个退订后等 `stopTimeout`(常用 5000ms)再停——给配置变更留缓冲,避免旋转瞬间停止又重启上游(省电且防抖)。**最常用**。
- `Eagerly`:VM 创建即启动(不管有没有订阅者),占用资源。
- `Lazily`:首个订阅者启动,之后永不停止。

### 7. 常见误用（面试反例 / 高频踩坑）

- **Composable 里直接 `flow.collect { }`**:每次重组都开新协程、还绕过生命周期。应 `collectAsStateWithLifecycle()` 把 Flow 变 State、由 Compose 订阅 State。
- **冷流被多个 collector 各自 collect → 重复网络请求**:冷流一对一,两个 collector 两份请求。用 `stateIn` / `shareIn` 转热流共享一份。
- **一次性事件塞 `StateFlow`**:状态会 conflate/去重,旋转后要么重复消费、要么新订阅者拿不到(已被覆盖)。事件必须用 `SharedFlow`(或 `Channel`)。
- **`stateIn` 漏掉 `WhileSubscribed`**:用 `Eagerly` 或不设 → ViewModel 创建就跑上游、永不停,流量泄漏;正确做法是 `WhileSubscribed(5000)`,无订阅者时自动停上游。
- **`catch` 位置错**:`catch` 只捕**上游**(在它之前的操作符),捕不到下游 `collect` lambda 内异常;要全局兜底配合 `CoroutineExceptionHandler` 或在 `collect` 内 try/catch。
- **热流不配生命周期**:StateFlow 在 Compose 里不用 `collectAsStateWithLifecycle` 而直接 collect,会在后台不可见时仍收集。

## 实践经验 / 踩坑

1. **冷流多 collect = 重复请求** —— VM 暴露的查询结果必须 `stateIn`/`shareIn` 转热流,否则每来一个 collector(DB、网络)重跑一次。
2. **事件 vs 状态选错流** —— 状态(可恢复、关心最新)用 `StateFlow`;事件(一次性、Toast/导航)用 `SharedFlow`。最常见的 bug 就是事件放 StateFlow 导致旋转重复弹 Toast。
3. **Compose 端忘了 `collectAsStateWithLifecycle`** —— 老 `collectAsState` 不绑生命周期,App 切后台还在收集。引入 `lifecycle-runtime-compose` 用 `collectAsStateWithLifecycle()`。
4. **`flatMapLatest` 用错场景** —— 它会取消上一轮;若内流有副作用(写库),被取消会留下脏状态。无副作用的纯查询才适合。
5. **`flowOn` 方向** —— `flowOn(Dispatchers.IO)` 影响**上游**的执行调度器;`flowOn` 之后的操作符才是默认 dispatcher。多个 `flowOn` 各自影响其上游。
6. **SharedFlow buffer 满默认 SUSPEND** —— 发射方挂起等消费方,若消费方卡住,生产也卡;要保事件不丢又不想卡,设 `extraBufferCapacity` + `DROP_OLDEST`(但会丢事件,需权衡)。
7. **测试 StateFlow/SharedFlow** —— `Turbine` 库是 Flow 测试标配(`test { awaitItem() }`);`runTest` 控制虚拟时间测 `debounce`/`delay`。

## 待深入 / 下一步

- [ ] 读 `StateFlowImpl` / `SharedFlowImpl` 源码:订阅者链表与 conflate/buffer 实现
- [ ] `Channel` 与 `SharedFlow` 的关系(`Channel` 是单消费者原语,`SharedFlow` 基于多播)
- [ ] `callbackFlow` / `channelFlow`:把回调/第三方 listener 适配成 Flow,及 `awaitClose` 释放资源
- [ ] Turbine 实战:Flow 单元测试的虚拟时间与断言
- [ ] Compose 中 `produceState` / `snapshotFlow`:Compose State ↔ Flow 的桥接

## 参考资料

- 官方 Flow 文档:https://kotlinlang.org/docs/flow.html
- Android StateFlow/SharedFlow 指南:https://developer.android.com/kotlin/flow/stateflow-sharedflow
- Android Flow 与响应式:https://developer.android.com/kotlin/flow
- `collectAsStateWithLifecycle`:https://developer.android.com/jetpack/androidx/releases/lifecycle
- 关键源码类:`FlowCollector`、`FlowCoroutine`、`StateFlowImpl`、`SharedFlowImpl`、`SharingStarted`
