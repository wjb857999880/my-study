---
title: Room 数据库
domain: 02-框架与Jetpack
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [Room, SQLite, 数据库]
related: [网络与离线缓存策略]
---

# Room 数据库

## 概述
Jetpack 的 SQLite ORM:用注解(`@Entity`/`@Dao`/`@Database`)定义表与访问,**编译期校验 SQL**。核心是 Dao 的增删改查 + 用 `Flow`/`LiveData` 观察数据变化。进阶:迁移(`Migration`)、事务、类型转换器(`TypeConverter`)、与网络层组合成 Repository 数据源模式(本地 DB + 远程)、复杂查询与索引性能。是「离线优先」架构的本地数据基座。

## 考核记录
（尚未考核）
