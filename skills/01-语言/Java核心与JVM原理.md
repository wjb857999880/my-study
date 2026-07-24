---
title: Java 核心与 JVM 原理
domain: 01-语言
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [Java, JVM, 集合]
related: [多线程与并发]
---

# Java 核心与 JVM 原理

## 概述
Java 仍是 Android 历史代码与 SDK 的基础。核心:**集合框架**(List/Set/Map 各实现与适用场景、HashMap 原理)、**面向对象**(封装 / 继承 / 多态、接口 vs 抽象类)、**泛型与类型擦除**、**异常体系**。JVM / ART 层:**类加载机制**(双亲委派)、**内存区域**(堆 / 栈 / 方法区)、**GC**(分代回收、可达性分析、GC Root)、对象生命周期。Android 上是 **ART**(编译成机器码,而非标准 JVM),但 JVM 知识是理解内存 / GC / 并发的地基。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 集合框架全景
两大顶层:`Collection`(List/Set/Queue)与 `Map`。
- **List**:有序可重复。`ArrayList`(数组,随机访问 O(1)、尾增 O(1) 均摊、中间插 O(n),最常用)、`LinkedList`(双向链表,理论增删快但缓存不友好、多数更慢)、`CopyOnWriteArrayList`(读多写极少,写时复制)。
- **Set**:`HashSet`(基于 HashMap,无序)、`LinkedHashSet`(保插入序)、`TreeSet`(红黑树有序)。
- **Map**:`HashMap`(主力)、`LinkedHashMap`(保序 + 可做 LRU)、`TreeMap`(按 key 排序)、`ConcurrentHashMap`(并发)。
- **Queue/Deque**:`ArrayDeque`(栈/队列首选,优于 Stack/LinkedList)、`PriorityQueue`(堆)。

### 2. HashMap 原理(JDK 8+)
`数组 + 链表 + 红黑树`。桶下标 = `(n - 1) & hash(key.hashCode() 扰动)`。put 流程:算 hash → 定位桶 → 空则放 → 有则沿链/树比较 key(equals),相同覆盖否则尾插。**链表长度 ≥ 8 且数组 ≥ 64 转红黑树(O(logn));缩到 ≤ 6 退化回链表**。
**扩容**:超过 `容量 × 负载因子(0.75)` 时 2 倍扩容并 rehash(JDK8 用高位 bit 判断「原位 / 原位 + oldCap」两分,免重算)。容量建议预设为「预期元素 / 0.75」再取 2 的幂,避免反复扩容。

### 3. ConcurrentHashMap
并发安全的 HashMap。JDK7 用分段锁(Segment,16 段);**JDK8 起改为「数组 + 链表/红黑树 + CAS + synchronized 锁单桶头节点」**——锁粒度细化到桶,并发度大增。size 用 LongAdder 思想的 `CounterCell` 分段计数减少竞争;get 全程无锁(volatile 读)。

### 4. 面向对象核心
- **封装**:private 字段 + getter/setter,隐藏内部。
- **继承**:`extends` 单继承、`implements` 多接口。
- **多态**:编译时类型 vs 运行时类型;**动态分派**基于运行时类型调重写方法(虚方法表 vtable);`instanceof` + 强转。
- **接口 vs 抽象类**:接口重「行为契约」(Java8+ default/static 方法、Java9+ private 方法),抽象类重「is-a + 部分实现」(单继承)。优先接口、组合优先继承。

### 5. 泛型与类型擦除
Java 泛型是**编译期**机制:编译后类型参数擦除为上界(默认 Object),运行时 `List<String>` 与 `List<Integer>` 是同一个 `List`。后果:
- 运行时不能 `new T()`、不能 `instanceof T`;
- 编译器靠**桥接方法(bridge method)**保证多态正确(子类泛型方法与父类擦除后签名一致时插入);
- 基本类型必须装箱(`List<Integer>` 而非 `List<int>`),有装箱开销。

### 6. 类加载机制
**双亲委派**:加载类时先委托父加载器,父找不到才自己加载,保证核心类(如 java.lang.String)不被篡改。层级:Bootstrap → Platform(原 Extension)→ Application(ClassPath)→ 自定义。
阶段:加载 → 验证 → 准备(静态变量赋默认值)→ 解析(符号引用→直接引用)→ 初始化(`<clinit>` 执行静态块)。**Android 走 ART/DexFile**,类加载用 `PathClassLoader`/`DexClassLoader`(基于 dex),双亲委派思想一致、实现不同。

### 7. JVM 内存区域
- **堆(Heap)**:对象实例 + 数组,GC 主战场,分新生代(Eden + 2 Survivor)/ 老年代,所有线程共享。
- **虚拟机栈(VM Stack)**:线程私有,存栈帧(局部变量表 / 操作数栈 / 动态链接);递归过深 → StackOverflowError。
- **本地方法栈**:native 方法。
- **方法区**:类信息 / 常量池 / 静态变量。JDK8 前是「永久代 PermGen」(易 OOM),**JDK8+ 改为「元空间 Metaspace」用本地内存**,不再挤堆。
- **程序计数器(PC)**:线程私有,指向当前指令。
Android ART 有自己的内存布局(对象头、card table),概念相通。

### 8. 垃圾回收(GC)
- **判定可达**:从 **GC Root**(栈局部变量、静态字段、JNI 引用、活动线程)出发做可达性分析,不可达即回收——不数引用计数(难解循环引用)。
- **分代假说**:多数对象朝生夕灭 → 新生代用复制算法(Eden→Survivor,Minor GC 廉价频繁);老年代用标记-清除/标记-整理(Major/Full GC 昂贵)。
- **常用收集器**:Serial、Parallel(吞吐)、CMS(并发低停顿,JDK9 弃用)、**G1**(Region 化、可预测停顿,JDK9+ 默认)、ZGC/Shenandoah(亚毫秒级低停顿)。
- **Android ART GC**:运行时回收,分 **Partial GC(新生代)/ Full GC(全堆)**,用屏障 + 并发标记,目标是减少 UI 卡顿。排查用 `dumpsys meminfo` / ART 日志。

## 实践经验 / 踩坑

1. **HashMap 并发不安全**:JDK7 多线程扩容链表成环 → get 死循环;JDK8 改尾插解环但仍可能丢数据。多线程一律用 `ConcurrentHashMap`。
2. **== vs equals + 缓存陷阱**:`==` 比引用;`Integer a=127,b=127` 为 true(`IntegerCache` 缓存 -128~127),`128` 则 false。包装类比较必须 `equals`。
3. **自动装箱 NPE**:`Integer i = null; int j = i;` 拆箱抛 NPE;`Map.get` 返回 null 当 int 用同样崩。
4. **ArrayList vs LinkedList**:LinkedList「增删快」只在已定位节点处成立,`get(i)` 是 O(n)。绝大多数场景 ArrayList 更快(缓存友好),别无脑选 LinkedList。
5. **fail-fast**:ArrayList 迭代时结构被改 → `ConcurrentModificationException`(单线程用 iterator.remove,多线程用并发集合)。
6. **内存泄漏**:静态集合/单例持有 Activity、非静态内部类(默认持外部引用)后台线程持 View → Activity 无法回收。Android 用 static + WeakReference 或生命周期感知组件。
7. **OOM 多在堆/Bitmap**:Android OOM 常因 Bitmap 未按采样压缩、长生命对象未释放,而非 GC 本身;先看 `dumpsys meminfo` 与 LeakCanary。

## 待深入 / 下一步
- [ ] ZGC / Shenandoah 着色指针与读屏障原理
- [ ] ART 的 GC 与卡表(card table)、并发标记细节
- [ ] 字节码与 MethodHandle / invokedynamic
- [ ] 对象内存布局(对象头、Mark Word、指针压缩)
- [ ] 衔接并发内存模型 → [[多线程与并发]]

## 参考资料
- 《深入理解 Java 虚拟机(第 3 版)》周志明
- JVM 规范:https://docs.oracle.com/javase/specs/
- Android ART:https://source.android.com/docs/core/runtime
- Java 集合教程:https://docs.oracle.com/javase/tutorial/collections/
