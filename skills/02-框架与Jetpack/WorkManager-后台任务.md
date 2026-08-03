---
title: WorkManager 后台任务
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-11-27
tags: [WorkManager, 后台, 任务]
related: [Android 四大组件与生命周期]
---

# WorkManager 后台任务

## 概述
Jetpack 的**可靠后台任务**方案:适合「需要保证执行、但可延迟」的任务(上传日志、同步数据、定期清理)。系统会根据电量 / 网络 / 约束择机执行,即使 App 退出或重启也能补跑(持久化 + 重启恢复)。替代了 Service + AlarmManager 的碎片化方案,适配 Android 后台限制。区分:即时任务用协程 / 前台服务,可靠延迟任务用 WorkManager。支持约束(网络 / 充电)、链式任务、周期任务。

## 考核记录
（尚未考核）

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