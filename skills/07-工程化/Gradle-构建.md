---
title: Gradle 构建配置
domain: 07-工程化
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-15
next_review: 2026-11-09
tags: [构建, Gradle]
related: []
---

# Gradle 构建配置

## 概述
**Gradle** 是 Android 官方构建系统(取代了早期的 Ant),职责是把源码、资源、依赖加工成 APK/AAB:编译、打包、签名、变体管理、依赖解析全归它管。它基于 **Groovy/Kotlin DSL** 写 `build.gradle(.kts)`,运行在 **JVM** 上,可直接复用 Maven 仓库的依赖。理解 Gradle 的核心心智模型是**两个阶段**:**配置期**(读所有脚本、构建 Task DAG)与**执行期**(只跑被选中及其依赖的 Task);几乎所有「build 慢」「莫名其妙重新编译」问题都源于搞混了这两阶段。Android 侧真正干活的是 **AGP(Android Gradle Plugin)**,它在 Gradle 之上定义了 Application/Library 模型、构建变体(`buildTypes × productFlavors`)和打包流程。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 为什么需要 Gradle / 它的角色

早期 Android 用 Ant(命令式、写一堆 XML/脚本,繁琐)。Gradle 凭 **声明式 DSL、增量构建、依赖管理、灵活的插件机制、构建缓存/并行** 成为官方构建工具。它把「构建」建模成一个**有向无环图(DAG)的 Task**:你声明 Task 与依赖关系,Gradle 算出执行顺序并增量/并行执行——你描述「要什么」,它决定「怎么跑」。

### 2. 三大生命周期阶段

Gradle 每次构建走三阶段:

- **Initialization**:读 `settings.gradle(.kts)`,决定有哪些 Project 参与构建(`include` 的模块),为每个创建 `Project` 对象。
- **Configuration**:对每个 Project 从上到下**执行** `build.gradle(.kts)` 里的 DSL 代码——这里「执行」是真的跑一遍 Groovy/Kotlin,目的是**配置 Task**(设属性、建依赖关系),最终形成 **Task 执行图(DAG)**。即使你只想跑一个 task,所有相关配置代码也都会执行。
- **Execution**:按 DAG 拓扑序执行被请求的 Task 及其依赖,真正干活(编译/拷贝/签名)。Task 的 `doFirst`/`doLast` 只在这一阶段运行。

### 3. 配置期 vs 执行期(最易踩坑的心智模型)

- **配置期代码** = `build.gradle` 顶层、`android { }` 块、`dependencies { }`、`task { }` 配置块里的语句;**每次构建都跑**(不论最终执行哪个 task)。
- **执行期代码** = Task 的 `doLast { }` / `doFirst { }` 闭包、`@TaskAction` 方法。
- 典型错误:在配置期读文件 / 跑外部命令 / 算复杂逻辑 → 每次构建都付代价,还会破坏 **Configuration Cache**。
- 钩子:`afterEvaluate { }`(配置完单个 Project 后回调)、`gradle.taskGraph.whenReady { }`(DAG 构建好后,可在此动态决定是否加 task)。

### 4. Project / Task 模型与增量构建

- **Project** = 一个模块,与 `build.gradle` 一一对应,持有属性、依赖、配置。
- **Task** = 最小工作单元,有 `actions`(doFirst/doLast)与 **inputs / outputs**。
- **增量构建(up-to-date check)**:Task 声明了 inputs/outputs 后,Gradle 比对两者的哈希与上次构建;一致就跳过(`UP-TO-DATE`)。这是 build 快的关键——**没声明 inputs/outputs 的自定义 task 每次都重跑**。
- 进阶:**Build Cache**(local/remote)按 inputs 哈希缓存 outputs,换机器 / CI 命中即可复用产物;**Configuration Cache** 缓存配置期结果,跳过重复配置。

### 5. 依赖管理:implementation vs api 与传递依赖

- `implementation`:依赖**不向下游传递**(不进消费者的 compile classpath),下游编译时看不到它。改它**只重编本模块**,不波及依赖方。**默认应优先用 implementation。**
- `api`:依赖**会传递**给下游(进 compile classpath),适合「下游要直接用到这个库的类型」(通常是底层基础库 / facade 模块)。改 api 依赖会让所有下游重编译。
- 来源:`java-library` 插件提供 implementation/api;旧的 `compile`(已废弃)≈ api。另有 `testImplementation` / `androidTestImplementation` / `compileOnly`(仅编译期,如注解处理器) / `runtimeOnly`。
- 解析与冲突:Gradle 默认取**冲突依赖中最高版本**(newest);可用 `resolutionStrategy.force` / 依赖 `constraints` 统一;`./gradlew :app:dependencies` / `dependencyInsight` 看依赖树。

常用依赖配置对比:

| 配置 | 对本模块 | 对下游(传递性) | 典型用途 |
|---|---|---|---|
| `implementation` | 编译 + 运行可见 | **不传递**(不进下游 compile classpath) | **默认**;内部依赖 |
| `api` | 编译 + 运行可见 | **传递**(进下游 compile classpath) | 基础库,下游要用到其类型 |
| `compileOnly` | 仅编译期 | 不传递 | 注解处理器 / provided 依赖 |
| `runtimeOnly` | 仅运行期 | 不传递 | 运行时实现(如日志后端) |
| `testImplementation` | 测试编译 + 运行 | 不传递 | 单元测试依赖 |

### 6. AGP 与构建变体(buildTypes × productFlavors)

- **AGP** 提供 `com.android.application` / `com.android.library` 插件,在 Gradle 之上加 `android { }` DSL:`compileSdk`、`defaultConfig { applicationId, minSdk, targetSdk, versionCode }`、签名、`buildTypes { debug / release }`、`productFlavors`。
- **构建变体(Variant)** = `buildType` × 各 `flavorDimension` 的笛卡尔积。例:2 flavor(free/paid)× 2 buildType(debug/release)= 4 个变体,各自有独立 sourceSet(`src/freeDebug/`)、applicationId 后缀、依赖(`freeImplementation`)。
- `flavorDimensions` 声明维度,每个 flavor 必须归属一个维度;多维度时变体数 = 各维度 flavor 数之积,容易爆炸。
- 产物:`assemble<Variant>` 打 APK,`bundle<Variant>` 打 AAB。

### 7. 构建加速:Daemon / 并行 / Configuration Cache / Build Cache

- **Gradle Daemon**:长驻 JVM 进程,复用类加载 / JIT,省 JVM 启动开销(默认开,`--no-daemon` 关)。
- **并行**(`org.gradle.parallel=true`):多模块并行执行无依赖关系的 Task。
- **Configuration Cache (CC)**:缓存「配置期算出的 Task 图与状态」,下次构建直接复用、跳过整段配置——大项目提速显著。Gradle 8.0 引入(opt-in)、**8.1 起稳定**,AGP 自 7.0 起逐步兼容;用了不可序列化全局态(如直接捕获 `Project`、`afterEvaluate` 改图)的插件会序列化失败。
- **Build Cache**:按 task inputs 哈希缓存 outputs,`org.gradle.caching=true`;分 local(`.gradle`) 与 remote(CI 共享、跨机器命中)。
- 组合:Daemon + 并行 + CC + Build Cache 是现代大项目提速「四件套」。

### 8. 排查与性能工具

- `./gradlew --scan`:发布 **Build Scan**(构建报告),看每个 task 耗时、配置期耗时、依赖解析、CC 命中率——排查慢构建**最先该用**。
- `./gradlew build --profile`:本地 HTML 性能报告。
- **Android Studio Build Analyzer**:可视化哪个 task 慢、为什么没 up-to-date。
- `:app:dependencies` / `:app:dependencyInsight --dependency <名>`:查依赖来源与冲突。
- `--offline`:CI 离线构建(配合缓存)避免网络抖动失败。
- 不兼容排查:`--configuration-cache` 跑一次看 CC 报告哪些插件/写法不支持。

## 实践经验 / 踩坑

1. **滥用 api → 编译雪崩** —— 默认用 implementation,只在确实要暴露给下游时才用 api;否则改一个库全仓库重编,增量构建失效。
2. **配置期做重活** —— 在 `build.gradle` 顶层 / `android{}` 里读 git commit、跑 shell、动态算 versionCode → 每次构建都付代价且破坏 CC;挪进 task 的 `doLast`,或用 buildSrc / Version Catalog 管理。
3. **自定义 task 没声明 inputs/outputs** —— 永远不是 up-to-date、每次重跑;用 `@Input`/`@OutputDirectory` 注解或 `inputs.file()` / `outputs.file()` 声明。
4. **依赖冲突 NoClassDefFound / NoSuchMethod** —— 多版本同名类被解析;`dependencyInsight` 查、`resolutionStrategy.force` 统一到兼容版本,而不是靠「运气」。
5. **Configuration Cache 不兼容** —— 老插件捕获 `Project` 等可变全局态、或 `afterEvaluate` 里改 task 图 → CC 序列化失败报错;升级插件,或临时 `org.gradle.configuration-cache.problems=warn` 先放过。
6. **变体爆炸** —— 多 flavor × buildType 导致变体数与编译时间暴涨;用 `android.variantFilter { setIgnore(true) }` 关掉不发布的组合。
7. **版本漂移 / daemon 吃内存** —— 多项目各自 Gradle 版本各起 daemon 吃内存;用 `gradle-wrapper` 锁版本并提交 `gradle/wrapper` 到仓库,保证团队构建环境一致。

## 待深入 / 下一步

- [ ] 实战 Configuration Cache:适配所有第三方插件,CI 上开启
- [ ] 搭建 remote Build Cache(CI 产出、本地命中)
- [ ] 读 Gradle 源码,理解 task graph 构建与 up-to-date 哈希算法

## 参考资料

- Gradle User Guide:https://docs.gradle.org/current/userguide/userguide.html
- Configuration Cache:https://docs.gradle.org/current/userguide/configuration_cache.html
- AGP / 构建配置:https://developer.android.com/build
- Build variants:https://developer.android.com/build/build-variants
- implementation vs api(java-library 插件):https://docs.gradle.org/current/userguide/java_library_plugin.html