---
title: Jetpack Navigation
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-11-13
tags: [Navigation, 路由, Jetpack]
related: [Jetpack Compose, 组件化与模块化]
---

# Jetpack Navigation

## 概述
Jetpack 的导航框架,统一管理页面(目的地)间的跳转与参数传递:**Navigation Component**(XML / Fragment 版)与 **Navigation Compose**(Compose 版)。核心:NavGraph 定义目的地与路径、**safe args** 类型安全传参、深链接、底部导航 / 抽屉集成、返回栈管理。价值:替代手写 Fragment 事务与 Intent 跳转的样板,跳转逻辑集中、可测、与 Compose / 组件化路由配合。

## 考核记录
（尚未考核）

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

## 参考资料
- Navigation 概览:https://developer.android.com/guide/navigation
- Navigation Compose:https://developer.android.com/guide/navigation/navigation-compose
- 传参与 Safe Args:https://developer.android.com/guide/navigation/navigation-pass-data