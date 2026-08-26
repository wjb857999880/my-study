---
title: Hilt 依赖注入
domain: 02-框架与Jetpack
level: 精通
target: 精通
importance: 中
last_assessed: 2026-08-26
last_reviewed: 2026-08-26
next_review: 2027-02-22
tags: [Hilt, DI, Dagger]
related: [MVVM, 移动端架构设计]
---

# Hilt 依赖注入

## 概述
依赖注入(DI)把对象的创建与使用解耦,便于测试与降低耦合。**Hilt 基于 Dagger**、针对 Android 简化:用 `@HiltAndroidApp` + `@AndroidEntryPoint` + `@Inject`/`@Module`/`@Provides` 声明依赖,编译期自动生成装配代码。常见:注入 Repository / ViewModel / Retrofit,替换实现做单元测试。需理解作用域(`@Singleton` / `@ActivityScoped` 等)与组件层次。

## 考核记录
- **2026-08-26** 判定：了解 → 精通 ✅ ｜ 考官：AI
  - 表现：四档全部稳过——了解档 Hilt/Dagger/Koin 关系讲清;熟悉档 @Binds @Provides 抽象类/Module/作用域全对;掌握档 #1 排障(manifest 注册/super.onCreate 时机/作用域漏标/`/* */` 编译错误)四坑全中,#2 多绑定设计(@Binds @IntoSet + @JvmSuppressWildcards Kotlin 协变坑 + Set 为构建期不可变 + 动态用 Flow 替代)深度到位;精通档画出完整组件树并讲明可见性 + `HiltViewModelFactory` 走 `ActivityComponent` 的特殊通道 + 编译期 `*_Factory` 直接调无反射 + Hilt vs Koin 三维度 + 本质总结。
  - 依据：精通档要求"架构设计 + 原理深挖 + 性能权衡 + 能否讲透",组件父子可见性 + 编译期 codegen 路径 + Hilt/Koin 静态图 vs 动态图本质差异均讲透,达标。
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

## 四档考核 Q&A（2026-08-26）

### 了解档
**Q: ① Hilt 和底层 Dagger 的关系？② 全局入口要配对的两个注解？③ Hilt 相对于 Koin 这类运行期 DI 的工程取舍？**

A:
① **Hilt 基于 Dagger**，针对 Android 预置了一套**标准组件与生命周期**——把 Application / Activity / Fragment 等的 Component、Activity 注入入口自动生成，省去 Dagger 手写样板；底层仍是 Dagger 编译期生成代码。
② `@HiltAndroidApp`（标 Application，触发代码生成）+ `@AndroidEntryPoint`（标 Activity/Fragment/View/Service，标注可注入字段）。
③ Hilt/Dagger **编译期完成依赖图的装配与校验**，运行期无反射、无图遍历；Koin 是运行期注册 + get() 解析。取舍：**Hilt 跑得快、错误编译期暴露但配置不灵活**；Koin 灵活但运行期慢、错误可能上线才暴露。

---

### 熟悉档
**Q: Analytics（三方实现）希望全局单例，Clock（自有实现）希望每 Activity 一实例。请写出接口/实现/绑定模块，并简述 @Provides vs @Binds 的适用场景。**

A:

```kotlin
// 1. 接口与实现
interface Analytics { fun logEvent(name: String, params: Map<String, Any>? = null) }
interface Clock     { fun now(): Long }

// Firebase SDK 是 final class → 组合方式包装,实现类有 @Inject 构造器
@Singleton
class FirebaseAnalyticsImpl @Inject constructor(
    private val firebase: FirebaseAnalytics
) : Analytics { override fun logEvent(...) = firebase.logEvent(...) }

// 自有类 + @ActivityScoped
@ActivityScoped
class SystemClock @Inject constructor() : Clock {
    override fun now(): Long = java.lang.System.currentTimeMillis()
}

// 2. FirebaseAnalytics 是三方库 → 必须 @Provides(Hilt 不会自己 new)
@Module
@InstallIn(SingletonComponent::class)
object FirebaseModule {
    @Provides @Singleton
    fun provideFirebaseAnalytics(@ApplicationContext context: Context) =
        FirebaseAnalytics.getInstance(context)
}

// 3. 接口→实现 用 @Binds(MODULE 必须是 abstract class,方法本身必须是 abstract)
@Module
@InstallIn(SingletonComponent::class)
abstract class AppBindingsModule {
    @Binds @Singleton      abstract fun bindAnalytics(impl: FirebaseAnalyticsImpl): Analytics
    @Binds @ActivityScoped abstract fun bindClock    (impl: SystemClock): Clock
}
```

**@Provides vs @Binds 适用场景：**
- **@Binds**：纯「接口→实现」的零开销映射，实现类必须有 @Inject 构造器；方法在 `abstract class/interface` 内、无方法体。
- **@Provides**：三方库对象或需要调用工厂方法构造（Retrofit.Builder()…build()、FirebaseAnalytics.getInstance(ctx)）；方法可放 `object` / 普通 class / `companion object`，有方法体 return 实例。

一句话：实现类你写不出 `@Inject` 构造器 → `@Provides`；否则优先 `@Binds`（更轻、生成代码更少）。

---

### 掌握档 · 排障
**Q: 以下代码有什么问题？**

```kotlin
@HiltAndroidApp class App : Application()

@Module @InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides @Singleton
    fun provideRetrofit(): Retrofit { /* ... */ }
}

class MyService @Inject constructor()

@AndroidEntryPoint
class MyActivity : AppCompatActivity() {
    @Inject lateinit var myService: MyService
}
```

A: 四坑：

| # | 位置 | 问题 | 修复 |
|---|------|------|------|
| 1 | App.kt | Manifest 未配 `android:name=".App"` → Hilt 未触发，字段注入全 null | `<application android:name=".App" …>` |
| 2 | NetworkModule | `/* ... */` 让函数无 return 语句，**编译报错**：`must have a non-empty body` | 给出真实构造:`fun provideRetrofit(ok: OkHttpClient, gson: Gson) = Retrofit.Builder()…` |
| 3 | MyService | 无作用域注解 → 每次 @Inject 都 new 一个（注释里要的是「复用」） | 加 `@Singleton` |
| 4 | MyActivity | 字段注入发生在 `super.onCreate()` 之前完成 → 提前访问抛 NPE | `super.onCreate(savedInstanceState)` 必须最先调 |

只有 #2 编译失败；#1 / #4 运行时，#3 是语义错。

---

### 掌握档 · 多绑定设计
**Q: 用 Hilt 多绑定把多个 WelcomeProvider 聚成 Set 注入 Repository，加新 provider 时不动 Repository。**

A:

```kotlin
// 1. 接口 + 两个实现(都有 @Inject 构造器)
interface WelcomeProvider { fun welcome(): String }

class DefaultWelcomeProvider @Inject constructor() : WelcomeProvider {
    override fun welcome() = "欢迎,xxx"
}
class VipWelcomeProvider @Inject constructor() : WelcomeProvider {
    override fun welcome() = "尊享 VIP 通道已开通"
}

// 2. @Binds @IntoSet 收集(MODULE 用 interface 也行,因为全是 @Binds)
@Module
@InstallIn(SingletonComponent::class)
interface WelcomeBindings {
    @Binds @IntoSet fun bindDefault(impl: DefaultWelcomeProvider): WelcomeProvider
    @Binds @IntoSet fun bindVip   (impl: VipWelcomeProvider): WelcomeProvider
}
// 之后加 HolidayProvider 只动这一个 interface,其它代码零修改。

// 3. Repository 收 Set(注意 @JvmSuppressWildcards:解决 Kotlin Set<out T> 协变与 Dagger 生成代码的冲突)
@Singleton
class WelcomeRepository @Inject constructor(
    private val providers: Set<@JvmSuppressWildcards WelcomeProvider>
) {
    fun buildWelcome() = providers.joinToString("\n") { it.welcome() }
}
```

- 注入 `Set<WelcomeProvider>` 即可（不是 `Provider<Set<…>>`），multibinding 在 Component 创建时已定型为「组装好的一次性快照」。
- 该 Set **不可变**（底层 `Collections.unmodifiableSet`）；想做运行期新增需叠自己的 `mutableSetOf`，或换 Flow / 事件总线——**多绑定是编译期/构建期多态，不是运行期容器**。
- `@JvmSuppressWildcards` 是 Kotlin 协变与 Dagger codegen 类型推导的常见坑，省掉会编译失败。

---

### 精通档
**Q1: Fragment 想注入 @ViewModelScoped 的 UserState，UserState 依赖 @ActivityScoped 的 AnalyticsTracker，AnalyticsTracker 依赖 @Singleton 的 ApiService。能否解析？为什么？**

A: **能**——但走 Hilt 的特殊通道，而不是看父子组件同名作用域。

Hilt 组件树与可见性规则：

```
SingletonComponent            @Singleton
└── ActivityRetainedComponent @ActivityRetainedScoped
    ├── ViewModelComponent    @ViewModelScoped   ← UserState 这里
    └── ActivityComponent     @ActivityScoped    ← AnalyticsTracker 这里
        └── FragmentComponent @FragmentScoped
```

**单向可见**：`子可见父，父不可见子，兄弟互不可见`——长寿命作用域可被短寿命作用域消费，反之不行。表面看 `ViewModelComponent` 不可见 `ActivityScoped`（兄弟），按规则会失败。但 `@HiltViewModel` 的解析不走 `ViewModelComponent`，而是由 `HiltViewModelFactory`（持有 `ActivityComponent`）构造 VM，让 VM 能看到 ActivityScoped 绑定及其祖先。这正是 Hilt 设计 `ActivityRetainedComponent` + `HiltViewModelFactory` 的目的。

**核心原则**：作用域只能从大到小消费，不能从小到大依赖——这是 lifetime 兼容性硬约束，不是 Hilt 限制。

---

**Q2: 反过来 ViewModel 注入 @FragmentScoped 依赖行不行？反映出作用域传递的什么本质？**

A: **不行**。`FragmentComponent` 是 `ActivityComponent` 的子孙，而 `ViewModelComponent` 与 `ActivityComponent` 平级。反向注入会产生「Fragment 已销毁但 ViewModel 仍持有其引用」的悬空依赖。

**本质**：作用域只能从大到小单向消费，不能反向依赖。父子不可见是语义约束而非框架约束——`@FragmentScoped` 实例的寿命短于 `@ViewModelScoped`，绑定方向只能是短→长允许、长→短禁止。

---

**Q3: 这种「传递合法性」是编译期保证还是运行期校验？为什么说 Hilt 运行期无反射、无图遍历？**

A: **编译期保证**。`kotlinc + Dagger APT` 在编译期校验整张依赖图：scope 匹配？依赖可见？作用域嵌套合法？任一不满足 → build 红字。示意错误：

```
[ksp] error: AnalyticsTracker is scoped to a component that is not a
parent of the component in which UserState is scoped.
```

**与生成代码的关系**：Dagger/Hilt 为每个绑定生成**普通 Java/Kotlin 类**，全是直接方法调用：

```java
public final class UserState_Factory implements Factory<UserState> {
    private final Provider<AnalyticsTracker> trackerProvider;
    @Override public UserState get() {
        return new UserState(trackerProvider.get());   // 直调,无反射
    }
}
```

APK 打包前图已展平为 `new X(provider.get())`，运行期没有 `Class.forName` / `getDeclaredMethod` / 图查找——这也是 Hilt 比 Koin/Guice 快得多的根因。

---

**Q4: 同样的多作用域依赖链切到 Koin，从依赖可见性 / 错误暴露时机 / 测试性三个维度的本质差异？**

A:

| 维度 | Hilt | Koin |
|------|------|------|
| **依赖可见性** | 编译期硬约束：组件父子 + scope 嵌套规则强制 | 运行期软约束：所有 module 注册进全局 `GlobalContext`，谁都能 `get()` / `inject()` |
| **错误暴露时机** | 编译期——scope 不对 / 依赖未提供 → build 红字 | 运行期——第一次 `get()` 才抛 `NoBeanDefFoundException`，APK 可能已到用户手机 |
| **测试性** | 较重——`@TestInstallIn(replaces=[…])` 或 `HiltAndroidRule` 重启整套；模块不可热替换 | 极简——`loadKoinModules(testModule)` / `unloadKoinModules()` 一行替换；`KoinTestRule` 几行搞定 |

**本质一句话**：**Hilt 把图画在编译期（静态、强校验、快运行）；Koin 把图画在运行期（动态、弱校验、慢一点但灵活）**。选哪个取决于更怕：写代码时编译器报红，还是上线后用户碰到 `NoBeanDefFoundException`。

## 参考资料

- Hilt 指南:https://developer.android.com/training/dependency-injection/hilt-android
- Dagger:https://dagger.dev/
- Hilt 与 ViewModel:https://developer.android.com/training/dependency-injection/hilt-jetpack