---
title: Room 数据库
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-11-25
tags: [Room, SQLite, 数据库]
related: [网络与离线缓存策略]
---

# Room 数据库

## 概述
Jetpack 的 SQLite ORM:用注解(`@Entity`/`@Dao`/`@Database`)定义表与访问,**编译期校验 SQL**。核心是 Dao 的增删改查 + 用 `Flow`/`LiveData` 观察数据变化。进阶:迁移(`Migration`)、事务、类型转换器(`TypeConverter`)、与网络层组合成 Repository 数据源模式(本地 DB + 远程)、复杂查询与索引性能。是「离线优先」架构的本地数据基座。

## 考核记录
（尚未考核）

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