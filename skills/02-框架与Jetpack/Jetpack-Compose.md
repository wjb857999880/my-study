---
title: Jetpack Compose
domain: 02-框架与Jetpack
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-10
next_review: 2026-08-19
tags: [UI, 声明式]
related: [RecyclerView]
---

# Jetpack Compose

## 概述
Android 官方的**声明式 UI 框架**:用 `@Composable` 函数描述界面「应该长什么样」,而不是命令式地一步步改 View。核心思想是 **UI = f(state)**——状态变了,框架自动**重组**(re-run 受影响的 Composable)刷新界面;靠 `remember`/`State` 在重组之间持有数据,靠**编译器插件**把 Composable 函数改写成可记忆、可重启的结构。相较传统 View 体系,少了 `findViewById` 与手动同步、天然状态驱动,但也带来**重组与稳定性**这些新的性能课题。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 声明式 UI 与重组

声明式描述「UI 该是什么样」,而不是「怎么一步步改 View」。核心等式 **UI = f(state)**:UI 由状态推导出来。**重组（recomposition）** 指当 Composable 读取的 `State` 改变时,框架重新执行该 Composable(或其一部分)刷新界面。

- **智能重组**:框架尽量只重组受影响的部分,而非整棵树。
- **可跳过（skippable）**:参数都没变时,整个 Composable 调用被跳过。
- **可重启（restartable）**:函数是一个独立的「重启作用域」,它订阅了自己读过的 State,State 变化只重启该作用域。
- **稳定性决定能否跳过**:只有「稳定」类型才能可靠判断「未变」从而跳过;不稳定类型(如 `List`、含 `var` 的类)会让 Composable 无法被跳过。
- **重组是乐观的（optimistic）**:状态在帧间反复变化时,正在进行的重组可能被取消重来。

### 2. @Composable 与编译器

`@Composable` 不是运行时注解,而是 **Compose Compiler（编译器插件）** 的标记。编译器对每个 Composable 函数做改写:

- 注入一个隐藏的 `Composer` 参数(加在参数列表最前);
- 基于**调用位置**做记忆（position-based memoization）——用位置槽记录上次输入与结果;
- 用 `startRestartGroup`/`endRestartGroup` 这类调用把函数体包成一个**重启作用域**。

正因为注入了 `Composer`,`@Composable` 函数只能在另一个 `@Composable`(或受控入口)里调用。这套改写是 Compose「粒度化重组」(按作用域重启、按参数跳过)的根基——不是重跑整棵树。

### 3. remember 与状态

- `remember { }`:在 Composition 里存一个值,跨重组保留(按调用位置记忆)。
- `mutableStateOf(value)`(常配合 `by`):返回 `State<T>`/`MutableState<T>`;被 Composable 读取时自动订阅,改它触发重组。
- `rememberSaveable`:在 `remember` 基础上,还能在**配置变更(旋转)和进程死亡**后恢复(底层走 Bundle / SavedState)。
- **状态提升（state hoisting）**:把状态上移、让子组件无状态(stateless)——子组件只接收值 + 回调,状态由父持有。好处:可复用、可预览、易测试。
- **单向数据流（UDF）**:状态向下流动、事件向上冒泡;Composable 读 State 渲染,用户操作触发回调去改 State。

```kotlin
// 有状态(stateful)→ 无状态(stateless)提升示例
@Composable
fun Counter() {
    var count by rememberSaveable { mutableStateOf(0) }   // 状态在父
    CounterButton(count = count, onIncrement = { count++ })  // 值向下,事件向上
}

@Composable
fun CounterButton(count: Int, onIncrement: () -> Unit) { /* 只读 count、回调 */ }
```

### 4. 副作用 (Side-effects)

Composable 函数体本身应**无副作用**(不直接做网络/写文件/订阅),副作用交给专用的 effect API,它们绑定 Composition 生命周期、按 key 控制重启:

| API | 作用 |
|-----|------|
| `LaunchedEffect(key)` | 进入组合时启动协程;key 变化时取消旧的、起新的;离开组合时取消 |
| `DisposableEffect(key)` | 进入/离开时做配对操作(如注册/反注册监听) |
| `rememberCoroutineScope()` | 拿一个绑定 Composition 的协程作用域,用于在回调里 `launch`(而非组合期间) |
| `SideEffect { }` | 每次成功重组后,把状态同步给非 Compose 对象 |
| `produceState` | 把非 Compose 数据源(Flow/回调)转成 `State` |

### 5. CompositionLocal

`CompositionLocal` 提供**隐式跨子树传值**:父用 `CompositionLocalProvider` 提供值,任意层后代用 `LocalXxx.current` 读取,无需层层透传参数。

- `staticCompositionLocalOf`:值几乎不变,优化成静态读(变化时影响整棵子树重组)。
- `compositionLocalOf`:值会变,读取处会订阅、精准重组。
- **慎用**:隐式依赖让组件难复用/难测;通常只留给主题(`LocalContentColor`、`LocalTextStyle`)这类真正全局的东西。

### 6. 组合三阶段与性能

Compose 渲染分三阶段,每阶段都能被独立跳过:

1. **Composition**:执行 Composable,产出描述 UI 的节点树(记在 Slot Table 里)。受 `State` 改变触发。
2. **Layout**:measure(测量)+ place(摆放)每个节点。
3. **Draw**:绘制到 Canvas。

性能要点(减少重组 / 缩小重组范围):

- **稳定类型**:用 `@Immutable`(绝不会变)/`@Stable`(可变但能判断是否变了)标注,让 Composable 可跳过。`List<T>` 是接口、实现可变 → 默认不稳定 → 用 `ImmutableList` 或 `@Immutable` 包装类。
- `derivedStateOf`:把频繁变化的若干 State 派生成「只有结果改变才触发重组」的 State(如「滚动超过阈值」这类阈值状态)。
- `key(...)`:在 `LazyColumn` 的 `items` 里给稳定 key,让增删/重排时能复用 item、状态不串位。
- **读 State 范围最小化**:把「读 State」限制在最小子组件,别让大组件因读了某个 State 整块重组。
- **别在组合里做重活**:网络/IO/重计算放进 effect 或 ViewModel。

### 7. 快照 (Snapshot) 系统

`State<T>` 的底层是 **Snapshot** 系统——一个全局、可订阅的响应式状态容器,这是 Compose 状态驱动重组的真正根基:

- 每次 `mutableStateOf` 的写都被记录;读被「当前快照」隔离——读到什么取决于你在哪个快照。
- `Snapshot.withMutableSnapshot { }`:把多个写合并成**一次通知**(批量),避免中间态触发多次重组。
- 支持多线程:可以开独立快照在别的线程读写状态再 `apply` 回去(`takeMutableSnapshot`)——这是 Compose 并发安全的依据。
- `mutableStateOf` 能驱动重组,本质是它在快照里注册了读写监听。

```kotlin
// 多次写合并成一次重组通知
Snapshot.withMutableSnapshot {
    state.a = 1
    state.b = 2   // 否则两次写可能各触发一次重组
}
```

### 8. 与 View 体系互操作

- **Compose 里嵌老 View**:`AndroidView(factory = { OldView(it) }, update = { it.prop = ... })`。
- **老 View 里嵌 Compose**:`ComposeView`(或 `AbstractComposeView`)。
- **生命周期/保存状态**:混用时需保证 `ViewTreeLifecycleOwner`/`ViewTreeSavedStateRegistryOwner` 等已绑定(`ComponentActivity`/新版入口通常已自动处理)。
- **主题**:`MaterialTheme` ↔ AppCompat/Material XML 主题,互嵌时颜色/形状需手动桥接。
- **性能**:`AndroidView` 有 inflate/测量开销,列表里大量混用会拖慢;能纯 Compose 就别混。

## 实践经验 / 踩坑

1. **状态没用 remember** —— Composable 里直接 `var x = 0` 或裸 `mutableStateOf(...)`(没 `remember`),重组时重置/丢失。要 `remember { mutableStateOf(...) }` 或 `var x by remember { mutableStateOf(0) }`。
2. **组合里做副作用** —— 在函数体里直接发网络/读文件/订阅,每次重组都触发。改用 `LaunchedEffect`/`produceState` 等。
3. **不稳定类型致整树重组** —— 参数是 `List<T>` 或含 `var` 的类,Composable 不可跳过,稍变就重组整子树。用 `@Immutable` 标注或换 `ImmutableList`。
4. **derivedStateOf 误用** —— 把高频变化的条件直接喂给会重组的组件 → 重组风暴;或忘了包成 State 导致每次重新求值。用它包「阈值类」派生状态。
5. **LazyColumn 忘 key** —— `items(list) { ... }` 没给 key,增删/重排时 item 被错误复用、状态串到别的项。用 `items(list, key = { it.id })`。
6. **读 State 范围太大** —— 大组件读了某个 State,整个大组件跟着重组。把读 State 的部分抽成小 Composable。
7. **rememberSaveable 漏存** —— 只用 `remember` 存了 UI 状态(滚动位置/输入),旋转或进程恢复后丢失。要恢复的改用 `rememberSaveable`。

## 待深入 / 下一步
- [ ] 在小项目里用 Compose 重写一个页面
- [ ] 读 Compose 编译器产物:看 `Composer` 注入与重启作用域的实际改写
- [ ] 读 Snapshot 系统:`mutableStateOf` / `SnapshotKt` 实现
- [ ] 自定义 Layout(`Layout` / `MeasurePolicy`)
- [ ] 性能工具:Layout Inspector 的重组计数

## 参考资料
- Compose 核心思想:https://developer.android.com/jetpack/compose/mental-model
- 状态与重组:https://developer.android.com/jetpack/compose/state
- 副作用:https://developer.android.com/jetpack/compose/side-effects
- 性能:https://developer.android.com/jetpack/compose/performance
- 源码类:`Composer`、`Snapshot`、`SnapshotStateKt`、`CompositionLocal`