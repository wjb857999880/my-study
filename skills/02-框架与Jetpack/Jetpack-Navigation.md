---
title: Jetpack Navigation
domain: 02-框架与Jetpack
level: 精通
target: 精通
importance: 中
last_assessed: 2026-08-26
last_reviewed: 2026-08-26
next_review: 2027-02-22
tags: [Navigation, 路由, Jetpack]
related: [Jetpack Compose, 组件化与模块化]
---

# Jetpack Navigation

## 概述
Jetpack 的导航框架,统一管理页面(目的地)间的跳转与参数传递:**Navigation Component**(XML / Fragment 版)与 **Navigation Compose**(Compose 版)。核心:NavGraph 定义目的地与路径、**safe args** 类型安全传参、深链接、底部导航 / 抽屉集成、返回栈管理。价值:替代手写 Fragment 事务与 Intent 跳转的样板,跳转逻辑集中、可测、与 Compose / 组件化路由配合。

## 考核记录
- **2026-08-26** 判定：(待考核) → 精通 ✅ ｜ 考官：AI
  - 表现：四档全部稳过——了解档 Navigation 根本问题(声明式图模型替代命令式 FragmentTransaction)+ 三件套职责 + `rememberNavController()` 四根因(state save / 生命周期 / ViewModelStoreOwner 作用域 / 单例语义)讲清;熟悉档 Compose 底部导航教科书级(`hierarchy.any{}` 判选中 + popUpTo/saveState/restoreState/launchSingleTop 四件套 + 三需求对应关系);掌握档 #1 三坑全抓(login 不清栈 / 用 rootNav 跳当前目的地重复压栈 / innerNav 跳不到 rootNav 注册的 detail + callback 替代 NavController 下漏的架构建议),#2 未登录拦截架构(Parcelize PendingDestination + SavedStateHandle.getStateFlow + consume 原子读写 + AuthGuard vs OnDestinationChangedListener 取舍);精通档四问全透(Navigation 3.x 四步内部机制 / DeepLink + KSerializer 编译产物无反射但有运行时 / NavBackStackEntry 四接口 + 父 entry 共享 VM 必须显式传 parentEntry / STARTED 而非 RESUMED 监听因 onSaveInstanceState 在 STARTED→CREATED 窗口)。
  - 依据：精通档要求"架构 + 原理 + 性能权衡 + 讲透",全部达标。首次考核直接到 target(精通)。

## 核心原理 / 关键点

### 1. 导航框架的定位与组成
Jetpack Navigation 用一张**导航图(NavGraph)** 描述「目的地(Destination)」与它们之间的路径,由 **NavController** 驱动跳转、管理返回栈。核心三件套:`NavController`(状态机,持有返回栈)、`NavHost`(容器,渲染当前目的地)、`NavGraph`(目的地与连线的声明)。

### 2. Fragment 版 vs Compose 版
- **Navigation Component**(XML / Fragment):`NavHostFragment` 承载,目的地是 Fragment,跳转即 Fragment 事务。
- **Navigation Compose**:目的地是 Composable:

```kotlin
val nav = rememberNavController()
NavHost(nav, startDestination = "home") {
    composable("home") { Home(onClick = { nav.navigate("detail/$id") }) }
    composable("detail/{id}") { backStackEntry ->
        Detail(backStackEntry.arguments?.getString("id"))
    }
}
```

两者概念一致,差别只在目的地是 Fragment 还是 Composable。

### 3. 目的地(Destination)与路由(route)
每个目的地由**路由字符串(route)** 标识(如 `"detail/{id}"`)。`navigate("route")` 入栈、`popBackStack()` 出栈。路由可带参数占位符。

### 4. 类型安全传参:Safe Args / NavType
- **Fragment 版**:用 Safe Args Gradle 插件生成类型安全的 Directions / Args 类,避免手拼字符串 key。
- **Compose 版**:`navArgument` + `NavType` 声明参数类型,`backStackEntry.arguments?.getString("id")` 取值。新版还支持用 Kotlin Serialization 做类型安全路由。
传大数据不要塞参数(Binder / URL 限制),用共享 ViewModel 或 Repository,只传 id。

### 5. 底部导航 / 抽屉与返回栈管理
底部导航的 tab 切换常配合 `popUpTo(startDestination) { saveState = true }` + `restoreState = true`,实现「切回 tab 恢复状态、不堆积重复目的地」。返回栈语义:`popUpTo`(弹到某目的地)、`launchSingleTop`(避免重复栈顶)。

### 6. 深链接(Deep Link)与隐式跳转
支持 App Link / URI 深链接:在目的地声明 `<deepLink>`(XML)或 `composable(..., deepLinks = ...)`(Compose),外部 URI 命中即可直达该页。用于推送点击、网页跳 App、分享回流。

### 7. 嵌套导航图与模块化
导航图可**嵌套**(navigation 节点),按业务模块拆分;多模块工程里每模块提供自己的 NavGraph(include),实现按模块化的导航组织。

### 8. 与组件化路由的配合 / 选型
大型项目常用**组件化路由**(如 ARouter / WMRouter)解耦模块间跳转。Jetpack Navigation 更偏「单 App 内、有图」的集中式导航;二者可结合(模块内用 Navigation,跨模块用 ARouter)。选型看团队架构。

## 实践经验 / 踩坑

1. **ViewModel scope 绑 NavBackStackEntry**:目的地级 ViewModel 绑当前 entry,离开即清理;跨目的地共享数据用父图(parent graph)entry 的 ViewModel。
2. **返回栈膨胀**:循环 navigate 不处理会堆叠大量 entry;用 `popUpTo` + `launchSingleTop` 控制。
3. **Compose NavController 位置**:`rememberNavController()` 要放在 Composable 层级合适位置(通常 Scaffold 顶层),位置不当会丢返回栈状态。
4. **参数传大对象**:Parcelable 序列化有大小限制,大数据走共享 ViewModel / Repository,只传 id。
5. **状态保存**:NavController 自动保存返回栈;UI 自定义状态用 `rememberSaveable`,ViewModel 用 SavedStateHandle。

## 待深入 / 下一步
- [ ] Navigation 3.x / 类型安全路由(Kotlin Serialization)
- [ ] 多模块 NavGraph 的 include 与按需加载
- [ ] Hilt `hiltViewModel()` 在导航中的作用域
- [ ] 与组件化路由(ARouter)的取舍

## 四档考核 Q&A（2026-08-26）

### 了解档
**Q1: 用一句话讲 Jetpack Navigation 的根本问题、三件核心组件、Fragment 版 vs Compose 版差别 + `rememberNavController()` 为何不能手动持有。**

A1:
① **根本问题**：把 Android 上散落在 `Intent / FragmentTransaction / startActivity / 手动 back stack` 这些「各自为政」的导航手段，统一成一张**可声明、可可视化、可推理的单向图模型**——节点是 destination，边是 action，让「我从哪来 / 现在在哪 / 怎么回去」不再依赖人脑维护状态。
② **三件套**：

| 组件 | 职责 | 角色 |
|---|---|---|
| `NavController` | 驱动跳转、管 back stack、暴露 `currentDestination` | 司机 + 路线调度 |
| `NavHost`（Fragment 版叫 `NavHostFragment`） | 把当前 destination 渲染到屏幕 | 车厢 / 舞台 |
| `NavGraph` | 声明 destination + action 连线 + 参数 + deep link | 地图 / 路网定义 |

③ Fragment 版围绕 **XML 资源 + Fragment 事务 + `@IdRes int`** 建模；Compose 版围绕**字符串 route + Composable 函数**建模——destination 类型不同（`Fragment` vs `@Composable`），Graph 声明不同（XML vs Kotlin DSL），参数传递不同（Bundle+SafeArgs vs 路径字符串）。
④ `rememberNavController()` 不能换成 `val nav = NavController(LocalContext.current)`，因为它做了四件手动持有做不到的事：**rememberSaveable 保存 back stack**、**与 LifecycleOwner 联动**、**绑定正确的 ViewModelStoreOwner（支持嵌套图）**、**与 NavHost 共享同一个 NavHostController 实例**。任一缺失都会导致「navigate 了但屏幕没切」或「旋转后回到 startDestination」。

---

### 熟悉档
**Q: Compose 底部导航 `Scaffold + NavigationBar + 3 tab(Home/Search/Profile)`,写出 `MainScreen` 骨架 + `navigate()` 调用,要求 ① 不回 startDestination ② 每 tab 独立返回栈 ③ 同 tab 重复点不出重复栈顶。**

A:

```kotlin
@Composable
fun MainScreen(navController: NavHostController = rememberNavController()) {
    Scaffold(bottomBar = { BottomBar(navController) }) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = "home",
            modifier = Modifier.padding(innerPadding)
        ) {
            composable("home")    { HomeScreen() }
            composable("search")  { SearchScreen() }
            composable("profile") { ProfileScreen() }
        }
    }
}

@Composable
private fun BottomBar(navController: NavHostController) {
    val backStackEntry by navController.currentBackStackEntryAsState()
    NavigationBar {
        tabs.forEach { tab ->
            // 用 hierarchy.any{} 穿透子 destination —— 进 home/detail 后底栏 Home 仍亮
            val selected = backStackEntry?.destination?.hierarchy
                ?.any { it.route == tab.route } == true

            NavigationBarItem(
                selected = selected,
                onClick = {
                    navController.navigate(tab.route) {
                        popUpTo(navController.graph.findStartDestination().id) {
                            saveState = true   // 切走时把当前 tab 子栈状态存住
                        }
                        launchSingleTop = true    // 同 tab 重复点不复压
                        restoreState = true       // 切回时还原上次的子栈
                    }
                },
                icon  = { Icon(tab.icon, contentDescription = tab.label) },
                label = { Text(tab.label) }
            )
        }
    }
}
```

| 需求 | 由哪行解决 | 机制 |
|---|---|---|
| ① 切 tab 不回 startDestination | `popUpTo(startDestination) { saveState = true }` | 弹栈但保留状态；栈顶是新 tab，`startDestination` 仍在栈 |
| ② 每 tab 独立返回栈 | `saveState + restoreState = true` | 切走时 Serialize 整个子栈，切回时反序列化复原 |
| ③ 同 tab 重复点不出重复栈顶 | `launchSingleTop = true` | 目标已在栈顶则复用，不 push 新 entry |

`startDestination` 选 `"home"`：它是用户每次启动的自然落地页（消费型主界面）；另外让 `popUpTo(startDestination)` 的「弹回起点」和「切回入口」是同一动作，逻辑干净。**业务上的「未登录跳 Login」应该在 `startDestination` 之外独立做路由层拦截，不要把 `startDestination` 改成 `login`**。

---

### 掌握档 · 排障
**Q: 以下代码有三处 Navigation 坑(login → home 不清栈 / BottomBar 用 rootNav + selected=true / innerNav 跳 detail)。逐一指出 + 修复。**

A:

**坑 A：`nav.navigate("home")` 没清栈。**

- 现象：登录后栈变成 `splash → login → home`，按返回键又回 login 页（用户已登录却能「退出登录」，是常见线上 UX bug）。
- 修复：
  ```kotlin
  nav.navigate("home") {
      popUpTo("login") { inclusive = true }   // 把 login 弹出
  }
  ```
  想更彻底可 `popUpTo("splash") { inclusive = true }`，让 home 成为栈底，back 直接退出 App。

**坑 B：`HomeTabScreen` 里 BottomBar 用 rootNav 跳当前目的地 + `selected = true` 硬编码。**

- 现象：① 在 root 的 home 上再 `navigate("home")` 默认会再压一份 → root stack 出现 `… → home → home`，back 看似不响应；② `selected = true` 写死体验全废；③ 没有 `popUpTo + saveState + restoreState`，子 tab 切走切回会丢状态。
- 修复：用 `innerNav` 驱动 + 动态 selected + tab 四件套：
  ```kotlin
  NavigationBarItem(
      selected = innerBackStackEntry?.destination?.route == "feed",
      onClick = {
          innerNav.navigate("feed") {
              popUpTo(innerNav.graph.findStartDestination().id) { saveState = true }
              launchSingleTop = true
              restoreState = true
          }
      },
      …
  )
  ```

**坑 C：`innerNav.navigate("detail/$id")` —— inner 图里没注册 detail。**

- 现象：直接抛 `IllegalArgumentException: Navigation destination "detail/{id}" is unknown to this NavController`。
- 修复：用 rootNav（detail 是注册在 root NavGraph 上的）。**架构上推荐把跳转封装成 callback 往下传，不要把 NavController 漏给叶子 Composable**：
  ```kotlin
  composable("home") {
      HomeTabScreen(onItemClick = { id -> nav.navigate("detail/$id") })
  }

  @Composable
  fun HomeTabScreen(onItemClick: (Int) -> Unit) {
      val innerNav = rememberNavController()
      NavHost(innerNav, startDestination = "feed") {
          composable("feed") { FeedScreen(onItemClick = onItemClick) }
      }
  }
  ```
  这样 `FeedScreen` 不知道 NavController 的存在，只调一个 lambda；叶子没有「该往哪跳」的决定权，避免内/外层串调带来「跳错图」或「栈污染」。

**回到架构硬规则**：每个 `NavController` 只认识注册到自己 NavHost 的 destination。父能读子的图吗？——不能；子能读父的图吗？——能（往回调就行）这点和 Hilt 的作用域父子规则正好形成镜像。

---

### 掌握档 · 未登录拦截
**Q: 实现未登录拦截 + 登录成功后回原目标 + 主动退出登录回 home。**

A:

**1. 关键数据结构 + 存储**

```kotlin
@Parcelize
data class PendingDestination(
    val route: String,                      // 已解析的路由,如 "article/42"
    val args: Bundle = Bundle(),            // 非路径参数(Boolean / Parcelable / 等)
    val fallback: String = "home"           // 登录取消/失败时回这里
) : Parcelable

@HiltViewModel
class AuthNavigationViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    // 用 SavedStateHandle.getStateFlow:进程被杀也能恢复
    val pending: StateFlow<PendingDestination?> =
        savedStateHandle.getStateFlow("pending", null)

    fun save(p: PendingDestination) { savedStateHandle["pending"] = p }

    /** 读 + 清,原子操作 —— 防止下次登录再消费一次 */
    fun consume(): PendingDestination? {
        val current = savedStateHandle.get<PendingDestination>("pending")
        savedStateHandle.remove<PendingDestination>("pending")
        return current
    }
}
```

存到 Activity 级 shared ViewModel 的 SavedStateHandle，跨配置变更存活、跨 NavHost 边界可访问。

**2. `navigateWithAuth` 拦截函数**

```kotlin
class AuthNavigator @Inject constructor(
    private val authRepository: AuthRepository,
    private val pendingStore: AuthNavigationViewModel,
) {
    fun NavController.navigateWithAuth(
        target: NavTarget,
        fallbackRoute: String = "home"
    ) {
        if (authRepository.isAuthenticated()) {
            navigate(target.route)                              // 已登录:直跳
        } else {
            pendingStore.save(PendingDestination(target.route, target.args, fallbackRoute))
            navigate("login") {
                popUpTo(graph.findStartDestination().id) { inclusive = true }
            }
        }
    }
}
```

**3. 登录成功 / 取消后的取出 + 跳转 + 清掉**

```kotlin
LaunchedEffect(loginState) {
    when (loginState) {
        is LoginState.Success -> {
            val pending = pendingStore.consume()                // ① 读 + 清(原子)
            val route = pending?.route ?: pending?.fallback ?: "home"
            navController.navigate(route) {
                popUpTo("login") { inclusive = true }            // ② 清掉 login 栈
            }
        }
        is LoginState.Cancelled -> {
            val pending = pendingStore.consume()
            navController.navigate(pending?.fallback ?: "home") {
                popUpTo("login") { inclusive = true }
            }
        }
        else -> Unit
    }
}
```

关键防漏点：`consume()` 内部已经把 SavedStateHandle 里的 key 删掉，下次登录不会读到上一次的残留目标。

**4. `NavTarget` 数据类设计**

```kotlin
@Parcelize
data class NavTarget(
    val route: String,
    val args: Bundle = Bundle()
) : Parcelable {
    companion object {
        fun article(id: Int) = NavTarget(route = "article/$id")           // 路径参数已编进 route
        fun profile(userId: String, isAdmin: Boolean) = NavTarget(
            route = "profile",
            args = bundleOf("userId" to userId, "isAdmin" to isAdmin)
        )
        fun search(query: String, sort: SortOrder) = NavTarget(
            route = "search?query=$query",
            args = bundleOf("sort" to sort)                               // SortOrder 需 @Parcelize
        )
    }
}
```

Bundle 支持：基本类型 / String / Parcelable / Serializable / ArrayList<Parcelable> / 加了 `@Parcelize` 的自定义类。普通 Kotlin Object 不行——必须 `Parcelable` 或 `Serializable`。

**5. 拦截挂载点（两种方案对比）**

```kotlin
// 方案 A:NavController 监听 destination 变化
NavController.addOnDestinationChangedListener { controller, destination, args ->
    val needsAuth = destination.route in authRequiredRoutes
    if (needsAuth && !authRepository.isAuthenticated()) {
        controller.navigateWithAuth(
            NavTarget(destination.route ?: "", args ?: Bundle()),
            fallbackRoute = "home"
        )
    }
}

// 方案 B:AuthGuard Composable 包住需要鉴权的目的地（推荐）
composable<ArticleRoute> { entry ->
    AuthGuard(target = NavTarget.from(entry)) {
        DetailScreen(id = entry.toRoute<ArticleRoute>().id)
    }
}
```

A 侵入性小但要小心「已经在 article 页 → 深链到 article 时重复触发」。生产里更推荐 B：在每个需要鉴权的目的地 Composable 顶层套一个 `AuthGuard`，渲染时才决定下一步，职责清晰。

---

### 精通档
**Q1: Compose Navigation 3.x 类型安全路由怎么用 `@Serializable data class` 当 route 入口？`navigate(route)` 内部怎么序列化 / 反序列化？**

A1:

```kotlin
@Serializable
data class ArticleRoute(val id: Int)

NavHost(nav, startDestination = ArticleRoute(0)) {
    composable<ArticleRoute> { entry ->
        val route: ArticleRoute = entry.toRoute()         // 反序列化产物
    }
}
nav.navigate(ArticleRoute(id = 42))                      // 序列化入口
```

四步内部：

| 步骤 | 关键 API | 干了什么 |
|---|---|---|
| ① 生成 serializer | `kotlinx-serialization` 编译器插件 | 给 `ArticleRoute` 生成 `KSerializer<ArticleRoute>`，描述字段名 / id / 顺序 |
| ② 注册目的地 | `composable<T>(reified)` | 用 `serializer<T>().descriptor` 算出**稳定的 destinationId**（基于 descriptor hash），挂进 NavGraph；按字段类型生成对应 `NavType`（Int → IntType, String → StringType, …） |
| ③ `navigate(route)` | `NavController.navigate<T>(route)` | 调 `serializer<T>()` → `encodeToXxx` → 把 `ArticleRoute(42)` 序列化成结构化表示（路径参数 → URL 段，查询参数 → querystring，复杂对象 → JSON 串），存进 `NavBackStackEntry.arguments`（本质 Bundle） |
| ④ `entry.toRoute<T>()` | `NavBackStackEntry.toRoute<T>` | 用 `serializer<T>()` 反序列化 arguments Bundle 回 `ArticleRoute` 实例，强类型返回 |

边界：类型必须 `@Serializable`（缺插件编不过 `composable<T>`）；同一个 T 多次 `composable<T>` 是同一个 destination（这就是类型安全路由能跟 deep link 严格一一对应的根因）；序列化产物走 Bundle，跨配置变更 / 进程死亡都能活下来。

---

**Q2: Deep Link `https://my.app/article/42` 落到 NavHost 时框架如何把 URI 解析回 `ArticleRoute(42)`？运行时是否引入反射？**

A2:

```kotlin
composable<ArticleRoute>(
    deepLinks = listOf(navDeepLink<ArticleRoute>(basePath = "https://my.app"))
)
```

匹配流程：`URI → NavDeepLink 匹配（basePath + path 占位符）→ 抽出 {id} = "42"（仍是 String）→ NavType.tryParse("42") = 42 → serializer<ArticleRoute>().decodeFromArgs(...) → ArticleRoute(id = 42) → entry.toRoute<ArticleRoute>() → Destination 渲染`。

- `@SerialName` 是路径字段名 ↔ URI 占位符的桥梁；改了 `@SerialName`，deep link 的 `uriPattern` 也得跟着改。
- `navDeepLink<T>(basePath)` 由 Navigation 根据 `KSerializer.descriptor` **自动推出 URI 模板**——字段顺序、是否必填、嵌套对象都会被映射成 path / query 段。
- 运行时引入了 kotlinx-serialization 吗？**是**。`NavDeepLink` 命中后反序列化构造对象需要 `KSerializer`，这是 `kotlinx.serialization` 的产物（运行时调用 `serializer.decode...`）。但**没有反射**：serializer 是编译期生成的 `$serializer` 对象，运行时只是普通方法调用，效率与传统 Bundle 同一量级。

边界：可空 / 默认值字段 → URL 缺该字段时反序列化用默认 / null，不崩；嵌套对象 → 走 JSON 序列化，URL 太长时自动转 query 或 base64（实现细节）。

---

**Q3: 导航到 `article/42` 时，`hiltViewModel<ArticleViewModel>()` 与 `NavBackStackEntry` 生命周期怎么绑定？为什么「从 article 想共享父图的某个 VM」必须写成 `hiltViewModel(parentEntry)`？**

A3:

`NavBackStackEntry` 同时实现四件 owner：

```kotlin
NavBackStackEntry : ViewModelStoreOwner,
                     LifecycleOwner,
                     SavedStateRegistryOwner,
                     HasDefaultViewModelProviderFactory
```

导航进 `ArticleRoute(42)` 时框架为它 new 一个 `NavBackStackEntry`，entry 自带**独立的** ViewModelStore / Lifecycle / SavedStateRegistry / SavedStateHandle。

`hiltViewModel<T>()` 三步：

1. 取 `LocalViewModelStoreOwner.current`——在 `composable<ArticleRoute>` 作用域里，这正是当前 entry；
2. 用这个 entry 的 ViewModelStore 去 `HiltViewModelFactory` 拿 T——命中 → 返回已有实例，未命中 → 用 Hilt 生成新实例塞进该 entry 的 store；
3. 生命周期：entry pop 出去 → `ViewModelStore.clear()` → `VM.onCleared()`。

**VM 与 entry 同生共死**——这就是「按目的地隔离 ViewModel 状态」的根本机制。

共享父图 VM 必须显式传 `parentEntry`，因为**默认 `hiltViewModel()` 取的是当前 entry 的 ViewModelStore**：

```kotlin
composable<ArticleRoute> { entry ->
    val parentEntry = remember(entry) { nav.getBackStackEntry(parentRoute) }
    val parentVM: ParentVM = hiltViewModel(parentEntry)   // ✅ 拿父作用域的 VM

    // ❌ val wrong = hiltViewModel()  // 用当前 entry 的 store,会新建一份,和父目的地的 ParentVM 不是同一个对象
}
```

不传 `parentEntry` 会出问题：要么 `Hilt` 在当前 entry 的 store 里 new 一份新的 `ParentVM`（和父目的地的不是同一对象，状态串台）；要么报「no parent」错误（如果父 entry 从未进入过）。**「NavBackStackEntry 就是 VM 的家，`hiltViewModel` 默认住在当前 entry 家，想共享父 VM 必须把钥匙（父 entry）递过去。」**

---

**Q4: `rememberNavController()` 在配置变更（旋转）和进程被杀重启两种场景下如何恢复返回栈 + 各目的地的 SavedStateHandle？为什么用 `Lifecycle.State.STARTED` 监听而不是 `RESUMED`？**

A4:

两层 Saver 协同：

1. `rememberNavController()` 内部用 `rememberSaveable` 包了 `NavHostController` 的创建；
2. 提供 `NavControllerSaver`，负责把 back stack 序列化 / 反序列化；
3. back stack 里每个 entry 自带 SavedStateHandle（也是 Saver 化的）。

| 场景 | 谁留住了状态 | 恢复路径 |
|---|---|---|
| 配置变更（旋转） | NavController 关联的 `NavControllerViewModel`（被 Activity 的 `ViewModelStore` 持有） | Activity.getViewModelStore() 不销毁 → VM 不死 → `NavControllerViewModel` 不死 → back stack 不动 → 各 entry 的 SavedStateHandle 都在 |
| 进程被杀重启 | Activity 的 `onSaveInstanceState(Bundle)`（由系统托管） | Saver 在 `onSaveInstanceState` 时被调用 → 把 back stack（各 entry 的 route + arguments Bundle + SavedStateHandle）写进 Bundle → 系统杀进程 → 重启时 `SavedStateRegistry` 取出 Bundle → 反向走一遍 Saver → 各 entry 通过同一个 destinationId 找回原 typed route |

**为什么 typed route 在进程死亡后还能还原**：route 类型 → 序列化进 Bundle 的只是「参数键值对」；恢复时 NavGraph 里仍注册着那个 destinationId 对应的 `composable<T>`，`entry.toRoute<T>()` 用同一份 `KSerializer` 反序列化出来。只要 `composable<T>` 的 T 没有改结构，Bundle 跨进程死亡就是无损的。

**为什么监听 STARTED 而不是 RESUMED**：

Lifecycle 走向：`RESUMED → STARTED → CREATED → STOPPED`，`onSaveInstanceState` 在 `STARTED → CREATED` 期间被调。

Navigation 内部的 `NavControllerViewModel` / `Saver` 必须在 `onSaveInstanceState` 触发时还活着、还能写 Bundle：

- **如果观察 `RESUMED`**：`RESUMED → STARTED` 时 Navigation 的 observer 已被移出 → 到 `onSaveInstanceState` 调用时 Saver 已被注销，back stack 状态就漏到 Bundle 外了。
- **如果观察 `STARTED`**：`STARTED → CREATED` 这条边仍然触发 observer → Saver 在 `onSaveInstanceState` 触发时还有效 → back stack 顺利写进 Bundle → 系统杀进程后能恢复。

一句话：**`RESUMED` 太晚**——Saver 已经被 GC 路径踢掉了；`STARTED` 刚好覆盖到 `onSaveInstanceState` 触发的窗口期。这也是为什么 Compose 里 `rememberSaveable` 内部的生命周期订阅默认都用 `STARTED` 当下界，跟 Navigation 是同一个考量。

## 参考资料
- Navigation 概览:https://developer.android.com/guide/navigation
- Navigation Compose:https://developer.android.com/guide/navigation/navigation-compose
- 传参与 Safe Args:https://developer.android.com/guide/navigation/navigation-pass-data