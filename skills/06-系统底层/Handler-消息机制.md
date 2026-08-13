---
title: Handler 消息机制
domain: 06-系统底层
level: 精通
target: 精通
importance: 高
last_assessed: 2026-08-13
last_reviewed: 2026-08-13
next_review: 2027-02-09
tags: [Handler, Looper, 消息队列]
related: [Kotlin 协程]
---

# Handler 消息机制

## 概述
Android 主线程消息循环的基础:Handler 发消息 / Runnable → `MessageQueue`(按时间排序的单链表)→ `Looper.loop()` 取出 → 分发回 `Handler.handleMessage`。**线程切换**(子线程 post 到主线程)本质靠它;底层用 epoll(管道唤醒)避免空轮询阻塞。主线程 Looper 在 `ActivityThread.main` 启动。Handler 持 Activity 导致的**内存泄漏**是经典考点(用静态内部类 + 弱引用规避)。

## 考核记录
- **2026-08-13** 判定：(待考核) → 精通 ✅ ｜ 考官：AI
  - 表现：四要素 + epoll 机制完整；跨线程 post 代码首次有误经引导后修正；内存泄漏问题完整三步回答；同步屏障 skip 逻辑理解到位
  - 依据：四档全部通过，了解→精通突破

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

## 各档考核 Q&A

### 了解档

**Q1: Handler 是什么？它解决什么问题？**

> Handler 是 Android 的消息发送与处理机制，用于**线程间通信**。它解决的问题是：Android 规定只有主线程能更新 UI，但耗时任务必须在子线程执行——Handler 充当"桥梁"，在子线程发消息，主线程收消息并更新 UI，实现**线程切换**。

**Q2: Handler 四要素是哪四个？各自的作用是什么？**

> - **Handler**：发送消息 (`sendMessage`/`post`) 并处理 (`handleMessage`)
> - **Message**：消息载体，带 `what`/`obj`/`arg` 等数据，通过对象池复用
> - **MessageQueue**：消息队列，按 `when`(时间) 升序排列的**单链表**，负责消息的存储与排序
> - **Looper**：循环从队列取消息、分发给对应 Handler；每个线程最多一个（存在 ThreadLocal 中）

---

### 熟悉档

**Q1: 描述一次 Handler 消息从发送到处理的完整流转过程。**

> 1. `handler.sendMessage(msg)` 或 `handler.post(Runnable)`（内部把 Runnable 包装成 Message）
> 2. `MessageQueue.enqueueMessage` 按 `when`（时间戳）将消息插入队列正确位置
> 3. `Looper.loop()` 死循环调用 `queue.next()` 取出队首消息（队列空时线程阻塞在 epoll）
> 4. `msg.target.dispatchMessage(msg)` 将消息分发给发送它的 Handler
> 5. 回调 `Handler.handleMessage(msg)` 或执行 Runnable.run()

**Q2: 子线程为什么不能直接 new Handler？不报错的做法是什么？**

> 子线程默认没有 Looper，直接 `new Handler()` 会报「Can't create handler inside thread that has not called Looper.prepare()」。正确做法：
> ```java
> Looper.prepare();          // 在当前线程创建 Looper（存入 ThreadLocal）
> Handler handler = new Handler(Looper.myLooper());
> Looper.loop();             // 启动消息循环（此行之后的代码不会执行，通常新开线程）
> ```
> 如果要和主线程交互，用主线程已有的 Looper 即可，无需 prepare。

**Q3: Message.obtain() 相比 new Message() 有什么优势？为什么？**

> `Message.obtain()` 从**对象池**复用已回收的 Message，比 `new Message()` 减少内存分配开销。频繁发消息时（大量 UI 更新）性能差异明显。

---

### 掌握档

**Q1: Handler 内存泄漏的原因是什么？如何彻底规避？**

> **原因**：非静态内部类 Handler 隐式持有外部 Activity（因为 Handler 需要访问 Activity 的成员）。若 Handler 有延迟消息未执行，Activity 销毁后消息仍持有 Handler → Activity 泄漏。
>
> **规避方法**：
> 1. 使用**静态内部类**（不持有外部类引用）
> 2. 静态内部类用**弱引用**持有 Activity：`static class SafeHandler extends Handler { WeakReference<Activity> ref; }`
> 3. Activity `onDestroy` 中调用 `handler.removeCallbacksAndMessages(null)` 清空队列
> 三步缺一不可，只清队列不改内部类结构仍可能泄漏。

**Q2: MessageQueue 的同步屏障（sync barrier）是什么？它如何影响消息调度？**

> 同步屏障是一个特殊的 Message，其 `target` 字段为 null。插入队列队首后，`next()` 遍历时会**跳过所有普通同步消息**，只取出设置了 `setAsynchronous(true)` 的**异步消息**。
>
> **用途**：系统用它让 UI 渲染相关的帧消息（Choreographer 驱动）优先于普通业务消息，保证动画/滑动的流畅性。
>
> **插入方式**：`MessageQueue.enqueueMessage()` 在 barrier 的 `when` 时间点自动将 barrier 置于同步消息之前。

**Q3: 子线程发消息到主线程的完整代码示例：**

> ```java
> // 在子线程
> new Thread(() -> {
>     Looper.prepare();                     // 创建子线程 Looper
>     Handler workerHandler = new Handler(); // 默认用当前线程的 Looper
>
>     // 如果要发到主线程
>     Handler mainHandler = new Handler(Looper.getMainLooper());
>     mainHandler.post(() -> {
>         // 这里的代码在主线程执行，可更新 UI
>         // textView.setText("done");
>     });
>
>     Looper.loop(); // 开始循环（此行之后代码不会继续向下执行）
> }).start();
> ```

---

### 精通档

**Q1: MessageQueue.next() 在队列为空时如何避免 busy-wait（空转浪费 CPU）？底层用的是什么机制？**

> 队列空时线程**阻塞休眠**，不空转。底层用 **epoll** 监听一个**管道（pipe）**的文件描述符：
> - `MessageQueue` 持有管道的写端和读端 fd
> - `next()` 调用 `nativePollOnce(blocking, timeout)` → Native 层 `epoll_wait` 阻塞在管道的读端 fd
> - 有新消息入队时，`enqueueMessage` → 往管道**写端写入数据** → epoll 唤醒阻塞的 `next()`
> - 对于延迟消息，用 timeout 参数让 `epoll_wait` 在到期时间自动唤醒
>
> **关键**：`Looper.loop()` → `MessageQueue.next()` → **Native 层 epoll** → 线程不耗 CPU 地等待。

**Q2: 假设在主线程 post 一个 5 秒延迟的 Runnable，5 秒内主线程能响应其他消息吗？分两种情况讨论：**

> **情况一：5 秒内没有其他消息入队**
> 主线程在 `Looper.loop()` 的 `MessageQueue.next()` 中被 `epoll_wait` 阻塞（不占 CPU），5 秒后到期自动唤醒，执行该 Runnable。

> **情况二：5 秒内有其他消息（如用户点击）入队**
> `enqueueMessage` 写入管道 → epoll 立即唤醒 → `next()` 返回**时间最接近当前时间**的消息（即刚入队的消息）→ **插队执行**，点击事件先被处理，5 秒 Runnable 仍在队列中等。
>
> **结论**：延迟消息**不阻塞**队列中的其他消息，`next()` 始终返回队首（按时间），延迟只是"到期才出队"。

**Q3: 同步屏障在 Choreographer 帧调度中的作用是什么？为什么 View.post() 不能保证在下一帧之前执行？**

> **Choreographer 帧调度流程**：
> 1. `Choreographer.postFrameCallback` 插入一个**异步消息**到队首（带同步屏障）
> 2. 同步屏障让 `next()` 跳过普通消息，先取出帧回调
> 3. 帧回调执行 → 触发 `doTraversal()` → 绘制
>
> **View.post() 不能保证在下一帧之前执行的原因**：
> `View.post(Runnable)` 将 Runnable 包装成 Message 加入队列，**它是普通同步消息**。若队列中在此之前有其他同步消息（包括旧的未处理消息、同步屏障后的普通消息），它们会排在 View.post 的消息**之前**执行，导致 Runnable 延迟到下一帧之后。
>
> **正确做法**：若必须在下一次绘制前执行，用 `Choreographer.postFrameCallback`（插入异步消息，可被同步屏障优先处理）。

**Q4: 手动调用 `Looper.quit()` 和 `Looper.quitSafely()` 的区别是什么？**

> - `quit()`：**直接移除所有消息**，队列清空，`next()` 返回 null，`loop()` 退出。已入队的延迟消息被丢弃。
> - `quitSafely()`：**安全退出**，只移除尚未到达执行时间的消息，队列中**已到期的消息仍会被处理完**再退出，保证消息处理的完整性。
>
> **适用场景**：一般用 `quitSafely()` 更安全；需要立即终止（如 Activity 销毁）且确定无需处理剩余消息时用 `quit()`。

**Q5: Handler 与协程 Dispatcher（特别是 Dispatchers.Main）的线程切换有何本质区别？**

> | | Handler | 协程 Dispatcher |
> |---|---|---|
> | **切换机制** | 消息入队，epoll 阻塞/唤醒 | 挂起/恢复，基于 Continuations |
> | **线程占用** | 发送线程发出后立即继续执行，接收线程从队列取消息执行 | 切出协程释放线程，调度器在目标线程恢复协程 |
> | **表达能力** | 只能"发消息等待处理" | 可以顺序写异步代码（`await` 挂起），更直观 |
> | **底层** | 仍然依赖 `Looper.loop()` / `MessageQueue` | `Dispatchers.Main` 底层就是 Handler（主线程 Looper） |
>
> **本质**：协程的 `Dispatchers.Main` **最终依赖 Handler / Looper**，只是用 suspend 机制把"等消息"包装成了顺序代码。Handler 是底层实现，协程是上层抽象。

## 参考资料

- 进程与线程 / Handler:https://developer.android.com/guide/components/processes-and-threads
- Looper / MessageQueue:`android.os`
- Handler 源码:https://cs.android.com/android/platform/superproject/+/master:frameworks/base/core/java/android/os/Handler.java