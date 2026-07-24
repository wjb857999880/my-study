---
title: Hilt 依赖注入
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [Hilt, DI, Dagger]
related: [MVVM, 移动端架构设计]
---

# Hilt 依赖注入

## 概述
依赖注入(DI)把对象的创建与使用解耦,便于测试与降低耦合。**Hilt 基于 Dagger**、针对 Android 简化:用 `@HiltAndroidApp` + `@AndroidEntryPoint` + `@Inject`/`@Module`/`@Provides` 声明依赖,编译期自动生成装配代码。常见:注入 Repository / ViewModel / Retrofit,替换实现做单元测试。需理解作用域(`@Singleton` / `@ActivityScoped` 等)与组件层次。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 什么是 DI / 为什么需要

依赖注入(DI)= 把对象的**依赖(它需要的其他对象)由外部提供**,而非自己 new。好处:① 解耦(类不绑死具体实现);② 可测试(测试时注入 mock);③ 集中管理创建与生命周期。Android 里典型:ViewModel 依赖 Repository,Repository 依赖 Retrofit / Room——手动 new 会层层耦合。

### 2. Dagger → Hilt 的简化

**Dagger** 是 Java/Android 上性能最好的 DI(编译期生成代码、无反射),但样板代码多(手写 Component / 工厂)。**Hilt** 基于 Dagger、针对 Android 预置了一套标准组件与生命周期,把 Application / Activity / Fragment 等的注入自动化,大幅减少样板,是 Google 官方推荐。

### 3. 核心注解

- `@HiltAndroidApp`:标在 Application,触发 Hilt 代码生成,生成全局 Application Component。
- `@AndroidEntryPoint`:标在要注入的 Activity / Fragment / View / Service,生成注入入口。
- `@Inject`:① 构造函数 `@Inject` 让 Hilt 知道怎么创建这个类;② 字段 `@Inject` 声明要注入的依赖。
- `@Module` + `@InstallIn`:模块(提供「Hilt 不会自己 new 的依赖」,如三方库对象),`@InstallIn(SingletonComponent::class)` 指定装到哪个组件。
- `@Provides` / `@Binds`:在 Module 里提供依赖。

### 4. 注入入口

Hilt 内置支持 `@AndroidEntryPoint` 的类:Activity、Fragment、View、Service、BroadcastReceiver,以及 `@HiltViewModel` 的 ViewModel。对这些类,用 `@Inject lateinit var` 注入字段即可。

### 5. 预定义组件与作用域

Hilt 预定义组件对应 Android 生命周期,每个组件有匹配的作用域注解:

| 组件 | 作用域 | 生命周期 |
|---|---|---|
| SingletonComponent | @Singleton | App 全局 |
| ActivityComponent | @ActivityScoped | 一个 Activity |
| ViewModelComponent | @ViewModelScoped | 一个 ViewModel |
| FragmentComponent / ViewComponent / ServiceComponent | 对应 Scoped | 对应生命周期 |

作用域决定实例复用范围:`@Singleton` 全局单例,`@ActivityScoped` 每个 Activity 一个。

### 6. @Provides vs @Binds

- `@Provides`(在 `@Module` 的方法):**提供**一个依赖,方法体里构造 / 配置返回。适合三方库对象、需配置的依赖(如 `Retrofit`、`OkHttpClient`)。
- `@Binds`(抽象方法):**绑定**接口到实现,无方法体,告诉 Hilt「遇到这个接口就用这个实现」。更轻量,用于「接口 → 实现」。

### 7. 多实现:@Qualifier / @Named

同一接口有多个实现时,Hilt 无法区分 → 用限定符:`@Qualifier` 自定义注解或内置 `@Named("xxx")` 标注,注入时也带上对应限定符。

### 8. 测试价值

DI 最大收益之一是可测:测试时用替换 `@Module`(把真实现换成 mock),或在测试里构造被测类时直接传 mock 依赖,从而脱离网络 / DB 测业务逻辑。

## 实践经验 / 踩坑

1. **忘 `@HiltAndroidApp`** —— Application 没标,`@AndroidEntryPoint` 注入不生效;Application 类必须加。
2. **可注入类的构造函数要 `@Inject`** —— 否则 Hilt 不知如何创建;或用 `@Module` + `@Provides` 提供。
3. **作用域用错** —— 想「每个 Activity 一个实例」却用 `@Singleton`(全局共享),状态串了;按生命周期选作用域。
4. **接口多实现没限定符** —— 编译报「multiple bindings」;用 `@Named` / `@Qualifier` 区分。
5. **注入三方对象没写 @Module** —— Hilt 不会自己 new 三方库;必须 `@Provides` 提供。
6. **ViewModel 注入写错** —— ViewModel 用 `@HiltViewModel` + 构造函数 `@Inject`,而非字段注入。
7. **误以为 Hilt 用反射慢** —— Hilt / Dagger 是编译期生成代码、运行期无反射,性能不是问题。

## 待深入 / 下一步

- [ ] 实战 Hilt 多 module 注入 ViewModel / Repository / 网络层
- [ ] 理解 Component 层次与作用域传递
- [ ] 用 Hilt 替换 mock 做单元测试

## 参考资料

- Hilt 指南:https://developer.android.com/training/dependency-injection/hilt-android
- Dagger:https://dagger.dev/
- Hilt 与 ViewModel:https://developer.android.com/training/dependency-injection/hilt-jetpack
