---
title: Kotlin 协程
domain: 01-语言
level: 熟悉
target: 精通
importance: 高
last_assessed: 2026-07-29
last_reviewed: 2026-07-29
next_review: 2026-11-16
tags: [并发, 异步]
related: [RxJava, Handler]
---

# Kotlin 协程

## 概述
Kotlin 的轻量级异步/并发方案。**协程不是线程**,而是「可挂起的计算」:执行到 `suspend` 挂起点时把当前状态打包、交还线程(不阻塞),条件满足后 `resume` 接着跑——于是能用同步写法写异步代码。一个线程可复用跑大量协程;再通过**结构化并发**(作用域 + 父子关系)统一管理生命周期、取消与异常。

## 考核记录
- **2026-07-29** 判定：(待考核) → 熟悉 ✅ ｜ 考官：AI
  - 表现：概念扎实——协程≠线程/轻量(KB级+用户态切换)/suspend 释放线程不阻塞、结构化并发(父子取消、父等子、解决泄漏)。熟悉档稳过:async 并发合并(`async{}` 先发起再 `await` 合并)、`withContext` 切线程(IO 读→Main 更新)都写得对。
  - 不足：掌握档未达——协作式取消根因讲对(无挂起点)但 API 写错(`isAlived()` 应为 `isActive`/`ensureActive()`/`yield()`);超时+兜底实现(`withTimeoutOrNull` + try/catch)不会写。
  - 依据：了解→熟悉两档稳稳答到;掌握档要求独立实现,Q6 写不出、Q5 API 有误,未达,故判熟悉。差 1 档到 target(掌握)。

## 核心原理 / 关键点

### 1. suspend 与 CPS（续接传递）

`suspend` 函数能「挂起」而不阻塞线程，靠的是编译器把函数改写成 **CPS（Continuation Passing Style，续接传递风格）**：编译器自动给每个 suspend 函数加一个隐藏参数 `continuation: Continuation<T>`，并把函数体变成一个**状态机**——用 `label` 字段记录「下一次 resume 该从哪段接着跑」，用成员字段保存局部变量。

执行到挂起点时，suspend 函数返回特殊哨兵值 `COROUTINE_SUSPENDED`，把当前状态打包进状态机对象后**交还线程**；条件满足后调用 `resumeWith`，状态机按 `label` 跳回对应分支继续。所以 suspend 函数的真实返回类型是 `Any?`——要么是真正的结果 `T`，要么是「我挂起了」的哨兵。`Continuation<T>` 接口本身只有两样东西：`context: CoroutineContext` 和 `resumeWith(result: Result<T>)`。

```kotlin
// 你写的
suspend fun fetchUser(id: Int): User {
    val token = getToken()              // 挂起点 1
    val user = api.getUser(token, id)   // 挂起点 2
    return user
}

// 编译器生成（概念示意，非精确字节码）
fun fetchUser(id: Int, cont: Continuation<User>): Any? {
    val sm = (cont as? FetchUserSM) ?: FetchUserSM(cont)  // 复用/创建状态机
    when (sm.label) {
        0 -> { sm.id = id; sm.label = 1; return sm.getToken(sm) }   // 返回 COROUTINE_SUSPENDED
        1 -> { sm.token = sm.result as Token; sm.label = 2; return sm.apiGetUser(sm.token, sm.id, sm) }
        2 -> { return sm.result as User }   // 真正返回结果
    }
}
```

### 2. 结构化并发

**CoroutineScope** 定义一段生命周期边界，`launch` / `async` 都是在某个 scope 上启动的。每个协程持有一个 **Job**，子协程的 Job 挂在父 Job 下，形成一棵 **Job 树**。于是：

- 父协程会等所有子协程结束才结束；
- 取消父 Job → 整棵子树都被取消；
- 默认情况下，任一子协程**抛出未捕获异常**会向上传播，取消父和所有兄弟（失败是「集体」的）。

要切断这种连带，用 **SupervisorJob**（建 scope 时传）或 **supervisorScope { }**：在 supervisor 下，一个子的失败不会连累兄弟。Android 里不要自建 scope，直接用 **`lifecycleScope`**（绑定 LifecycleOwner）和 **`viewModelScope`**（绑定 ViewModel），组件销毁时自动取消；**`GlobalScope`** 没有父、跟进程同寿，几乎总是错的（生命周期泄漏）。

```kotlin
// 父协程等所有子:coroutineScope 返回前会等内部所有 launch 完成
suspend fun loadAll() = coroutineScope {
    launch { fetchA() }
    launch { fetchB() }
}

// Android:绑定 ViewModel 生命周期
class MyVm : ViewModel() {
    fun load() = viewModelScope.launch {   // ViewModel.clear() 时自动取消
        val a = fetchA()
    }
}
```

### 3. 调度器与线程

**Dispatcher** 决定协程在哪个线程（池）上 resume。`withContext(Dispatcher) { }` 临时切换调度器、结束后恢复。

| 调度器 | 用途 | 线程模型 |
|--------|------|---------|
| `Dispatchers.Default` | CPU 密集（排序、解析、计算） | 线程数 ≈ CPU 核数 |
| `Dispatchers.IO` | 阻塞 I/O（文件、数据库、阻塞网络） | 复用 Default 底层池，但可弹性扩到更多线程（默认上限 ≈ max(64, 核数)，可配 `kotlinx.coroutines.io.parallelism`） |
| `Dispatchers.Main` | UI 线程（Android：主线程 Looper） | 单线程 |
| `Dispatchers.Unconfined` | 不切换，在 resume 它的线程里继续 | 高级用法，慎用 |

**关键认知**：「不阻塞线程」只是 suspend 释放线程；如果你在协程里调真正阻塞的 API（`Thread.sleep`、阻塞 socket、同步 OkHttp），它照样会卡住跑它的那个线程——协程不会把阻塞代码变魔法成非阻塞。所以阻塞调用要么放进 `Dispatchers.IO`，要么改用真正 suspend 的库（Retrofit/Room 的 suspend 函数）。

```kotlin
suspend fun show() = withContext(Dispatchers.Main) {
    val data = withContext(Dispatchers.IO) { blockingRead() }  // 阻塞读切到 IO 池
    textView.text = data                                       // 回 Main 更新 UI
}
```

### 4. 拦截器（Interceptor）

**一句话**：拦截器是协程每次「**恢复**（从挂起接着往下跑）」时都要经过的一道**钩子**——它能在「恢复」这一瞬间插一手：记日志、掐表计时、或者**把你送去另一个线程再恢复**。

> **类比「收发室」**：协程挂起后要恢复，就像一个包裹要送到你手上；恢复前必须先过「收发室（拦截器）」。收发员可以登记一下（日志）、称个重（计时），也可以**直接把包裹转去另一栋楼（切线程）**再派送。`Dispatchers.IO` 就是那个「专门把包裹转去 IO 线程」的收发员——**所以 Dispatcher 本质就是个拦截器**。

**它拦截的到底是什么**：协程挂起靠「续接（Continuation）」——一段「接着往下跑」的凭证，它有个 `resumeWith()`，被调用 = 协程恢复。拦截器做的事就是把续接**包一层**，在真正的 `resumeWith` 前后插入自己的逻辑：

```kotlin
// 最朴素的拦截器：每次「恢复」时打印一行
class LogInterceptor : AbstractCoroutineContextElement(ContinuationInterceptor),
                          ContinuationInterceptor {
    // 拿原始续接 cont，返回一个「包了一层」的新续接
    override fun <T> interceptContinuation(cont: Continuation<T>) =
        object : Continuation<T> {
            override val context = cont.context
            override fun resumeWith(result: Result<T>) {
                println("即将在 ${Thread.currentThread().name} 恢复")
                cont.resumeWith(result)   // 再交给下层（往往是 Dispatcher）真正恢复
            }
        }
}
```

**为什么 Dispatcher 就是拦截器（关键认知）**：你写 `withContext(Dispatchers.IO) { ... }` 能切线程，底层正是 `Dispatchers.IO` 这个拦截器在续接「要恢复」时，**不让它就地恢复，而是 submit 到 IO 线程池、等池里有线程了再恢复**。换句话说「调度（切线程）」只是「拦截」的一种用法——拦截器是更通用的机制，Dispatcher 是它最常用的实现（这也是为什么 `CoroutineDispatcher` 实现的接口正是 `ContinuationInterceptor`）。

**一个常被忽略的坑**：`CoroutineContext` 是**按 Key 存的集合，每个 Key 只能有一个元素**（`a + b` 若同 Key，后者覆盖前者），而 `ContinuationInterceptor` 就是一个 Key。所以**一个 context 里至多一个拦截器**：

```kotlin
// ⚠️ Dispatchers.Default 和 LoggingInterceptor 都是 ContinuationInterceptor
//    结果只有一个生效(后者覆盖前者)，不是「两个叠加」
scope.launch(Dispatchers.Default + LoggingInterceptor()) { /* ... */ }
```

真要「先记日志、再切线程」两个都生效，不能并列塞进 context，得在**一个**拦截器的 `interceptContinuation` 里手动把日志包在调度外层、再 delegate 给 Dispatcher。

**日常记住两点就够**：① Dispatcher 底层就是个拦截器（在恢复时负责切线程）；② 一个 context 只能有一个拦截器，想叠加得在内部 delegate，不是往 context 里塞多个。

### 5. 启动与等待：launch / async

- **`launch`**：返回 `Job`，fire-and-forget，并发跑；异常按结构化并发规则传播。
- **`async`**：返回 `Deferred<T>`，`await()` 是挂起点，返回结果（或重新抛出内部异常）。
- **`awaitAll`**：等多个 Deferred 全部完成。

并发请求合并的惯用法：`async` 发起多个、再统一 `await`。注意在 `coroutineScope` 里任一 `async` 失败会取消其它兄弟——要互不影响就用 `supervisorScope`。

```kotlin
suspend fun loadProfile(id: Int): Profile = coroutineScope {
    val user  = async { api.getUser(id) }   // 并发发起
    val posts = async { api.getPosts(id) }
    Profile(user.await(), posts.await())    // 等两个结果
}
```

### 6. 协作式取消

协程取消是**协作式**的：`job.cancel()` 把 Job 置为 Cancelling，协程在**下一个挂起点**才会收到 `CancellationException` 而退出。如果协程根本不挂起（纯 CPU 循环），它就感知不到取消——必须主动检查 `isActive`、或调用 `ensureActive()` / `yield()`。

清理资源用 `finally`（`CancellationException` 能在里面被捕获），或对 `Closeable` 用 `use { }`；如果清理本身也要挂起，得用 `withContext(NonCancellable)` 包起来，否则清理会被取消打断。`CancellationException` 是取消「信号」本身，不算真正错误。

```kotlin
val job = launch {
    while (isActive) {          // CPU 密集循环:主动检查可取消性
        processChunk()
        yield()                 // 让出 + 顺便检查取消
    }
}
job.cancelAndJoin()

suspend fun work() {
    val conn = openConn()
    try { doStuff(conn) }
    finally { withContext(NonCancellable) { conn.close() } }  // 挂起的清理不被取消打断
}
```

### 7. 异常处理

- **取消异常** `CancellationException` 是取消机制本身，不当作「失败」。
- 默认：子协程未捕获异常 → 取消父 + 兄弟（集体失败）。
- **`CoroutineExceptionHandler`**：未捕获异常的最后兜底，**只对根协程（直接在 scope 上 launch 的、没有父的协程）生效**；子协程的异常会向上冒给父，装在子身上会被忽略。
- **`SupervisorJob` / `supervisorScope`**：让子协程相互独立，一个失败不连累兄弟。适合「多个互不相关、各自失败各自处理」的场景。
- `try/catch` 能包住 suspend 调用（它就是普通函数调用），但包不住 `launch { }` 的 lambda——那个跑在另一个协程里，异常不会同步冒给调用方。
- **超时**：`withTimeout(ms) { }` 到点抛 `TimeoutCancellationException`（属 `CancellationException`）；只想「超时不抛、返回默认值」用 **`withTimeoutOrNull(ms) { }`**——超时返回 `null`、正常返回结果，配合 `try/catch` 即可「超时或失败都兜底」。

```kotlin
supervisorScope {
    launch { sectionA() }   // 即便这里抛异常,sectionB 照常
    launch { sectionB() }
}

val handler = CoroutineExceptionHandler { ctx, e -> log("root failed: $e") }
scope.launch(handler) { risky() }   // 根协程兜底
```

「超时 + 失败都兜底」示例（`withTimeoutOrNull` + `try/catch`）：

```kotlin
// 5 秒超时;超时或请求失败都不抛,返回默认值
suspend fun fetchOrDefault(): Result = try {
    withTimeoutOrNull(5000) { api.fetch() } ?: DEFAULT   // 超时 → null → DEFAULT
} catch (e: Exception) {                                  // api.fetch() 抛异常 → DEFAULT
    DEFAULT
}
```

### 8. Flow（冷流）

**`Flow<T>`** 是冷流：生产代码只在被 `collect` 时才跑，且**每个 collector 各跑一份**。中间操作符（`map`/`filter`/`transform`/`flatMapConcat`/`flatMapMerge`/`flatMapLatest`）是冷的、惰性的；`collect` 是终端挂起点。

**背压**（生产比消费快）：`buffer`（生产/消费并发跑、中间加缓冲）、`conflate`（丢中间只留最新）、`collectLatest`（新值到来时取消上一轮慢 collect）。异常用 `catch`（仅上游）、`onEmpty`、`retry`；Flow 的取消跟随 collector 所在协程。

**热流**：`StateFlow`（持有一个状态、自动 conflate、适合 UI 状态）、`SharedFlow`（向多个 collector 广播，可配 replay/buffer）。热流一份生产、多方订阅。

```kotlin
fun ticks(): Flow<Int> = flow {
    for (i in 0..1000) { delay(100); emit(i) }
}

ticks().map { it * 2 }
    .buffer()                 // collect 慢时,生产不被阻塞
    .collect { processSlow(it) }

// UI 状态用热流
class MyVm : ViewModel() {
    private val _state = MutableStateFlow(UiState.Loading)
    val state: StateFlow<UiState> = _state.asStateFlow()
}
```

## 实践经验 / 踩坑

1. **协程 ≠ 线程，阻塞 API 照样卡线程** —— 协程里调 `Thread.sleep` / 阻塞 socket / 同步 OkHttp 会卡住跑它的线程；若跑在 Default 池里，会拖垮整池。改用 `Dispatchers.IO` + 真正 suspend 的库（Retrofit/Room 的 suspend 函数），或把不得不用的阻塞调用包进 `Dispatchers.IO`。
2. **主线程阻塞** —— 网络/数据库别在 Main 跑；`Dispatchers.Main` 只做轻量 UI 操作。
3. **取消不响应** —— 纯 CPU 或无挂起点的循环 `cancel()` 不生效，要 `isActive` / `ensureActive()` / `yield()` 主动让出。
4. **GlobalScope 泄漏** —— GlobalScope 启动的协程脱离组件生命周期，Activity/Fragment/ViewModel 销毁了它还在跑。用 `lifecycleScope` / `viewModelScope`。
5. **async 异常连累兄弟** —— 普通 scope 里 `async` 失败会取消 scope 内其它兄弟；要互不影响就用 `supervisorScope`。
6. **withContext 频繁切换** —— 每次切换都有调度开销，循环里别无意义地反复切线程。
7. **Flow collect 在主线程做重活** —— `collect` 的 lambda 跑在调用它的调度器上；重活先用 `flowOn(Dispatchers.IO)` 在上游处理，回 Main 再 collect 更新 UI。

## 待深入 / 下一步
- [ ] 读 suspend 的 CPS 原理 → 源码 `BaseContinuationImpl` / `ContinuationImpl`（本文已覆盖基础）
- [ ] 做一个 Flow 实战
- [ ] 读 `JobSupport`：Job 树与取消/异常传播的具体实现
- [ ] 读 `DispatchedContinuation`：调度与拦截的衔接
- [ ] Channel / `produce` 的冷热与背压

## 参考资料
- 官方指南：https://kotlinlang.org/docs/coroutines-guide.html
- kotlinx.coroutines：https://github.com/Kotlin/kotlinx.coroutines
- Flow：https://kotlinlang.org/docs/flow.html
- Android 协程（lifecycleScope / viewModelScope）：https://developer.android.com/kotlin/coroutines
- 关键源码类：`ContinuationImpl`、`BaseContinuationImpl`、`JobSupport`、`DispatchedContinuation`、`CoroutineContext`