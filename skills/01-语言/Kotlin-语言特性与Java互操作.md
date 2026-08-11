---
title: Kotlin 语言特性与 Java 互操作
domain: 01-语言
level: 了解
target: 精通
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-24
tags: [Kotlin, 语法, 互操作]
related: [Kotlin 协程]
---

# Kotlin 语言特性与 Java 互操作

## 概述
Kotlin 是 Android 官方首选语言,核心特性:**空安全**(类型系统区分可空 / 非空,编译期防空指针)、**扩展函数**(给已有类加方法)、**数据类**(自动生成 equals/hashCode/toString/copy)、**密封类 / sealed interface**(受限类型层级,配合 when 穷举)、**作用域函数**(let/run/apply/also)、**默认参数 + 命名参数**、**智能类型转换**。与 Java 互操作:Kotlin 可无缝调 Java,但要注意可空性**平台类型(platform type)**、`@JvmStatic`/`@JvmField`/`@JvmOverloads` 供 Java 调用方、集合可变性差异。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 空安全与平台类型
Kotlin 类型系统区分非空(`String`)与可空(`String?`),编译期强制:可空类型必须判空才能访问成员。配套运算符:`?.` 安全调用、`?:` elvis 默认值、`!!` 强解(可能抛 NPE)。这是 Kotlin 治理空指针的核心。
**平台类型(platform type,`String!`)** 在调用 Java(返回类型无空信息)时出现——编译器不强制判空,等同 Java 的「可能 null」。它是 Kotlin↔Java 互操作最大的 NPE 来源:一旦把平台类型传给 Kotlin 非空参数,运行时为 null 仍会崩。最佳实践:Java API 在 Kotlin 侧包一层带 `@Nullable` 注解的封装,或显式判空。

### 2. 扩展函数与扩展属性
`fun String.lastChar() = this[length - 1]` 给已有类(含 final、第三方)加方法,**不改源码、不真正继承**。本质:编译成静态方法,首个参数是接收者。由此推论:
- **静态解析**:按编译时类型决定调用哪个扩展,**没有多态**;
- 与成员函数同名时成员优先;
- 可空接收者 `fun String?.` 也能扩展。
Android 中 `view.visible()` / `dp2px()` 等工具普遍用扩展实现。

### 3. 数据类、密封类、枚举
- `data class`:主构造至少 1 个属性,自动生成 `equals/hashCode/toString/copy/componentN`(解构)。适合纯数据载体(DTO/Model)。默认 final、不可继承(需 `open` 或放进 `sealed`)。
- `sealed class/interface`:受限类型层级,**所有子类必须在同一文件/模块**。配合 `when` 可穷举,编译器强制覆盖全部分支——新增子类漏判会编译报错。这是表达「有限状态」(UI 状态、Result 成功/失败)的核心利器。
- `enum class`:经典枚举,可实现接口、带构造参数。

### 4. 作用域函数与惯用法
五个作用域函数,差异在「返回值」与「this/it」:

| 函数 | 引用对象 | 返回值 | 典型用途 |
|------|---------|--------|---------|
| let | it | lambda 结果 | 可空判空 `x?.let {}`、临时改名 |
| run | this | lambda 结果 | 初始化并计算 |
| with | this | lambda 结果 | 对同一对象多次调用(非扩展) |
| apply | this | 对象本身 | 构建/初始化(`Bundle().apply{}`) |
| also | it | 对象本身 | 链式副作用、日志(不改对象) |

口诀:操作对象用 apply/also(返回对象、可链式);计算用 let/run。

### 5. 默认参数、命名参数与 @JvmOverloads
`fun f(a: Int, b: Int = 0)` 支持省略带默认值的参数、用命名参数乱序传参,大幅减少方法重载样板。
但 **Java 调用方看不到默认参数**——加 `@JvmOverloads` 让编译器为每个默认组合生成重载。Android 自定义 View 多构造器正是 `constructor(c, a, d = 0) : this(c, a, d, 0)` + `@JvmOverloads` 的典型场景。

### 6. object / companion object / 顶层声明 + @JvmStatic/@JvmField
- `object`:单例对象,线程安全(类加载初始化),替代 Java 手写单例。
- `companion object`:类内「静态」伴生对象,成员经 `Companion.xxx` 访问;工厂方法、常量放这。
- 顶层函数/属性:直接写在文件顶层,编译成 `FileNameKt` 的静态成员。
Java 要静态风味需:`@JvmStatic`(方法变真静态)、`@JvmField`(字段暴露为 public field 而非 getter)、`@file:JvmName("Util")`(控制生成类名)。

### 7. Kotlin ↔ Java 互操作要点
- **集合可变性**:Kotlin `List` 是只读 view、`MutableList` 才可改;但调 Java 返回的 `List` 实际可变,Kotlin 无法保证——遍历时被改 → `ConcurrentModificationException`。
- **受检异常**:Kotlin 无 checked exception,调会抛 IOException 的 Java 方法无需 try-catch 声明。
- **反射**:Kotlin 类有 `.isCompanion`/`.isData` 等(kotlin-reflect);KClass vs Java Class(`.javaClass`/`.kotlin`)。
- **lambda**:非 inline lambda 在 Java 侧是 `Function1` 等函数接口。

### 8. 与 Java 的关键语义差异
- **等价性**:`==` 在 Kotlin 是结构相等(调 `equals`,即 Java 的 `equals`),`===` 才是引用相等(Java 的 `==`)——高频考点。
- **协变**:Kotlin `Array<out T>`(声明处协变)、`List<out T>` 默认协变,比 Java 数组协变更安全。
- **smart cast**:判空/`is` 后编译器自动窄化类型无需强转;但 `var` 可变属性的 smart cast 会失效(可能被并发改)。
- **默认不可继承/不可重写**:类/方法默认 `final`,需 `open` 才能继承/重写(Java 默认可继承)——鼓励组合优于继承。

## 实践经验 / 踩坑

1. **平台类型 NPE**:Kotlin 调 Java `getExtra()` 返回 `String!`,当非空用即崩。养成「Java 返回值一律当可空」或封装带空注解的 Kotlin 层。
2. **lateInit**:用于非空延迟初始化(DI 注入字段),访问前未初始化抛 `UninitializedPropertyAccessException`,用 `::x.isInitialized` 守卫;不能用于 `val`/可空/基本类型。
3. **by lazy 线程安全**:`lazy {}` 默认 `SYNCHRONIZED`(双检锁);确定单线程访问用 `LazyThreadSafetyMode.NONE` 提速;只能用于 `val`。
4. **扩展无多态**:父/子类同名扩展,调用结果取决于**编译时声明类型**而非运行时类型——别用扩展模拟「重写」。
5. **data class 陷阱**:自动 `equals/hashCode` 含全部主构造属性;含可变字段作 HashMap key 后被改会丢;`copy` 是浅拷贝。
6. **集合跨边界**:Kotlin `mutableListOf()` 传给 Java 被改 → 你这边意外变化;只读 `List` 经 Java 改 → 并发修改异常。跨边界先 `.toList()` 取不可变副本。
7. **const vs @JvmField**:`const val` 是编译期常量(内联进调用处),`@JvmField` 是运行时 public field;`companion object` 里 `const val` 才是真静态常量。

## 待深入 / 下一步
- [ ] Kotlin **K2 编译器**前端重写(2024+ 默认,提速、更稳)
- [ ] 内联类 / **value class**(无装箱的包装类型)
- [ ] 契约(contracts):`callsInPlace` 让 smart cast 更强
- [ ] Kotlin Metadata:字节码里的 `@Metadata` 如何支撑特性
- [ ] 与协程的衔接(structured concurrency)——见 [[Kotlin 协程]]

## 参考资料
- Kotlin 语言参考:https://kotlinlang.org/docs/reference/
- Kotlin 调 Java 互操作:https://kotlinlang.org/docs/java-interop.html
- Java 调 Kotlin:https://kotlinlang.org/docs/java-to-kotlin-interop.html
- Android Kotlin 指南:https://developer.android.com/kotlin