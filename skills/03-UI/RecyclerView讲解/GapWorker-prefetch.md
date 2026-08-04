---
title: RecyclerView 预取源码(GapWorker)
domain: 03-UI
level: 熟悉
target: 掌握
importance: 中
last_assessed: 2026-08-04
last_reviewed: 2026-08-04
next_review: 2026-10-03
tags: [RecyclerView, 源码, 预取, GapWorker, 性能]
related: [RecyclerView 四级缓存, RecyclerView 源码解析(Recycler / RecycledViewPool)]
---

# RecyclerView 预取源码(GapWorker)

## 概述
`GapWorker` 是 RecyclerView 自 25.1.0 起内置的**预取器**:在**主线程帧间隙的空闲时间**提前 `create` + `bind` 即将滑入屏幕的 ViewHolder,把「下一屏要付的建造成本」挪到空闲帧,从而降低实际滚动帧的掉帧。本篇读它的触发时机、时间预算(`deadlineNs`)、以及它如何复用 [[RecyclerView 源码解析(Recycler / RecycledViewPool)]] §5 那条 deadline 钩子。

## 考核记录
- **2026-08-04** 判定：了解 → 熟悉 ✅ ｜ 考官：AI
  - 表现：prefetch 主线程本质与 Choreographer 触发机制答得准确；gatherPrefetchPositions 作用理解正确；掌握档流程细节不熟，主动要求补充。
  - 依据：前两档稳稳通过，掌握档对 deadlineNs 全链路传递不熟，需继续补充。

## 核心原理 / 关键点

> 下方源码**简化改写自 AOSP / androidx**(保留结构,非逐字)。

### 1. 关键认知:跑在主线程帧间隙,不是子线程

这是最常被讲错的一点。GapWorker 由 **`Choreographer` 的帧回调**驱动,在**当前帧绘制完成后的空闲时间**跑,且**全程主线程**:

```java
// 简化自 GapWorker(它本身 implements Runnable / FrameCallback)
void doFrame(long frameTimeNanos) {
    long deadlineNs = frameTimeNanos + 剩余帧预算;
    if (有待预取任务) {
        把 mLauncher(Runnable)投递到主线程 Handler 执行;   // 仍主线程
    }
}
```

> ❌ 误区:「prefetch 在子线程预创建」。✅ 实情:**主线程帧间隙**,所以 `onBindViewHolder` 依然不能做阻塞 IO——预取也跑在主线程。

### 2. 一个主线程一个 GapWorker(ThreadLocal 共享)

```java
// 简化自 RecyclerView
static final ThreadLocal<GapWorker> sGapWorker = new ThreadLocal<>();
```

- GapWorker 是**主线程级的单例**,所有 RecyclerView **共享同一个**。
- RV `onAttachedToWindow` 时 `gapWorker.add(this)`,把自己登记进 GapWorker 的 `mRecyclerViews` 列表;`onDetachedFromWindow` 时移除。

### 3. 触发时机

- RV 滚动 / 布局后,LayoutManager 预测「哪些 position 马上要出现」。
- GapWorker 在每帧 `doFrame` 检查是否有预取任务,有则按预算排入执行。
- 开关:`LayoutManager.isItemPrefetchEnabled()`(默认 **true**);可 `setItemPrefetchEnabled(false)` 关闭。

### 4. 时间预算(deadlineNs):绝不抢当前帧

- 帧间隔约 vsync 16ms。`doFrame` 拿到 `frameTimeNanos`,算出本帧**剩余预算**作为 `deadlineNs`。
- `if (System.nanoTime() > deadlineNs) return;` —— 预取只在富余时间内做,不拖慢当前帧绘制;没时间就不预取(不亏)。

### 5. 选哪些位置预取:`gatherPrefetchPositions`

```java
// 简化自 GapWorker.buildTaskList / LayoutManager
void buildTaskList() {
    for (RecyclerView rv : mRecyclerViews) {
        int[] positions = rv.mLayout.gatherPrefetchPositions(/* 滚动方向/速度 */);  // 约前/后各 4 个
        // 每个位置算一个 Task,带「距离」=多快会滑入屏幕
    }
    按距离排序;   // 越快出现的越优先
}
```

- `LinearLayoutManager` 等内置 LayoutManager 实现了 `gatherPrefetchPositions`:依滚动方向/速度,选出最可能滑入屏幕的若干 position。
- **自定义 LayoutManager 必须自己实现 `collectAdjacentPrefetchPositions` / `gatherPrefetchPositions`,预取才会生效**(见踩坑)。

### 6. 执行:对接 Recycler 的 deadline 钩子

```java
// 简化自 GapWorker.flushTasksWithDeadline / prefetchPositionWithDeadline
ViewHolder prefetchPositionWithDeadline(Task task, long deadlineNs) {
    return task.view.mRecycler.tryGetViewHolderForPositionByDeadline(
        task.position, /* dryRun */ false, deadlineNs);   // 复用 §5 的 deadline 感知路径
}
```

- 预取直接走到 [[RecyclerView 源码解析(Recycler / RecycledViewPool)]] §3/§5 的**同一条查找链**,只是带上 `deadlineNs`。
- 预创建 + 预绑定的 holder 留在 Recycler 缓存里;**真正 layout 那一帧** `getViewForPosition` 直接命中、跳过 create+bind → 滚动更顺。
- 预算不足时 `tryBindViewHolderByDeadline` 提前返回(holder 已 create 但未 bind),把 bind 留到下一帧。

### 7. 源码骨架汇总

```java
// 简化自 androidx...RecyclerView.GapWorker(非逐字)
final class GapWorker implements Runnable {
    static ThreadLocal<GapWorker> sGapWorker = new ThreadLocal<>();     // 主线程单例,多 RV 共享
    final ArrayList<RecyclerView> mRecyclerViews = new ArrayList<>();
    private final Runnable mLauncher = () -> prefetch(本帧 deadlineNs);

    void add(RecyclerView rv)    { mRecyclerViews.add(rv); }
    void remove(RecyclerView rv) { mRecyclerViews.remove(rv); }

    void doFrame(long frameTimeNanos) {
        long deadlineNs = frameTimeNanos + 剩余预算;
        if (有任务) 投递 mLauncher 到主线程 Handler;
    }
    void prefetch(long deadlineNs) {
        buildTaskList();                  // 各 LayoutManager.gatherPrefetchPositions 汇总 + 按距离排序
        flushTasksWithDeadline(deadlineNs); // 预算内逐个 tryGetViewHolderForPositionByDeadline
    }
}
```

### 8. 调优与限制

- 默认开启,长列表几乎无脑收益。
- **依赖 LayoutManager 实现预取位置预测**:内置三种都有;自定义 LayoutManager 要实现才有。
- 预取也在主线程,所以 `onBindViewHolder` 慢 = 预取也卡主线程,**慢 bind 会反过来拖累**(见踩坑)。

## 实践经验 / 踩坑

1. **误以为预取在子线程** —— 实为主线程帧间隙;`onBindViewHolder` 仍不可做阻塞 IO / 重计算,否则预取反而抢主线程时间。
2. **自定义 LayoutManager 预取不生效** —— 没实现 `collectAdjacentPrefetchPositions` / `gatherPrefetchPositions`,GapWorker 拿不到预取位置。
3. **bind 本身慢时预取帮倒忙** —— 预取把 bind 提前到当前帧,若 bind 很重,反而拖慢当前帧;先把 bind 做轻(异步图片、缓存计算)。
4. **多 RV 共享一个 GapWorker** —— 任务按距离统一排序,优先级高的 RV 先预取;别误以为每个 RV 独立预取线程。

## 待深入 / 下一步
- [ ] 读 `doFrame` 与 `mLauncher` 投递 `Handler` 的精确时序(为何要 post 到 Handler 而非同步执行)。
- [ ] `isItemPrefetchEnabled`(RV 级)与 LayoutManager 级开关的优先级关系。
- [ ] 多 RV 共享 GapWorker 时,任务排序与预算如何在 RV 间分配。

## 参考资料
- androidx RecyclerView 源码(`GapWorker` 类):https://cs.android.com/androidx/platform/frameworks/support/+/master:recyclerview/recyclerview/src/main/java/androidx/recyclerview/widget/RecyclerView.java
- 配套:[[RecyclerView 四级缓存]]、[[RecyclerView 源码解析(Recycler / RecycledViewPool)]]
- 关键符号:`GapWorker`、`GapWorker.doFrame`、`LayoutManager.gatherPrefetchPositions`、`Recycler.tryGetViewHolderForPositionByDeadline`