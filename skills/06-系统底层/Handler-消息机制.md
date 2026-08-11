---
title: Handler 消息机制
domain: 06-系统底层
level: 了解
target: 精通
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-15
tags: [Handler, Looper, 消息队列]
related: [Kotlin 协程]
---

# Handler 消息机制

## 概述
Android 主线程消息循环的基础:Handler 发消息 / Runnable → `MessageQueue`(按时间排序的单链表)→ `Looper.loop()` 取出 → 分发回 `Handler.handleMessage`。**线程切换**(子线程 post 到主线程)本质靠它;底层用 epoll(管道唤醒)避免空轮询阻塞。主线程 Looper 在 `ActivityThread.main` 启动。Handler 持 Activity 导致的**内存泄漏**是经典考点(用静态内部类 + 弱引用规避)。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 为什么需要 Handler

Android 规定**只有创建 View 的线程(主线程)能更新 UI**;而耗时任务(网络 / IO)必须在子线程。任务完成后要「切回主线程更新 UI」——Handler 就是这个**线程切换**的桥梁:在子线程用 Handler 发消息,消息会在 Handler 所在 Looper 的线程被处理。

### 2. 四要素

- **Handler**:发送与处理消息(`sendMessage` / `post` → `handleMessage`)。
- **Message**:消息载体,带 what / obj / arg,通过对象池复用(用 `Message.obtain()` 而非 new)。
- **MessageQueue**:消息队列,按 `when`(时间)排序,底层是单链表。
- **Looper**:循环取出队首消息分发给对应 Handler;每个线程最多一个 Looper(存 ThreadLocal)。

### 3. 一次消息流转

`handler.sendMessage(msg)`(或 `post(Runnable)`,内部把 Runnable 包成 Message)→ `MessageQueue.enqueueMessage` 按 when 入队 → `Looper.loop()` 死循环调 `queue.next()` 取出队首 → `msg.target.dispatchMessage(msg)` → 回到 `Handler.handleMessage` / Runnable.run。

### 4. MessageQueue 排序与同步屏障

- 消息按 `when` 升序排列;延迟消息到点才出队,期间线程阻塞。
- **同步屏障(sync barrier)**:一个特殊的「target 为空」的 barrier 消息插入队首后,会让队列跳过后续普通同步消息、优先取出**异步消息**(`setAsynchronous(true)`)。系统用它让 UI 渲染(Choreographer 的帧消息)优先于普通消息。

### 5. 底层阻塞唤醒:epoll + 管道

`MessageQueue.next()` 没消息时不能 busy-wait(空转浪费 CPU):它用 **epoll** 监听一个管道(eventfd),队列空时线程**阻塞休眠**;有新消息(或到点)时通过管道写入唤醒。这是「消息没来时主线程不耗 CPU」的关键。

### 6. 主线程 Looper vs 子线程 Looper

- **主线程**的 Looper 在 `ActivityThread.main()` 里由系统 `Looper.prepareMainLooper()` 创建并 `loop()`,所以主线程天然有 Looper、能收 Handler 消息。
- **子线程**默认没有 Looper;要用自己的 Handler,需先 `Looper.prepare()`(创建 Looper 存入 ThreadLocal)再 `Looper.loop()`。

### 7. Handler 内存泄漏与规避

非静态内部类 Handler 隐式持有外部 Activity;若它有延迟未执行的消息,Activity 销毁后仍被 Message 持有 → 泄漏。规避:① **静态内部类 + 弱引用** 持 Activity;② Activity `onDestroy` 里 `handler.removeCallbacksAndMessages(null)` 清空消息队列。

### 8. 与现代 API 的关系

协程切线程(`Dispatchers.Main`)、`View.post`、`LiveData.postValue`、`runOnUiThread` 底层都**最终依赖 Handler / Looper**(主线程 Looper)。理解 Handler 就理解了 Android 主线程调度的根基。

## 实践经验 / 踩坑

1. **子线程 new Handler 崩** —— 没先 `Looper.prepare()` 直接 new 报「Can't toast on a thread that has not called Looper.prepare()」;先 prepare + loop 或用主线程 Handler。
2. **Message 不复用** —— 频繁 new Message 增开销;用 `Message.obtain()` 走对象池。
3. **Handler 持 Activity 泄漏** —— 延迟消息 + 非静态内部类;静态 + 弱引用 + `removeCallbacksAndMessages`。
4. **延迟消息忘了清** —— Activity 销毁后延迟消息仍执行,访问已销毁 View 崩;onDestroy 清队列。
5. **主线程消息队列阻塞** —— 一个耗时 message 占着主线程,后续(含 UI)全排队卡顿;耗时挪子线程。
6. **误以为 post 是开新线程** —— `handler.post` 只是把 Runnable 投递到该 Handler 的 Looper 线程,主线程 Handler 仍在主线程跑。
7. **混淆同步屏障 / 异步消息** —— 自定义一般用不到;了解即可,别误用 `setAsynchronous` 影响调度。

## 待深入 / 下一步

- [ ] 读 `Looper.loop` / `MessageQueue.next` / epoll 唤醒源码
- [ ] 理解同步屏障在 Choreographer 帧调度中的作用
- [ ] 对比 Handler 与协程 Dispatcher 的线程切换实现

## 参考资料

- 进程与线程 / Handler:https://developer.android.com/guide/components/processes-and-threads
- Looper / MessageQueue:`android.os`
- Handler 源码:https://cs.android.com/android/platform/superproject/+/master:frameworks/base/core/java/android/os/Handler.java