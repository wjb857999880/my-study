---
title: WorkManager 后台任务
domain: 02-框架与Jetpack
level: 精通
target: 精通
importance: 中
last_assessed: 2026-09-11
last_reviewed: 2026-09-11
next_review: 2027-03-10
tags: [WorkManager, 后台, 任务]
related: [Android 四大组件与生命周期]
---

# WorkManager 后台任务

## 概述
Jetpack 的**可靠后台任务**方案:适合「需要保证执行、但可延迟」的任务(上传日志、同步数据、定期清理)。系统会根据电量 / 网络 / 约束择机执行,即使 App 退出或重启也能补跑(持久化 + 重启恢复)。替代了 Service + AlarmManager 的碎片化方案,适配 Android 后台限制。区分:即时任务用协程 / 前台服务,可靠延迟任务用 WorkManager。支持约束(网络 / 充电)、链式任务、周期任务。

## 考核记录
- **2026-09-11** 判定：了解 → 精通 ✅ ｜ 考官：AI
  - 表现：四档全过。概念/边界清晰；照做题远超模板（retry 需显式返回、退避策略、KEEP/APPEND/REPLACE 区分）；排障题 4 bug 全中且指出输入/输出 Data 崩点位置差异、CoroutineWorker 占 Default 池不响应取消；设计题给出双请求双名字结构 + 周期任务首轮延迟/不可共用 unique name 两坑 + single-flight 兜底 + SUCCEEDED 瞬时态处理；原理题讲透 WorkDatabase 落库、Greedy/SystemJob 双调度器分工、DB 原子状态迁移做幂等闸门、三层重启恢复、doWork 线程环境与并发上限分离；多进程题命中 RUNNING 复位互踩、REPLACE 取消不跨进程等根因，给出收敛所有权 vs work-multiprocess vs 前台服务的取舍判断。
  - 依据：能讲透调度链路与恢复机制的源码级原理，并按架构权衡做多方案取舍（含「不值得引入」的反向判断），达到「精通」的原理深挖 + 架构设计标准。

## 核心原理 / 关键点

### 1. 定位:可靠、可延迟的后台任务
WorkManager 是 Jetpack 的**持久化后台任务**调度库,面向「需要保证最终执行、但可延迟」的任务(上传日志、同步数据、定期清理、定时上报)。它按 API level 自动选择系统最合适的底层调度(JobScheduler / AlarmManager + BroadcastReceiver),屏蔽碎片化。

### 2. 适用边界(与协程 / 前台服务 / AlarmManager 对比)
- **即时、可中断、用户感知**:协程 / 前台服务。
- **可靠、可延迟、即使 App 死 / 重启也要完成**:**WorkManager**。
- **精确时间触发**(闹钟 / 日历提醒):AlarmManager `setExactAndAllowWhileIdle`。
- **系统级定时**(旧):JobScheduler(已被 WorkManager 封装)。

### 3. Worker / CoroutineWorker 与约束
定义任务:继承 `Worker` 或 `CoroutineWorker`(协程友好),实现 `doWork()`,返回 `Result.success() / failure() / retry()`。提交时用 `OneTimeWorkRequest` / `PeriodicWorkRequest` + `Constraints`(需联网 / 充电 / 空闲 / 存储充足)。

### 4. 持久化与重启恢复
WorkManager 把任务存入其内部 Room 数据库;**App 被杀甚至设备重启后,未完成任务会在合适时机恢复执行**。这是它相对 Service 的核心价值——「保证最终执行」。

### 5. 周期任务、链式任务、唯一任务
- **周期任务**:`PeriodicWorkRequest`,最短间隔 15 分钟(系统限制),无精确周期。
- **链式任务**:`beginWith(A).then(B).then(C)`,A 完成才跑 B,可并行 / 串行编排。
- **唯一任务**:`enqueueUniqueWork`,保证同名任务唯一(避免重复上报)。

### 6. 传递数据(input / output Data)
任务间通过 `Data`(键值对,类 Bundle)传输入输出。**Data 有约 10KB 限制**,大数据传 URI 或写库,任务里再读。

### 7. 任务调度与系统策略
WorkManager 服从系统省电策略(Doze / App Standby / 后台限制),约束满足才执行。内部按 API level 用 JobScheduler(API 23+)或自实现的 AlarmManager + Receiver。

### 8. 测试与排障
提供 `WorkManagerTestInitHelper` 做本地测试(同步执行、跳过约束)。排障用 `adb shell dumpsys jobscheduler`、WorkManager 日志,以及 `getWorkInfoById` / `getWorkInfosByTagFlow` 观察任务状态。

### 9. 调度器内部:GreedyScheduler / SystemJobScheduler / SystemAlarmScheduler

任务入队后先落库(§4 的持久化),再由一组 **Scheduler** 决定「何时、由谁真正把 Worker 跑起来」。`Schedulers` 是编排者:在入队 / 约束变化 / 设备启动时,逐个询问已注册的 Scheduler 能否调度这块任务。三种具体实现,分工对应「立即跑」与「系统托管」两条路径:

- **GreedyScheduler**:**不依赖系统**、跑在 App 进程内。约束一满足就**立刻**通过 `Processor` 把 Worker 拉起来执行(「贪心」即在此——能跑就跑)。这就是「App 活着、约束已满足时任务马上执行」的原因。它带**并发上限**(`Configuration.setMaxSchedulerLimit`,默认远低于系统 JobScheduler 的 ~100 上限)。
- **SystemJobScheduler**:封装平台 **`JobScheduler`**(API 23+)。把任务映射成一个系统 Job,由系统择机唤醒——这是「App 被杀 / 重启后任务仍能恢复、并服从 Doze / App Standby」的底层保障。
- **SystemAlarmScheduler**:封装 **`AlarmManager` + `BroadcastReceiver`**,API < 23(M 以前)的回退方案,在老设备上提供同样的「延迟 + 重启恢复」能力。

**选型逻辑**:`Schedulers.create()` 按 API level 与配置产出 Scheduler 列表;每次调度时系统型 Scheduler(Job/Alarm)负责「保活与系统托管」,GreedyScheduler 负责「约束已满足就在进程内立即执行」。设备启动或 App 启动时,WorkManager 重新读库、把所有未完成任务再次注册到系统 Scheduler——这正是 §4「重启恢复」的实现。**加急任务**(`setExpedited`)在支持的版本走 JobScheduler 的 expedited job 通道。

> 一句话记忆:**GreedyScheduler = 进程内立即跑;SystemJob/Alarm = 系统托管、保活兜底;按 API level 选系统通道。**

### 10. 自定义 Configuration:Worker 工厂、初始化、日志级别

默认初始化由 `androidx.startup` 的 `WorkManagerInitializer` 自动完成,但要做 **DI 注入 Worker** 或调日志/调度参数时,必须接管初始化并自定义 `Configuration`:

① **关闭默认初始化**(AndroidManifest 里移除 startup provider 的 WorkManager 节点):

```xml
<provider
    android:name="androidx.startup.InitializationProvider"
    android:authorities="${applicationId}.androidx-startup"
    android:exported="false"
    tools:node="merge">
    <meta-data
        android:name="androidx.work.WorkManagerInitializer"
        android:value="androidx.startup"
        tools:node="remove" />
</provider>
```

② **实现 `Configuration.Provider`**(Application 里暴露配置,WorkManager 在首次 `getInstance()` 时**懒初始化**):

```kotlin
class App : Application(), Configuration.Provider {
    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setMinimumLoggingLevel(Log.INFO)   // 日志级别:VERBOSE 最详(排障用)
            .setWorkerFactory(MyWorkerFactory(deps))  // 自定义工厂,注入依赖
            .build()
}
```

> 旧式手动 `WorkManager.initialize(context, config)` 仍可用,但官方推荐 `Configuration.Provider`(避免重复 init、自动懒加载)。

③ **自定义 `WorkerFactory`**:WorkManager 默认**靠反射**按类名 new Worker,无法注入依赖。自定义工厂让 Worker 走 DI:

```kotlin
class MyWorkerFactory(private val repo: UserRepository) : WorkerFactory() {
    override fun createWorker(
        appContext: Context, workerClassName: String, params: WorkerParameters
    ): ListenableWorker? = when (workerClassName) {
        UploadWorker::class.java.name -> UploadWorker(appContext, params, repo)  // 注入 repo
        else -> null   // 交给下一个工厂(链式)
    }
}
```

- 多工厂用 `Configuration.Builder().setWorkerFactorys(f1, f2)` 或 `DelegatingWorkerFactory(listOf(...))` 串起来,逐个尝试直到返回非 null。
- 其他常用配置:自定义 `Executor`(`setExecutor`)、JobScheduler job id 区间(`setJobSchedulerJobIdRange`,多 App 防冲突)。

### 11. 多进程 App 与 WorkManager

**WorkManager 默认不是多进程安全的**:它的数据库在磁盘上跨进程共享,但运行时的 `WorkManager` 单例、内存调度状态是**每进程一份**。多个进程各自 enqueue / 各自加载同一任务,会读到同一份库 → 出现**重复调度、双重执行**的竞态。

- 典型场景:App 拆了独立进程(如 `:push`、`:remote`、推送 SDK 自带进程),从不同进程发任务。
- 方案:**`androidx.work:work-multiprocess`** 库。它指定一个**主进程**(primary)真正负责调度与执行,其他进程通过 IPC(bound service)把任务**转发**给主进程,从而保证「库只有一份运行时、由主进程统一调度」。
- 落地:依赖 work-multiprocess → 仍用 §10 的自定义 Configuration 初始化 → 确保只在主进程初始化 WorkManager。
- 实践:绝大多数**单进程 App 不需要它**;只有真有多进程且跨进程发任务时才引入,否则徒增复杂度。

### 12. 与 Foreground Service 的 `setForeground` 结合

长耗时 / 用户可感知的任务(大文件上传下载)会被系统后台限制打断。`CoroutineWorker` 提供 **`setForeground(ForegroundInfo)`**(suspend;`ListenableWorker` 用 `setForegroundAsync`)——把当前 Worker **提升为前台服务**:带一条常驻通知、获得前台优先级与后台执行的豁免,从而**保活运行直到完成**(前台服务生命周期见 [[Android 四大组件与生命周期]])。

```kotlin
class UploadWorker(appContext: Context, params: WorkerParameters) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        setForeground(foregroundInfo("上传中…"))   // 提升为前台服务
        // …长耗时上传…
        return Result.success()
    }

    private fun foregroundInfo(text: String): ForegroundInfo {
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setContentTitle("上传").setContentText(text)
            .setSmallIcon(R.drawable.ic_upload).setOngoing(true).build()
        // API 29+ 需指定前台服务类型(API 34+ 强制声明类型 + 对应权限)
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q)
            ForegroundInfo(NOTIF_ID, notification, FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        else ForegroundInfo(NOTIF_ID, notification)
    }
}
```

要点:
- **通知渠道必须先建**;API 33+ 需 `POST_NOTIFICATIONS` 运行时权限,否则通知不显示。
- **前台服务类型**(Android 14 / API 34 起强制):WorkManager 加急任务常用 `FOREGROUND_SERVICE_TYPE_DATA_SYNC`,需在 manifest 声明对应类型与权限。
- **加急任务**(`setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST)`):系统配额耗尽时,部分版本会以前台服务 + 通知形式运行,走的就是 `setForeground` 通道。
- Worker 要在系统判定其「后台运行超时」前尽早 `setForeground`,否则可能在长时间无通知时被回收。

## 实践经验 / 踩坑

1. **Data 大小限制**:约 10KB,大文件传 URI / 路径,Worker 内读;塞大对象会崩。
2. **周期任务最小 15 分钟**:且系统可能延迟,不能当精确闹钟(用 AlarmManager)。
3. **Worker 默认主线程**:`doWork` 耗时要用 `CoroutineWorker` 或自行切线程,否则 ANR。
4. **退出 App 后**:任务会继续 / 恢复,但服从系统策略;别假设「立刻跑」。
5. **用户可感知的长任务**:用 `setForeground`(把 WorkManager 任务转前台服务 + 通知),满足 Android 后台限制。

## 待深入 / 下一步
> 下方前四项已补入 §9-§12;此处为再深一层的下一步。

- [ ] **源码层**:`WorkManagerImpl` → `Schedulers.create()` → `Processor`/`WorkerWrapper` 实际调用 `doWork()` 的链路,确认 §9 的选型与并发上限实现。
- [ ] **Hilt + WorkManager**:`@HiltWorker` + `HiltWorkerFactory` 如何替代 §10 手写的 `WorkerFactory`(见 [[Hilt 依赖注入]])。
- [ ] **加急任务配额**:`setExpedited` 的系统配额来源(前台应用可用量),`OutOfQuotaPolicy` 两种策略的取舍与降级。
- [ ] **多进程实战**:`work-multiprocess` 的主进程选举 + IPC 转发机制(§11),找个多进程 Demo 跑通。
- [ ] **实战闭环**:在自己项目跑通「自定义 Configuration + DI Worker + setForeground 长任务」→ 考冲「熟悉」。

## 参考资料
- WorkManager 概览:https://developer.android.com/topic/libraries/architecture/workmanager
- WorkManager 测试:https://developer.android.com/topic/libraries/architecture/workmanager/testing
- 持久化任务调度:https://developer.android.com/guide/background/persistent

## 四档考核 Q&A（2026-09-11）

### 了解档
**Q：WorkManager 解决什么问题？一句话定位 + 该用 / 不该用的典型场景；即时任务和精确时间触发分别该用什么？为什么 WorkManager 干不了精确闹钟？**

A：定位一句话——**解决「可延迟、但必须保证最终执行」的后台任务**。该用：定时同步数据、上传日志这类「晚点跑没关系、但不能丢」的任务；不该用：立即执行的用户感知任务。

任务分流：即时 / 可中断 / 用户感知 → 协程 + 前台服务；精确时间触发（闹钟 / 日历提醒）→ AlarmManager `setExactAndAllowWhileIdle`；可靠可延迟 → WorkManager。

**干不了精确闹钟的原因**：WorkManager 依赖系统调度、服从省电策略（Doze / App Standby），约束不满足就不执行；它只保证**最终执行**、不保证**执行时机**，且周期任务最短 15 分钟、系统还可能延迟——「何时跑」完全交给系统。

---

### 熟悉档
**Q：① 写「上传日志」Worker（协程版）：联网约束、失败可重试，完整代码；② 「同步数据」要求同时最多一个在跑、后来的取消旧的，用哪个 API？**

A：

```kotlin
class UploadLogWorker(context: Context, params: WorkerParameters) :
    CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            val logFile = File(applicationContext.filesDir, "app.log")
            upload(logFile)
            logFile.delete()                          // 上传成功后清理
            Result.success()
        } catch (e: IOException) {
            if (runAttemptCount < 5) Result.retry() else Result.failure()  // 重试带上限
        }
    }
}

fun scheduleUploadLogs(context: Context) {
    val constraints = Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .build()
    val request = OneTimeWorkRequestBuilder<UploadLogWorker>()
        .setConstraints(constraints)
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL,
            WorkRequest.MIN_BACKOFF_MILLIS, TimeUnit.MILLISECONDS)
        .build()
    WorkManager.getInstance(context)
        .enqueueUniqueWork("upload_logs", ExistingWorkPolicy.KEEP, request)
}
```

②「后来的取消旧的」→ `enqueueUniqueWork` + **`ExistingWorkPolicy.REPLACE`**：

```kotlin
WorkManager.getInstance(context).enqueueUniqueWork(
    "sync_data", ExistingWorkPolicy.REPLACE, request)
```

关键点：
- **retry 必须显式返回 `Result.retry()`**——CoroutineWorker 里抛异常会被当作 failure（不重试）；用 `runAttemptCount` 设上限，否则按退避策略无限重试（上限间隔 5 小时）。
- **REPLACE 会真正取消正在运行的旧 Worker**：协程收到取消（`doWork` 抛 `CancellationException`）+ 回调 `onStopped()`，旧任务的网络请求要能响应取消，否则线程里的活继续跑完（只是结果被丢弃）。
- 三兄弟别混：**KEEP** 旧的没跑完就丢弃新请求；**APPEND** 新任务排到旧任务后面链式执行；**REPLACE** 取消旧的换新的。

---

### 掌握档

#### Q3.1（排障）：下面代码有 4 处问题（含 1 处当场崩），逐个指出并修

```kotlin
class SyncWorker(ctx: Context, params: WorkerParameters) :
    CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val json = inputData.getString("payload")!!   // 2MB 的 JSON 字符串
        val list = parseBigJson(json)
        val ok = uploadAll(list)          // 阻塞式上传，可能要跑 10 分钟
        return if (ok) {
            val resp = fetchServerResponse()           // 响应体约 500KB
            Result.success(workDataOf("resp" to resp))
        } else Result.failure()
    }
}
fun scheduleSync(app: Application) {
    val request = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
        .setInputData(workDataOf("payload" to hugeJson))
        .build()
    WorkManager.getInstance(app).enqueue(request)
}
```

A：按严重程度排：

1. **当场崩：2MB 塞进输入 Data**。Data 序列化后上限 10KB（`Data.MAX_DATA_BYTES = 10240`），`workDataOf("payload" to hugeJson)` 在 `build()` 时就抛 `IllegalStateException`，且在 `scheduleSync` 调用者的调用栈上（很可能主线程）——任务根本进不了队列。**修**：大负载写文件只传路径（或传 DB 记录 ID），Worker 里读文件；Data 只放 key / 路径 / 开关这类小字段。
2. **同一根源第二处：500KB 塞进输出 Data**。`Result.success(workDataOf("resp" to resp))` 同样超限；这处不崩进程（异常发生在 doWork 内部，任务被标 FAILED），症状是**上传明明成功、任务却永远失败**。**修**：响应写 cacheDir，输出只回路径。
3. **10 分钟阻塞调用：占错线程池 + 不可取消**。`CoroutineWorker.doWork` 默认跑在 `Dispatchers.Default`（CPU 池，就几根线程），网络 IO 一阻塞白占一根计算线程；更要命的是任务被 stop（REPLACE 换新、约束失效）时协程被取消，但阻塞调用感知不到，线程会把 10 分钟跑完只是结果被丢弃。**修**：至少 `withContext(Dispatchers.IO)`；理想是改成可取消的 suspend 调用（OkHttp `await()` / Retrofit suspend），或分片上传间 `ensureActive()`。
4. **裸 enqueue 没保唯一性**：每调一次就多排一个全新周期任务，多处调用 / 重启后重调度会多个 SyncWorker 并发。**修**：`enqueueUniqueWork("sync", ExistingWorkPolicy.REPLACE, request)`。

顺带：`getString("payload")!!` 当前流程能过但属埋雷，改 `?: return Result.failure()`；15 分钟恰是 PeriodicWorkRequest 最小间隔，合法（写 10 分钟会被钳到 15，不崩）。

#### Q3.2（设计）：数据同步要满足 ①启动同步一次 ②每 6 小时 ③同时只一个、后来的踢旧的 ④失败重试有上限 ⑤UI 观察状态

A：**2 个 WorkRequest、同一个 Worker 类、两个 unique name**：

| 需求 | 手段 |
|---|---|
| ① 启动同步一次 | `OneTimeWorkRequest`，unique name `"sync_now"`，REPLACE |
| ② 每 6 小时 | `PeriodicWorkRequest(6h)`，unique name `"sync_periodic"`，KEEP |
| ③ 同时只一个 | 同名 REPLACE + Worker 内 single-flight 兜底 |
| ④ 重试有上限 | `setBackoffCriteria(EXPONENTIAL)` + `runAttemptCount` 到顶转 failure() |
| ⑤ UI 观察 | `getWorkInfosForUniqueWorkFlow()` → combine → StateFlow |

```kotlin
fun scheduleSync(app: Application) {
    val wm = WorkManager.getInstance(app)
    val constraints = Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED).build()

    val nowRequest = OneTimeWorkRequestBuilder<SyncWorker>()
        .setConstraints(constraints)
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL,
            WorkRequest.MIN_BACKOFF_MILLIS, TimeUnit.MILLISECONDS).build()
    wm.enqueueUniqueWork("sync_now", ExistingWorkPolicy.REPLACE, nowRequest)

    val periodicRequest = PeriodicWorkRequestBuilder<SyncWorker>(6, TimeUnit.HOURS)
        .setConstraints(constraints)
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL,
            WorkRequest.MIN_BACKOFF_MILLIS, TimeUnit.MILLISECONDS).build()
    wm.enqueueUniquePeriodicWork("sync_periodic",
        ExistingPeriodicWorkPolicy.KEEP, periodicRequest)
}
```

在 `Application.onCreate()` 调一次即可，两个入队都幂等。**为什么不是一个请求 / 一个名字（常见坑）**：
- 周期任务入队后**首次执行在一个周期之后**（6 小时后才跑），启动那次必须 OneTime 补。
- 两类请求**不能共用 unique name**：OneTime 用 REPLACE 覆盖同名 periodic 会把整条周期链取消掉；UPDATE 策略又不允许改变请求类型。

**③ 跨名字撞车兜底（single-flight）**：两个名字理论上可能撞车（周期任务触发时启动同步正在跑），Worker 内用 companion 的 `AtomicReference<Job?>` 互踢——新实例 `getAndSet(job)?.cancel()` 取消旧实例；业务要「排队」就换 Mutex。

**⑤ UI 观察**：`combine` 两个名字的 Flow → StateFlow（`WhileSubscribed(5_000)`）→ Compose `collectAsStateWithLifecycle()`。状态映射：RUNNING / ENQUEUED（首排）/ BLOCKED → 同步中（BLOCKED = 等网络；`runAttemptCount > 0` 的 ENQUEUED 显示「重试第 N 次」）；SUCCEEDED → 成功；FAILED / CANCELLED → 失败。

细节：**SUCCEEDED 是瞬时态**——周期任务成功后立刻回 ENQUEUED 等下一轮，UI 的「成功」要么当一次性事件消费、要么结合 outputData 里的完成时间展示；加分项 `WorkInfo.nextScheduleTimeMillis`（2.8+）可显示「下次同步：xx:xx」。

---

### 精通档

#### Q4.1（原理深挖）：从 enqueue() 返回到 doWork() 真正执行，内部发生了什么？

**全链路鸟瞰**：

```
enqueue()
 ├─ WorkContinuationImpl：WorkRequest 翻译成实体，
 │   一个 Room 事务写入 WorkDatabase（workspec / dependency / worktag / workname）
 └─ Schedulers.schedule(...)
       ├─ GreedyScheduler.schedule()      ← 进程内快路径
       └─ SystemJobScheduler.schedule()   ← 系统托管路径（JobInfo 交 JobScheduler）
              （API < 23：SystemAlarmScheduler = AlarmManager + 广播链）
两条路汇聚同一入口：
WorkManagerImpl.startWork(workSpecId)
 └─ WorkerWrapper（跑在 Configuration 的 worker 执行池）
      ├─ DB 事务：原子地把 ENQUEUED → RUNNING（谁改成功谁执行，输家退出）
      ├─ WorkerFactory 创建实例 → CoroutineWorker.startWork()
      │     = CoroutineScope(Dispatchers.Default).launch { doWork() }
      └─ 结果落库；RETRY 算退避 + runAttemptCount+1；周期任务滚动 periodStartTime、唤醒子任务
```

**① 持久化——Room 库，不是内存队列**：可靠性承诺全靠 `WorkDatabase`（应用私有目录，WAL 模式）。核心表：`workspec`（类名 / state / Data blob / 约束列 / 退避 / run_attempt_count / period_start_time；**Data 限 10KB 就因为它要整体落库**）、`dependency`（链式父子边）、`workname`（unique name 注册表，KEEP/REPLACE 判断依据）、`systemidinfo`（workSpecId UUID ↔ JobScheduler int jobId 映射，跨重启对得上）。enqueue 返回的 Operation 在事务提交后完成——之后无论进程死活，任务事实活在磁盘和系统服务里。

**② 双调度器分工**：
- **GreedyScheduler**（快路径）：enqueue 后立刻被调，订阅各约束 tracker；约束已满足的任务**不做任何系统调用**，直接 `startWork()` 进程内开跑——没有 IPC、没有 JobScheduler 调度延迟和限额，「进程活着入队即执行」靠它。
- **SystemJobScheduler**（托管路径）：WorkSpec 翻译成 JobInfo（约束→`setRequiredNetworkType`，延迟→`setMinimumLatency`，`setPersisted(true)`）交给 system_server 里的 JobScheduler；到点回调 `SystemJobService.onStartJob()` → 仍走 `startWork()`——**执行永远发生在自己进程里，SystemJobService 只是「闹钟」**；`onStopJob` 对应 stop 链路（协程取消 + onStopped()）。API < 23 用 SystemAlarmScheduler 等价实现。
- **为什么两套都要**：只有 Greedy——进程一死没人跑，可靠性破产；只有 JobScheduler——进程活着也得等系统调度，「立即执行」做不到。**两套会重复触发但不会重复执行**：都指向 startWork，WorkerWrapper 在 DB 做条件更新（`UPDATE ... SET state=RUNNING WHERE id=? AND state=ENQUEUED`），只有一个线程改得动，输家放弃；SystemJobService 还核对 DB 状态剔除陈旧 job。

**③ 被杀 / 重启恢复**：进程被杀——调度事实有两份（磁盘 DB + system_server 的 JobInfo），约束满足时系统 bind SystemJobService 把进程拉起来执行；设备重启——JobInfo `setPersisted(true)`（库自动合并 `RECEIVE_BOOT_COMPLETED`）+ 开机/时间变化广播走 `rescheduleEligibleWork()` 全量重注册，双保险；进程重启自愈——初始化时把遗留 RUNNING 复位回 ENQUEUED（进程都没了不可能真在跑），runAttemptCount / 退避 / periodStartTime / 依赖图全在 DB，进度不丢。

**④ 线程环境（两层分离，易混淆）**：
- **函数体跑哪**：`CoroutineWorker.startWork()` 自己 `CoroutineScope(Dispatchers.Default).launch { doWork() }`——默认在 Dispatchers.Default（CPU 池），不在主线程也不在 WM executor；跑 IO 要自己 `withContext(Dispatchers.IO)`。`onStopped()` → `job.cancel()` → doWork 在挂起点收 `CancellationException`——这正是「阻塞调用感知不到取消」的根源。
- **占哪个坑**：WorkerWrapper（DB 校验 / 状态迁移 / 结果落库）跑在 Configuration 的 worker 执行池，每个运行中 Worker 占一个线程坑；默认池很小（`max(2, min(CPU 核数, 4))`，`setExecutor()` 可调）。
- **与并发上限的关系**：GreedyScheduler 对合格任务全放行、自己不设闸——**真正的进程内并发上限就是 worker 执行池大小**（塞 20 个合格任务实际也就 2~4 个在跑）；`Configuration.maxSchedulerLimit`（默认 20）限的是交给 JobScheduler 托管的触发器数量，不是同时在执行的数量。

> 一句话：入队 = 落库 + 通知两套调度器；执行永远在本进程、以 DB 原子状态迁移做幂等闸门；可靠性 = 磁盘 DB（事实）+ JobScheduler（闹钟）双份冗余。

#### Q4.2（架构排障）：IM App 拆了 `:push` 进程，push 进程入队「消息上报」、主进程也入队同类任务，线上偶发重复上报——为什么默认挡不住？方案与取舍？

**根因一句话：WorkManager 运行时「每进程一个」，两个进程共享同一个 workdb 文件，但所有协调逻辑都是进程内的——两套实例互不知晓，靠踩数据库状态互相干扰。** 具体踩法：

1. **初始化自愈互踩（最典型重复源）**：任何进程初始化 WM 都会把 DB 里的 RUNNING 复位成 ENQUEUED；push 进程被频繁杀死/拉起，每次重启都可能把主进程正在执行的任务复位回队 → 再被调度一次。
2. **STOP/取消不跨进程**：REPLACE / cancel 只改 DB + 通知**本进程**运行时；另一进程正在跑的 WorkerWrapper 收不到 stop，照常跑完——「后来取消先来」跨进程直接失效。
3. **双 GreedyScheduler**：两个进程的 greedy 都从 DB 捞 ENQUEUED 任务开跑；ENQUEUED→RUNNING 原子更新是闸门，但叠加第 1 条的复位后拦不住已错乱的状态。
4. **unique name 只有一半语义**：KEEP 查库跨进程可见、大体能挡；REPLACE 依赖「取消正在运行的实例」，跨进程不成立——所以是**偶发**而非必然，取决于进程生命周期交错。

**方案 A（默认推荐）——收敛所有权，push 进程不碰 WorkManager**：push 进程只做「投递」（bind/start 主进程 Service、广播、或写本地队列表由主进程消费），所有 enqueue 在主进程。契合执行模型：Worker 执行本来就发生在默认进程（SystemJobService 在主进程），push 进程从头到尾不需要「拥有」WM——它只是消息入口。根因修复：默认 startup 初始化 provider 只装在主进程，`:push` 之所以有实例是代码自己调了 `getInstance()`，删掉这些调用点互踩就消失。

**方案 B——work-multiprocess**：push 进程改用 `RemoteWorkManager.getInstance(context)`。核心机制：**单实例原则**——DB、调度器、执行池只属于主进程（primary instance）；RemoteWorkManager 本质是 Binder 客户端，所有操作经 AIDL 转发给主进程的 `SystemRemoteWorkManagerService` 代为执行——不是加锁，而是把「多进程并发访问」收敛成「远程调用单实例」，竞态从根上消失；push 进程先启动时 bind 会把主进程带起。**它不解决的事**：Worker 仍只在主进程执行，multiprocess 只让次要进程变「遥控器」，没有让任务跑在 `:push` 里的能力。

**无论哪个方案：幂等兜底**——按 msgId 服务端去重；调度层只能把重复概率压到极低，最后一道防线在业务层。

**引入判断标准**（不是「App 有多进程」，而是「多进程是否都频繁直接操作 WM 且想保留其语义」）：
- **值得**：多进程都是重度调用方（高频入队 / 查状态 / 依赖 unique / REPLACE / cancel 语义），且收敛到主进程改造成本高（跨模块跨团队）——一条 IPC 换语义正确性，划算。
- **不值得**：次要进程入队频率低、任务形态简单（本 IM 场景大概率如此）——方案 A 一个转交 Service 就解决，少依赖少一层 IPC 少「主进程单点」心智负担；何况 multiprocess 每次入队同样要 bind 主进程，延迟和拉活成本没省。
- **都不合适**：真实需求若是「主进程死了也要由 push 进程完成上报」——两方案都做不到（Worker 永远跑主进程），push 进程自己起前台服务 + 本地持久化重试更对路。