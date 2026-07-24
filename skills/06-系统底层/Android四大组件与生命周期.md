---
title: Android 四大组件与生命周期
domain: 06-系统底层
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [四大组件, 生命周期, Activity]
related: [Handler 消息机制]
---

# Android 四大组件与生命周期

## 概述
Android 应用的基石:**Activity**(界面,完整生命周期 onCreate→onStart→onResume→onPause→onStop→onDestroy,及配置变更 / 异常重建)、**Service**(后台,started / bound 两种模式,Android 8+ 后台限制严)、**BroadcastReceiver**(广播,静态 / 动态注册)、**ContentProvider**(跨进程数据共享)。`Context` 是访问系统资源的入口。生命周期管理是高级开发的核心——内存泄漏、状态恢复、进程优先级都与之相关。Android 10+ 还有作用域存储、后台启动限制等演变。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. Activity 与完整生命周期
Activity 是界面载体,生命周期方法按序:`onCreate`(初始化、setContentView)→ `onStart`(可见)→ `onResume`(可交互、获焦)→ `onPause`(失焦、部分遮挡)→ `onStop`(不可见)→ `onDestroy`(销毁)。
关键:用户可见 = 已过 onStart;可交互 = 已过 onResume。`onPause` 应轻量(它会阻塞下一个 Activity 显示),耗时清理放 onStop。系统因内存压力杀进程时 onStop 之后可能不回调 onDestroy。

### 2. Fragment 生命周期与 Activity 的关系
Fragment 寄生于 Activity,生命周期更细(onAttach/onCreate/onCreateView/onViewCreated … onStart … onResume … onPause … onStop … onDestroyView/onDestroy/onDetach)。它区分「实例生命周期」与「视图生命周期」(`viewLifecycleOwner`)。现代做法是 Navigation + 单 Activity + 多 Fragment;Fragment 重建易踩坑——视图重建但实例可保留。

### 3. 配置变更、异常重建与状态保存
- **配置变更**(转屏等)默认销毁重建 Activity;除非 manifest 声明 `configChanges` 自行处理(一般不推荐,用 ViewModel 更稳)。
- **异常重建**:系统因内存杀进程后,用户回来 Activity 会重建。`onSaveInstanceState` 保存少量 UI 状态(注意 **API 28+ 在 onStop 之后**调用,旧版本在 onPause 之前)。
- **正确姿势**:UI 数据放 **ViewModel**(配置变更后存活)+ **SavedStateHandle**(进程被杀后存活);持久数据落库 / Repository。别往 onSaveInstanceState 塞大对象(受 Binder 1MB 限制)。

### 4. Service(started / bound / foreground + 后台限制)
- **started**:`startService`,独立运行,需 `stopSelf` / `stopService` 停。
- **bound**:`bindService`,与调用者绑定,无绑定时销毁,可 IPC 通信。
- **foreground**:前台服务,常驻通知,优先级高不易被杀(音乐 / 导航 / 下载)。
版本限制:
- **Android 8+(O)**:后台 App 不能 `startService`,要用 `startForegroundService` 并在 **~5s 内调 startForeground**(否则 ANR / 崩溃)。
- **Android 14(API 34)**:前台服务**必须声明 `foregroundServiceType`**(camera / location / mediaPlayback / dataSync / …),类型与权限要匹配,否则启动崩溃 / Play 拒审:

```xml
<service android:name=".MusicService"
         android:foregroundServiceType="mediaPlayback"/>
```

现代趋势:可靠后台任务优先用 WorkManager(见 [[WorkManager 后台任务]]),而非裸 Service。

### 5. BroadcastReceiver(静态 / 动态)
接收系统 / App 广播。
- **静态注册**:manifest `<receiver>`,App 未启动也能收(历史上的保活手段)。
- **动态注册**:代码 `registerReceiver`,需随组件生命周期 `unregisterReceiver`。
版本限制:
- **Android 8+(O)**:大部分**隐式广播不再投递给静态注册接收器**(少数例外如 BOOT_COMPLETED),旨在省电。需要时改动态注册或 JobScheduler / WorkManager。
- **Android 13+(T)**:动态注册接收器必须显式指定 **`RECEIVER_EXPORTED` 或 `RECEIVER_NOT_EXPORTED`**,否则抛 SecurityException(区分是否接收其他 App 广播)。
- **Android 12+(S)**:**PendingIntent 必须指定可变性**——`FLAG_IMMUTABLE`(推荐)或 `FLAG_MUTABLE`,否则崩溃。

### 6. ContentProvider(跨进程数据共享)
标准化地暴露数据给其他 App / 进程,基于 URI + CRUD(insert/query/update/delete)。系统 Provider:Contacts、MediaStore(图库)、Settings 等。本质是「跨进程数据接口」,自带权限校验。注意 **作用域存储(Android 10+)**:直接读外部存储目录被限制,多媒体走 MediaStore、文档走 SAF。App 间共享数据常用 ContentProvider 或 FileProvider(分享文件)。

### 7. Context 与进程优先级
`Context` 是访问系统资源(资源、数据库、SharedPreferences、启动组件、inflate)的入口,分 Application / Activity / Service Context。四大组件存活影响**进程优先级**:前台(可见 / 前台服务)> 可见 > 服务 > 缓存(后台 Activity)。低内存时系统优先杀缓存进程——这是「保活」难的根本原因:无前台形态的后台进程随时可被杀。

### 8. 生命周期与内存 / 稳定性衔接
生命周期是内存泄漏与稳定性的高发区:
- 非静态内部类(Handler、匿名 Runnable)默认持有外部 Activity → 泄漏;改 static + WeakReference 或用 LifecycleScope 协程。
- 静态 / 单例持有 Context 用 ApplicationContext 而非 Activity。
- 长任务绑生命周期:`lifecycleScope` / `viewModelScope`(协程随 Lifecycle 自动取消)。
- 与 Jetpack 衔接:Lifecycle / LiveData / ViewModel 都建立在组件生命周期之上(见 [[MVVM 架构]]、[[Hilt 依赖注入]])。

## 实践经验 / 踩坑

1. **异常重建丢状态**:别依赖成员变量,重建后为 null。UI 状态用 ViewModel,进程级用 SavedStateHandle,持久数据落库。
2. **startForegroundService 5s 规则**:Android 8+ 调用后必须 ~5s 内 startForeground 显示通知,否则 ANR / 崩溃;Android 14 还要声明匹配的 foregroundServiceType。
3. **静态广播失效**:Android 8+ 隐式广播不投递静态 receiver。排查「收不到系统广播」先想这点;改动态注册或 WorkManager。
4. **动态广播 RECEIVER_EXPORTED**:Android 13+ 不加标志直接崩;只在确实要收其他 App 广播时用 EXPORTED,内部广播用 NOT_EXPORTED。
5. **PendingIntent 崩溃**:Android 12+ 不加 FLAG_IMMUTABLE / MUTABLE 直接崩;优先 IMMUTABLE(除非需让接收方改 extra)。
6. **内存泄漏**:Handler / 静态字段 / 单例持 Activity 是经典坑;用 LeakCanary 抓,协程用生命周期感知 scope。
7. **保活不可靠**:无前台形态的后台进程随时被杀;真正需要常驻用前台服务(且符合 Google 政策)或 WorkManager 的可靠重试,别用黑科技保活(会被系统 / 商店限制)。

## 待深入 / 下一步
- [ ] LifecycleRegistry 与 LifecycleScope 原理(见 [[MVVM 架构]])
- [ ] WorkManager 如何取代后台 Service(见 [[WorkManager 后台任务]])
- [ ] SavedStateHandle 存活原理(进程被杀后如何恢复)
- [ ] 多进程(android:process)、ContentProvider 跨进程与 Binder(见 [[Binder 原理]])
- [ ] Android 各版本后台限制演进(O / S / T / U)

## 参考资料
- Activity 生命周期:https://developer.android.com/guide/components/activities/activity-lifecycle
- 应用基础与四大组件:https://developer.android.com/guide/components/fundamentals
- Android 14 行为变更:https://developer.android.com/about/versions/14/behavior-changes-14
- Services 概览:https://developer.android.com/guide/components/services
