---
title: WorkManager 后台任务
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
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

## 实践经验 / 踩坑

1. **Data 大小限制**:约 10KB,大文件传 URI / 路径,Worker 内读;塞大对象会崩。
2. **周期任务最小 15 分钟**:且系统可能延迟,不能当精确闹钟(用 AlarmManager)。
3. **Worker 默认主线程**:`doWork` 耗时要用 `CoroutineWorker` 或自行切线程,否则 ANR。
4. **退出 App 后**:任务会继续 / 恢复,但服从系统策略;别假设「立刻跑」。
5. **用户可感知的长任务**:用 `setForeground`(把 WorkManager 任务转前台服务 + 通知),满足 Android 后台限制。

## 待深入 / 下一步
- [ ] 调度器内部(GreedyScheduler / SystemJobScheduler / SystemAlarmScheduler)
- [ ] 自定义 Configuration(Worker 工厂、初始化、日志级别)
- [ ] 多进程 App 与 WorkManager
- [ ] 与 Foreground Service 的 `setForeground` 结合(见 [[Android 四大组件与生命周期]])

## 参考资料
- WorkManager 概览:https://developer.android.com/topic/libraries/architecture/workmanager
- WorkManager 测试:https://developer.android.com/topic/libraries/architecture/workmanager/testing
- 持久化任务调度:https://developer.android.com/guide/background/persistent
