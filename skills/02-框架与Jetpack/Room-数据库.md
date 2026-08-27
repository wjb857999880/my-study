---
title: Room 数据库
domain: 02-框架与Jetpack
level: 精通
target: 精通
importance: 中
last_assessed: 2026-08-27
last_reviewed: 2026-08-27
next_review: 2027-02-23
tags: [Room, SQLite, 数据库]
related: [网络与离线缓存策略]
---

# Room 数据库

## 概述
Jetpack 的 SQLite ORM:用注解(`@Entity`/`@Dao`/`@Database`)定义表与访问,**编译期校验 SQL**。核心是 Dao 的增删改查 + 用 `Flow`/`LiveData` 观察数据变化。进阶:迁移(`Migration`)、事务、类型转换器(`TypeConverter`)、与网络层组合成 Repository 数据源模式(本地 DB + 远程)、复杂查询与索引性能。是「离线优先」架构的本地数据基座。

## 考核记录
- **2026-08-27** 判定：(待考核) → 精通 ✅ ｜ 考官：AI
  - 表现：四档全通。概念讲得清（Room 本质+四大价值）、代码写法标准（实体/DAO/Database + 模糊查询参数化 + InvalidationTracker 原理）、Migration 实施到位（ALTER+CREATE INDEX、identity hash、addMigrations 注册时机、5 条 fallback 风险）、原理深挖到位（SQLite trigger + modification_log、channelFlow + observer、5 维度性能成本决策表）、架构设计完整（SSOT 边界、三条 Repository 链路、TTL 分级、失败按 HTTP 状态码分级、容量治理 + 8 条 trade-off）
  - 依据：从了解直接跨 3 档到精通，无任何档失守；Q4.1 讲到 SQLite trigger 机制与跨进程盲区、Q4.2 给出生产级离线优先文章列表的完整设计含熔断节流与 LRU 保留收藏——超出对「能讲透、做设计」的预期

## 核心原理 / 关键点

### 1. 为什么用 Room / vs 裸 SQLite

裸 SQLite(`SQLiteOpenHelper`)要手写大量样板(建表 SQL、Cursor 解析、线程管理),还容易写错 SQL 直到运行才崩。**Room** 是 Jetpack 的 SQLite ORM:用注解描述表与查询、**编译期校验 SQL**、自动生成样板、返回响应式数据,安全且省代码。

### 2. 三大注解

- `@Entity(tableName=…)`:定义一张表,类字段 = 列(可用 `@ColumnInfo` / `@PrimaryKey` 细化)。
- `@Dao`:数据访问对象,声明增删改查方法(`@Insert` / `@Delete` / `@Update` / `@Query`)。
- `@Database(entities=[…], version=n)`:数据库定义,RoomDatabase 子类,提供 Dao。

### 3. Dao 操作 + 响应式返回

- 增删改:`@Insert` / `@Update` / `@Delete`,可返回 id 或行数。
- 查询:`@Query("SELECT …")`,Room 编译期校验 SQL。
- **响应式**:查询返回 `Flow<T>` / `LiveData<T>`,表数据变化时自动重发,驱动 UI 自动刷新——这是 Room 配合响应式架构的核心。

### 4. 主键 / 索引 / 外键 / TypeConverter

- **主键**:`@PrimaryKey(autoGenerate=true)`。
- **索引**:`@Entity(indices=[Index("name")])`,给查询热点列建索引加速。
- **外键**:`@Entity(foreignKeys=…)`,做表关联与级联(谨慎用,有性能 / 复杂度代价)。
- **TypeConverter**:存非基本类型(如 Date、枚举、自定义对象)时,提供「对象 ↔ DB 类型」转换。

### 5. 事务与并发

- `@Transaction`:把多个操作放一个事务,原子、更快(批量写)。查询返回集合时也建议包事务,保证一致性。
- 并发:SQLite 写串行;Room 默认**禁止主线程访问数据库**(强制放子线程 / 协程),用连接池管理读。

### 6. 数据库迁移

版本升级要改表结构时,提供 `Migration(from, to)` 写 ALTER / 建表 SQL,用 `.addMigrations(mig)` 注册。`fallbackToDestructiveMigration()` 作兜底(直接重建丢数据,**仅开发期或可丢数据场景**)。生产环境务必写 Migration 保数据。

### 7. Repository 模式(本地 + 远程)

官方推荐 **Repository** 作为数据源唯一出口:UI / ViewModel 只认 Repository,Repository 内部决定「取本地 Room 还是请求网络」,网络结果写回 Room,Room 通过 Flow 通知 UI。这就是「单一数据源(single source of truth)」+ 离线优先架构。

### 8. 进阶:性能 / Paging / 加密

- 查询性能:索引、避免 `SELECT *`、分页。
- **Paging3 集成**:`PagingSource` 做数据库分页,配合网络分页实现无限滚动。
- **加密**:`SQLCipher` 给数据库加密,保护本地敏感数据。

## 实践经验 / 踩坑

1. **主线程访问 DB 崩** —— Room 默认禁止主线程 IO;放协程 IO / 子线程。
2. **版本升级不写 Migration** —— 加字段后 version 不匹配崩;写 Migration 或(仅开发)`fallbackToDestructiveMigration`。
3. **查询返回类型选错** —— 不需要响应式却返回 Flow 多余;需要 UI 自动刷新别忘了 Flow / LiveData。
4. **TypeConverter 漏注册** —— 存自定义类型报错;为每种非基本类型提供 converter。
5. **大批量写入不开事务** —— 逐条写慢;`@Transaction` 批量提交。
6. **外键滥用** —— 外键带来级联与性能负担,关系复杂时先想是否真需要。
7. **`SELECT *` 与无索引** —— 大表查询慢;按需选列 + 给过滤 / 排序列建索引。

## 待深入 / 下一步

- [ ] 实战 Repository(本地 Room + 远程网络)+ Flow 自动刷新
- [ ] 接入 Paging3 做数据库分页
- [ ] 用 SQLCipher 加密敏感数据

## 参考资料

- Room 指南:https://developer.android.com/training/data-storage/room
- 保存数据到本地:https://developer.android.com/training/data-storage
- Paging:https://developer.android.com/topic/libraries/architecture/paging

## 四档考核 Q&A（2026-08-27）

### 了解档
**Q：Room 是什么？和直接用 `SQLiteOpenHelper` 相比，核心解决了什么问题？**

A：Room 是基于 SQLite 的抽象层（ORM），用**注解描述表与查询、编译期校验 SQL、自动生成样板代码、返回响应式数据**——相对 `SQLiteOpenHelper` 消除了「手写建表 SQL / Cursor 解析 / 线程管理 / SQL 错到运行时才崩」四大痛点，安全且省代码。本质是「把 SQLite 用 Java/Kotlin 注解 + 编译期生成代码的方式包起来」，让 DB 层能像写普通 DAO 一样写。

---

### 熟悉档
**Q：写一个 `User` 实体（`id` 自增、`name`、`age`），`UserDao` 提供：插入返回 id、查询所有返回 `Flow<List<User>>`、查询所有返回一次性 `List<User>`、`name` 模糊匹配；再写 `@Database` 把 DAO 暴露出去。**

A：

```kotlin
// User 实体
@Entity(tableName = "users")
data class User(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val name: String,
    val age: Int
)

// UserDao
@Dao
interface UserDao {
    @Insert
    suspend fun insert(user: User): Long                                   // 1. 插入返回自增 id

    @Query("SELECT * FROM users")
    fun observeAll(): Flow<List<User>>                                    // 2. 响应式：写操作后自动重发

    @Query("SELECT * FROM users")
    suspend fun getAll(): List<User>                                       // 3. 一次性快照

    @Query("SELECT * FROM users WHERE name LIKE '%' || :name || '%'")     // 4. 模糊匹配（参数化）
    suspend fun searchByName(name: String): List<User>
}

// Database
@Database(entities = [User::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
}
```

关键点：
- 写操作用 `suspend` → 避免阻塞主线程；`insert` 的返回值就是自增 id。
- 响应式走 `Flow` → 底层靠 `InvalidationTracker`，表脏了自动重发。
- 模糊匹配用 `LIKE '%' || :name || '%'` → 既防 SQL 注入又能让 Room 编译器识别为绑定参数（直接字符串拼 `%${name}%` 会被编译器视为可疑字面量）。

---

### 掌握档
**Q：User 需要新增可空 `email` 字段 + 对 email 加唯一索引；写 v1→v2 的 Migration 并注册；说清 Migration 执行时机 + 为什么生产不用 `fallbackToDestructiveMigration`。**

A：

```kotlin
// 1. User 实体改造
@Entity(
    tableName = "users",
    indices = [Index(value = ["email"], unique = true)]   // SQL 中 NULL ≠ NULL，天然允许多行 email=NULL
)
data class User(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val age: Int,
    val email: String? = null
)

// 2. Migration v1 → v2
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE users ADD COLUMN email TEXT")                    // 加可空列
        db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_users_email ON users (email)") // 建唯一索引
    }
}

// 3. Database 升级 + 注册
@Database(entities = [User::class], version = 2)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    companion object {
        fun get(ctx: Context): AppDatabase = Room.databaseBuilder(
            ctx.applicationContext, AppDatabase::class.java, "app.db"
        ).addMigrations(MIGRATION_1_2)        // 关键注册；build() 之后再 add 无效
        // .fallbackToDestructiveMigration() // 调试期可开，**生产严禁**
        .build()
    }
}
```

**为什么分两条 SQL**：`ALTER TABLE ADD COLUMN` 不能顺带建索引；而且 Room 启动时会做 schema **identity hash 校验**——必须让最终 SQLite 结构（表列 + 索引）和 `@Database(version=2)` 生成的预期 schema 完全一致，否则抛 `IllegalStateException: Room cannot verify the data integrity`。

**Migration 执行时机**：第一次拿到 DB 连接那一刻，Room 读 `user_version` → 对比 `@Database.version` → 在同一事务里按版本号顺序跑迁移链 → 全部成功才提交并递增版本。任何一条失败 → 回滚 + 抛异常。多进程场景靠 SQLite 文件锁保证只有一个进程跑迁移。

**为什么生产不用 `fallbackToDestructiveMigration`**：① 用户数据静默清零（涉及 GDPR 合规事故）；② 调试期好用，线上一次漏写就是清库灾难；③ 外部引用（推送 token / 上传草稿）的 rowid 全部作废；⑤ 没有审计日志。生产实践：每升一档配套写 Migration + 用 `MigrationTestHelper` 跑断言测试；紧急时仅 debug build 或特定老版本走 destructive。

---

### 精通档

#### Q4.1（原理深挖）：Flow 响应式是怎么实现的？`InvalidationTracker` 机制？性能成本？什么场景用 Flow 什么场景用一次性 List？

**整体链路**：
`@Query Flow<...>` → 编译期生成 `CoroutineRoom.createFlow(db, tables={...}, callable)` → `channelFlow` 包成冷流 → 内部 `InvalidationTracker.Observer("users")` 注册到 tracker → tracker 检测到 users 表脏 → `Observer.onInvalidated` 唤醒 channelFlow → **重新执行一次 callable**（重打 SQL + 重映射）→ `emit` 新结果。

**InvalidationTracker 机制**：Room 给每个被 Flow / LiveData 跟踪的表自动加 3 个 SQLite trigger（INSERT/UPDATE/DELETE 各一个），写操作触发 trigger 把 `(table_id, invalidated=1)` 写进内存 SQL 表 `room_table_modification_log`。一个 `RefreshRunnable` 在 `queryExecutor` 上自循环：读 log → 跟内存 `AtomicLong[] tableVersions` 对比 → 对版本前进的表遍历所有 `Observer.onInvalidated(...)` → 把 invalidated 清零 → 把自己 post 回去再跑。**关键事实**：只要写经过 Room 同一个 DB 连接（哪怕 `openHelper.writableDatabase.execSQL(...)`），tracker 都响应；绕开 Room 自己新开连接写则不在视野里。

**性能成本 5 维度**：
1. **写放大**：每次写多一条 trigger 写 modification_log，高频批量写入场景成本可见。
2. **轮询开销**：RefreshRunnable 持续在 queryExecutor 上转，几十~几百毫秒一周期，空载 DB 也有 CPU 占用。
3. **每 collector 固定成本**：每个 Flow 在 tracker observers map 里占一项；同表挂 100 个 Flow → 100 次回调 + 100 次重查。
4. **重查成本**：每次 invalidate 重跑 SQL + 重映射，不做 diff；100 万行 JOIN 表一次 invalidate = 整表重算。
5. **写路径同步通知**：Room 的 `_Dao_Impl` 写完后同步调 `tracker.notifyChanges(...)`，相对磁盘写不大但有。

**选型决策表**：

| 场景 | 用 Flow | 用一次性 List |
|---|---|---|
| 表上 0 个收集者 | 基本零成本（但白搭） | ✅ 一次 SQL |
| UI 长生命周期订阅 + 写后还要继续看 | ✅ 收益高 | 需手动 reload |
| 高频写（埋点 / 日志缓冲 / 消息缓冲） | ❌ 写放大 + N 次重查 | ✅ 一次查 |
| 大量同时收集者（one-shot 列表 map observe） | ❌ observers 链表爆炸 | ✅ |
| 大结果集 JOIN | ❌ 整表重算 | ✅ |
| 进程空闲 | ❌ 还在转 RefreshRunnable | ✅ 完全静默 |

**经验法则**：读远多于写 + 结果集不大 + 写完 UI 还要看很久 → Flow；否则一次性快照。**两个工程注意点**：① Flow 不要泄露成热流放进 Application 长生命周期对象（要么 `stateIn(scope, ...)` 让 Room 托管，要么明确知道在干嘛）；② 跨进程写表 Flow 不会即时通知——要么共享 SQLite 连接（`openHelperFactory(SupportFactory)`），要么自己用广播 / ContentObserver 串起来。

#### Q4.2（架构设计）：设计一个**离线优先 + 单数据源**的 `Article(id, title, content, publishedAt, isFavorite)` 文章列表模块——表 + DAO + Repository 三层 + TTL + 降级。

**SSOT 硬约束**：UI 只读 DB；网络只写 DB；DB 不反向读网络。Repository 内存里**不放业务真值**（不写 `MutableStateFlow<List<Article>>(...)`）——只放信号（isRefreshing、error）。UI 写一次订阅代码，剩下全是数据可达性问题而非一致性。

**表结构**：

```sql
CREATE TABLE articles (
    id              TEXT PRIMARY KEY,         -- 服务端主键，不自增
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,             -- 仅详情用
    content_preview TEXT,                      -- 列表渲染用
    published_at    INTEGER NOT NULL,          -- 服务端毫秒时间戳
    is_favorite     INTEGER NOT NULL DEFAULT 0,
    cached_at       INTEGER NOT NULL,          -- TTL 策略支点
    etag            TEXT                       -- 304 加速
);
```

取舍：`id` 用服务端主键——离线写 favorite 不需要先 INSERT 再 UPDATE；`cached_at` 是 TTL 支点（Room 不替你判过期）；列表只投影 `content_preview` 不读 `content`；`etag` 详情 304。

**DAO 形态**：
```kotlin
fun observeArticleList(): Flow<List<Article>>                       // 简洁列表 / 收藏页
fun observeArticleListPaged(): PagingSource<Int, Article>           // 主列表（cursor 分页）
fun observeArticleDetail(id: String): Flow<Article?>                // 详情订阅
suspend fun snapshotArticleDetail(id: String): Article?             // 一次性（同步模块）
suspend fun setFavorite(id: String, favorite: Boolean)
suspend fun upsertAll(articles: List<Article>)                      // 网络回流入口
suspend fun purgeOlderThan(ts: Long): Int                           // 缓存清理
```

**为什么用 Paging 3 而不是 `LIMIT/OFFSET`**：离线优先本地会增删，`OFFSET` 会跳行 / 重读 / 漏读。`PagingSource<Int, Article>` 是「查询定义 + 锚点」工作，DB 变化自动触发 `Pager` 重载，列表与刷新两条线靠 DB 自动汇合。

**Repository 三条链路**：

1. **读链路**：`UI → repo.observePaged() → DAO PagingSource → DB`。Repo 只做薄封装返回 PagingSource，不 filter / sort——避免 UI 看到的列表 ≠ DB 真实列表的真值漂移。
2. **刷新链路**：`refresh()` ① 取 `lastSuccessAt`（SharedPreferences / DataStore，不进 Room 表）② 调 `server.listArticles(cursor=...)` ③ DTO → Entity 映射 ④ `dao.upsertAll(...)` ⑤（可选）`dao.purgeOlderThan(now - TTL)`。**第 4 步是关键**：一行 upsertAll 后 Room 自动标 articles 脏 → 所有 observe 的 Flow 重发 → PagingSource 触发 load() → UI 自动刷新。Repo 内存里不留网络数据。接口要幂等（连点 5 次刷新 = 1 个终态）。
3. **用户写链路**：`toggleFavorite(id)` ① `dao.setFavorite(id, true)` **先改本地立刻可见** ② `api.setFavorite(id)` 异步后台同步；失败入 outbox，下次 refresh / 进程重启时扫表补发。顺序反过来弱网下整屏卡住。

**TTL 分级**：

| 内容 | 本地 TTL | 触发刷新 |
|---|---|---|
| 列表首页 | 5–10 min | 进列表屏 / 下拉 / cached_at 过期 |
| 列表后续页 | 30 min ~ 数小时 | 用户翻到那页 + cached_at 过期 |
| 详情文章 | 数小时 ~ 一天 | 进详情时后台偷拉 |
| 用户私有（收藏） | 不设 TTL | 永远本地权威 |

**失败分级降级**（绝不一锅端抛 error）：
- **HTTP 4xx**（资源不存在 / 无权限）：列表剔除该 ID + 清本地 cache；详情显式提示「文章已删除」，不显示陈旧内容。
- **HTTP 5xx / 超时 / 弱网**：列表顶部 banner「无法更新，下拉重试」+ 旧数据继续可读；详情本地有就继续显，本地无则单独错误态；**不弹 toast**（弱网弹窗打扰）。
- **解析错误 / schema 不匹配**：单条丢弃 + 上报 crash，不影响其他条目——服务端某字段炸了不能让整页白屏。
- **断网（飞行模式）**：列表静默降级只读；用户写操作落本地 + outbox，不报失败。
- **节流 / 熔断**：1 min 内最多 N 次刷新；连续 N 次失败进入 5 min 冷却，期间 `refresh()` 直接走本地——防反复下拉把电耗光。

**容量治理**：按 LRU（基于 cached_at 淘汰）或 `keepLatestN=500`；**`is_favorite=1` 不能淘汰**（否则收藏丢失是退化的 SSOT）；时机：每次 refresh 成功顺手 purge + 单独 WorkManager 周期任务兜底。

**关键 trade-off：**
1. 列表 query **不要 JOIN**——一次 invalidate 绑死多张表，所有表都重查；列表只查 articles 单表。
2. **Cursor 分页而不是 offset**——离线优先几乎只能用 cursor；服务端不返 cursor 也要返 `(published_at, id)` 复合 anchor，客户端用 `WHERE published_at < ? OR (published_at = ? AND id < ?)` 翻页。
3. **详情用 Flow 而不是 suspend**——收藏 toggle 后自动刷新；但同步导出 / 推送这种「读到立刻消费」必须 suspend，避免订阅泄漏。
4. **favorites 用 boolean 字段而不是单独表**——除非业务要支持多收藏夹标签，否则多开一张表纯属制造 JOIN。
5. **网络 / DB / 映射三层拆开**——网络只返 DTO，映射在 Repo（要纯净无副作用），DB 写在 DAO；三层各做一件事才好测试。
6. **过期判定不放 DAO**——DAO 只做「按时间戳过滤的查询」，业务语义留 Repo / UseCase 层，未来切数据源不重写 SQL。