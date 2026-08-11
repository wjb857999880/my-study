---
title: Java 核心与 JVM 原理
domain: 01-语言
level: 掌握
target: 精通
importance: 高
last_assessed: 2026-08-10
last_reviewed: 2026-08-10
next_review: 2026-11-08
tags: [Java, JVM, 集合]
related: [多线程与并发]
---

# Java 核心与 JVM 原理

## 概述
Java 仍是 Android 历史代码与 SDK 的基础。核心:**集合框架**(List/Set/Map 各实现与适用场景、HashMap 原理)、**面向对象**(封装 / 继承 / 多态、接口 vs 抽象类)、**泛型与类型擦除**、**异常体系**。JVM / ART 层:**类加载机制**(双亲委派)、**内存区域**(堆 / 栈 / 方法区)、**GC**(分代回收、可达性分析、GC Root)、对象生命周期。Android 上是 **ART**(编译成机器码,而非标准 JVM),但 JVM 知识是理解内存 / GC / 并发的地基。

## 考核记录
- **2026-08-10** 判定：了解 → 掌握 ✅ ｜ 考官：AI
  - 表现：了解档概念题(GC Root 可达性分析 vs 引用计数、HashMap 红黑树触发条件)全部答准；熟悉档 LinkedHashMap LRU 手写(含 ReentrantReadWriteLock 读写锁)正确；掌握档 ConcurrentHashMap 排障(merge 原子复合操作)与锁粒度分析正确；精通档(单桶锁对象身份、异步合并写入)暂未答出。
  - 依据：稳稳守住掌握档——概念/照做/排障三层均验证通过；精通档深挖(JDK8  synchronized 锁对象身份细节、CAS vs 锁的取舍)仍需补充。距 target「掌握」已达成，下次复习 90 天后(2026-11-08)。
- **2026-07-28** 判定：了解 → 了解 ✅(持平,但了解档质量由下沿升到上沿)｜ 考官：AI
  - 表现：复考昨日薄弱点全对——HashMap 转树规则记准(链表 ≥8 **且** 容量 ≥64、「且」非「或」、容量<64 先扩容);GC Root 定义正确(是可达性分析**起点对象**而非引用类型)、枚举完整(局部变量/参数、静态、常量、线程、JNI、synchronized 锁);引用计数致命在**循环引用**。但熟悉档照做题(LinkedHashMap 手写 LRU)给提示后仍写不出,accessOrder / removeEldestEntry 两关键点未掌握。
  - 依据：了解档概念能讲清且昨日薄弱点已补,稳稳守住;但「给 API 写出可行用法」的熟悉档还做不到。最高稳稳答到 = 了解。已补 LinkedHashMap LRU 实现到正文(3.1)。距 target「掌握」仍差 2 档,建议把集合实战用法(LinkedHashMap LRU、ConcurrentHashMap 并发用法)练熟后再考。
- **2026-07-27** 判定：了解 → 了解 ✅ ｜ 考官：AI
  - 表现：术语有印象(GC Root、HashMap「数组+链表+红黑树」)但讲不透——GC Root 定义含糊、只记得静态变量、漏「循环引用 vs 引用计数」关键点;HashMap 转树规则记错(把 8/6/64 混淆、漏「容量≥64」前提、条件误写成「或」)。
  - 依据：两道了解档概念题都只到「有印象」层级,定义/枚举/具体规则多处不准确,未达「能讲清」,守住了解档下沿。距 target「掌握」差 2 档,建议先系统复习(尤其 HashMap 原理、GC 与可达性分析)再考核。

## 核心原理 / 关键点

### 1. 集合框架全景
两大顶层:`Collection`(List/Set/Queue)与 `Map`。
- **List**:有序可重复。`ArrayList`(数组,随机访问 O(1)、尾增 O(1) 均摊、中间插 O(n),最常用)、`LinkedList`(双向链表,理论增删快但缓存不友好、多数更慢)、`CopyOnWriteArrayList`(读多写极少,写时复制)。
- **Set**:`HashSet`(基于 HashMap,无序)、`LinkedHashSet`(保插入序)、`TreeSet`(红黑树有序)。
- **Map**:`HashMap`(主力)、`LinkedHashMap`(保序 + 可做 LRU)、`TreeMap`(按 key 排序)、`ConcurrentHashMap`(并发)。
- **Queue/Deque**:`ArrayDeque`(栈/队列首选,优于 Stack/LinkedList)、`PriorityQueue`(堆)。

### 2. HashMap 原理(JDK 8+)
`数组 + 链表 + 红黑树`三件套,各自职责:**数组** O(1) 定位桶、**链表** 处理 hash 冲突、**红黑树** 把冲突桶最坏查找从 O(n) 拉回 O(logn)(防极端 / 恶意 hash 碰撞下的性能塌陷)。
- **桶下标** = `(n - 1) & hash`(`n` 为数组长度)。用位与而非取模 → 要求 **n 必须是 2 的幂**(扩容恒乘 2 保性质);`hash` 非裸 `hashCode()`,而是 `(h = key.hashCode()) ^ (h >>> 16)` **扰动**,把高位 bit 混进低位减少碰撞。
- **put 流程**:算 hash → 定位桶 → 空则放 → 有则沿链/树比较 key(`equals`),相同覆盖否则尾插。
- **转红黑树规则(易错,务必记准)**:链表长度 **≥ 8** **且** 数组容量 **≥ 64** → 转红黑树;两条件是**「且」非「或」**。容量 < 64 时即便链表到 8 也**先扩容**(扩容摊薄冲突比转树更划算)。退化阈值 **≤ 6** 回链表(6 与 8 之间留缓冲,防边界反复横跳)。阈值 8 源自泊松分布:负载因子 0.75 下单桶到 8 的概率约亿分之六,正常几乎不触发。
- **扩容**:`元素数 > 容量 × 负载因子(0.75)` 时 2 倍扩容并 rehash(JDK8 用高位 bit 判断「原位 / 原位 + oldCap」两分,免重算 hashCode)。容量建议预设为「预期元素 / 0.75」再取 2 的幂,避免反复扩容。

### 3. ConcurrentHashMap
并发安全的 HashMap。JDK7 用分段锁(Segment,16 段);**JDK8 起改为「数组 + 链表/红黑树 + CAS + synchronized 锁单桶头节点」**——锁粒度细化到桶,并发度大增。size 用 LongAdder 思想的 `CounterCell` 分段计数减少竞争;get 全程无锁(volatile 读)。

### 3.1 LinkedHashMap 实现 LRU 缓存
LinkedHashMap 比 HashMap 多维护一条双向链表记录遍历顺序,两个现成特性可直接做 LRU:
- **accessOrder 模式**:构造器 `new LinkedHashMap<>(initialCapacity, loadFactor, accessOrder)` 第三参 `boolean` 默认 `false`(**插入顺序**);传 `true` 则为**访问顺序**——每次 `get`/`put` 命中把该 entry 移到链表**末尾(MRU 端)**,头部即最久未访问(LRU 端)。
- **removeEldestEntry 回调**:`protected boolean removeEldestEntry(Map.Entry<K,V> eldest)`,**每次 put 后自动调用**,入参为当前最老 entry;默认返回 `false`(不删)。重写为 `size() > capacity` 时返回 `true`,框架自动淘汰头节点。

```java
class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;
    LRUCache(int capacity) {
        super(capacity, 0.75f, true);   // 第三参 accessOrder = true
        this.capacity = capacity;
    }
    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;       // 超容量自动淘汰最老 entry
    }
}
```

- **示例**(capacity=3):`put a→[a]`、`put b→[a,b]`、`put c→[a,b,c]`、`get a→[b,c,a]`(a 刷新末尾)、`put d→[c,a,d]`(超容量,最久未访问的 b 被淘汰)。
- **线程安全坑(高频考点)**:accessOrder 模式下 **`get` 也会改链表顺序**(把 entry 挪到末尾),所以并发 LRU 的 `get`/`put` **都要 `synchronized`**——只锁 put 会并发错乱链表。或用 `Collections.synchronizedMap()` 包一层(它对全部操作加同步)。
- **Android 直接用 `android.util.LruCache`**:源码就是「LinkedHashMap(accessOrder) + synchronized」,业务里别自己手撸。两个 hook 要会:`sizeOf(key, value)` 决定**容量单位**(Bitmap 按 KB 限、不重写则按条数限)、`entryRemoved(...)` 是**淘汰回调**(可 recycle Bitmap 等资源)。
- **何时换 Caffeine**:需要 TTL/过期、高并发、LFU/W-TinyLFU 策略或抗「扫描型访问」(一次大批量 get 把热数据挤掉)时,别扩 LinkedHashMap,上 Caffeine。

### 3.2 ConcurrentHashMap 熟练用法:原子复合操作
CHM 保证**单次操作**线程安全,但不保证「检查再操作」的组合原子。核心是四个**原子方法**,它们让 check-then-act 无需外部加锁。
- **经典竞态(❌)**:`if (!map.containsKey(k)) map.put(k, v);`——判断与 put 之间非原子,两线程可都判为 null 后双写覆盖。正解用下方原子方法。

| 方法 | 用途 | 典型场景 |
|---|---|---|
| `putIfAbsent(k, v)` | 仅当 k 不存在时放入,返回旧值 | 单次「缺则塞」 |
| `computeIfAbsent(k, fn)` | 缺时才调 fn 算值并放入 | **懒加载 / 缓存初始化(最高频)** |
| `compute(k, biFn)` | 原子 read-modify-write | 覆盖式更新(自己处理 null) |
| `merge(k, v, biFn)` | 缺则置 v、有则与旧值合并 | **计数 / 聚合(最优雅)** |

```java
// 并发词频统计:一行替代 synchronized + get + put
freq.merge(word, 1, Integer::sum);                 // 缺置 1,有则 +1
// 懒加载缓存:仅缺失时才算(不会重复计算)
cache.computeIfAbsent(key, k -> expensive(k));
```

- **记忆口诀**:懒初始化 → `computeIfAbsent`;计数累加 → `merge`;只在缺时塞 → `putIfAbsent`。
- **三个行为差异坑(与 HashMap 对比)**:
  1. **迭代弱一致**(weakly consistent):遍历不抛 `ConcurrentModificationException`,只反映迭代开始时的某状态,中途新增可能看不到。
  2. **`size()` 是估值**:用 `CounterCell` 分段累加,非强一致,**别拿来精确判断**。
  3. **key/value 都不能为 null**:null 与「不存在」有歧义,`map.put(k, null)` 直接 NPE。

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
- **判定可达(可达性分析)**:从一组叫 **GC Root** 的对象出发,沿引用一路 **trace**,被遍历到的对象(传递闭包)视为「可达 = 存活」,遍历**到不了的**即垃圾。注意 **GC Root 不是「不可回收的引用类型」,而是遍历的起点对象**——它们天然可达。常见 GC Root:
  - 虚拟机栈里**活动帧的局部变量 / 方法参数**(最常见);
  - **静态字段**引用的对象;
  - **常量**引用的对象(运行时常量池);
  - **活动线程**本身;
  - **JNI 全局引用**(native 持有);
  - **`synchronized` 锁**持有的对象;
  - 类加载器 / 关键系统类等。
- **为什么不用引用计数?** 引用计数(被引用 +1、断开 -1,归零即回收)有**致命缺陷——循环引用**:A↔B 互相引用,两者计数永远 ≥1 不归零,但已无外部入口、是彻头彻尾的垃圾。可达性分析从 GC Root trace,**「有引用但不可达」**的对象照样被识别回收——这正是它取代引用计数的原因。
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