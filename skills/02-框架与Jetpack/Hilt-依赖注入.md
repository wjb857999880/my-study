---
title: Hilt 依赖注入
domain: 02-框架与Jetpack
level: 了解
target: 精通
importance: 中
last_assessed: 2026-07-29
last_reviewed: 2026-07-29
next_review: 2026-11-11
tags: [Hilt, DI, Dagger]
related: [MVVM, 移动端架构设计]
---

# Hilt 依赖注入

## 概述
依赖注入(DI)把对象的创建与使用解耦,便于测试与降低耦合。**Hilt 基于 Dagger**、针对 Android 简化:用 `@HiltAndroidApp` + `@AndroidEntryPoint` + `@Inject`/`@Module`/`@Provides` 声明依赖,编译期自动生成装配代码。常见:注入 Repository / ViewModel / Retrofit,替换实现做单元测试。需理解作用域(`@Singleton` / `@ActivityScoped` 等)与组件层次。

## 考核记录
- **2026-07-29** 判定：(待考核) → 了解 ✅ ｜ 考官：AI
  - 表现：了解档概念扎实(DI 解耦/可测、Hilt=Dagger 的 Android 封装、`@HiltAndroidApp`/`@AndroidEntryPoint`/`@Inject`/`@Module`/`@Provides` 五个核心注解职责基本讲对)。熟悉档未达——最小骨架(Application/Module/Repository/Activity)与 ViewModel 注入(`@HiltViewModel` + `by viewModels()`)两题均答「不会」,无法写出可行用法。
  - 依据：了解档稳过;熟悉档要求「照写出可行用法」,两题均未写出,故持平了解。差 1 档到 target(熟悉)。已把这两题答案补入 §9 作学习材料。

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

### 9. 完整示例：最小骨架 + ViewModel 注入

**场景 A：搭一个能跑的最小 Hilt 骨架**（Application → Module 提供 Retrofit → Repository 构造注入 → Activity 字段注入）。

① Application——触发 Hilt 代码生成的全局入口,并在 `AndroidManifest.xml` 里配 `android:name=".App"`：

```kotlin
@HiltAndroidApp
class App : Application()
```

② Module 提供 `Retrofit` / `Api`——`@InstallIn(SingletonComponent::class)` 装到全局组件,`@Provides` 告诉 Hilt「这个依赖怎么造」,方法的入参也会被 Hilt 自动注入：

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides @Singleton
    fun provideRetrofit(): Retrofit = Retrofit.Builder()
        .baseUrl("https://api.example.com/")
        .build()

    @Provides
    fun provideApi(retrofit: Retrofit): Api = retrofit.create(Api::class.java)
}
```

③ Repository——构造函数 `@Inject`,Hilt 自动把 `Api` 注进来：

```kotlin
class UserRepository @Inject constructor(
    private val api: Api
) {
    suspend fun getUser(id: Int) = api.getUser(id)
}
```

④ Activity——`@AndroidEntryPoint` + `@Inject lateinit var` 字段注入：

```kotlin
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    @Inject lateinit var repo: UserRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // repo 已注入,直接用
    }
}
```

**场景 B：ViewModel 注入**——`@HiltViewModel` + 构造函数 `@Inject`（注意是**构造注入**、不是字段注入），Activity 用 `by viewModels()` 拿：

```kotlin
@HiltViewModel
class UserViewModel @Inject constructor(
    private val repo: UserRepository
) : ViewModel() { /* ... */ }

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    private val vm: UserViewModel by viewModels()   // Hilt 自动提供工厂构造 VM
}
```

> `by viewModels()` 来自 `activity-ktx`（Fragment 用 `fragment-ktx`）；标了 `@HiltViewModel` 后 Hilt 会自动替换默认 `ViewModelProvider.Factory`，无需手写工厂。

## 实践经验 / 踩坑

1. **忘 `@HiltAndroidApp`** —— Application 没标,`@AndroidEntryPoint` 注入不生效;Application 类必须加。
2. **可注入类的构造函数要 `@Inject`** —— 否则 Hilt 不知如何创建;或用 `@Module` + `@Provides` 提供。
3. **作用域用错** —— 想「每个 Activity 一个实例」却用 `@Singleton`(全局共享),状态串了;按生命周期选作用域。
4. **接口多实现没限定符** —— 编译报「multiple bindings」;用 `@Named` / `@Qualifier` 区分。
5. **注入三方对象没写 @Module** —— Hilt 不会自己 new 三方库;必须 `@Provides` 提供。
6. **ViewModel 注入写错** —— ViewModel 用 `@HiltViewModel` + 构造函数 `@Inject`,而非字段注入。
7. **误以为 Hilt 用反射慢** —— Hilt / Dagger 是编译期生成代码、运行期无反射,性能不是问题。

## 待深入 / 下一步

**原理深挖**
- [ ] Component 层次与作用域传递:`SingletonComponent` → `ActivityRetainedComponent` → `ActivityComponent` → `FragmentComponent`/`ViewModelComponent`,子组件能拿到父组件的绑定、反之不行——决定依赖在哪些范围可见。
- [ ] 多绑定(multi-binding):`@IntoSet` 把多个实现聚成 `Set<X>`;`@IntoMap` + `@StringKey`/`@ClassKey` 聚成 `Map<K,V>`(策略模式/插件化的常见用法)。
- [ ] 为什么 Hilt/Dagger 编译期生成代码、运行期无反射 → 性能不是问题:读生成的 `Hilt_*` / `*_Factory` 代码确认。

**进阶 API**
- [ ] `@EntryPoint` + `EntryPointAccessors`:给 Hilt 不直接支持的类(如 `ContentProvider`、第三方库里的对象)手动取依赖。
- [ ] `@HiltViewModel` + `SavedStateHandle`:进程被杀后恢复状态,VM 构造注入 `SavedStateHandle`。
- [ ] `@HiltWorker` + Hilt 的 WorkManager 集成(`Worker` 也走 DI)。
- [ ] Compose 里用 `hiltViewModel()` 拿 `@HiltViewModel`(替代 Activity 的 `by viewModels()`)。

**测试**
- [ ] `@HiltAndroidTest` + `HiltAndroidRule`:插桩(instrumentation)测试里用 Hilt 容器。
- [ ] `@UninstallModules` / 替换 Module:把真实现换成 fake/mock,脱离网络/DB 测 UI。
- [ ] VM 单测直接构造传 mock 依赖(VM 不依赖 Android 框架时最轻量的测法)。

**工程化**
- [ ] 多 Gradle module 注入:feature module 怎么对外暴露 / 消费 Hilt 绑定。
- [ ] KSP vs kapt:Hilt 已支持 KSP、构建更快,迁移注意点。
- [ ] Hilt vs Koin 取舍:编译期 vs 运行期、无反射 vs 反射/代理、错误暴露时机(编译期 vs 运行期)。
- [ ] 实战:在自己项目跑通 §9 骨架 → 多 module → 测试替换,再考冲「熟悉」。

## 参考资料

- Hilt 指南:https://developer.android.com/training/dependency-injection/hilt-android
- Dagger:https://dagger.dev/
- Hilt 与 ViewModel:https://developer.android.com/training/dependency-injection/hilt-jetpack