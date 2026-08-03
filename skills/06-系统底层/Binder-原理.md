---
title: Binder 通信原理
domain: 06-系统底层
level: 了解
target: 掌握
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-10
tags: [IPC, 底层]
related: [AIDL]
---

# Binder 通信原理

## 概述
**Binder** 是 Android 跨进程通信(IPC)的基石:系统服务(AMS/WMS/PMS 等)在 `system_server` 或独立进程,App 调它们几乎都走 Binder。它由四部分构成——Client、Server、`ServiceManager`(名称→引用的「DNS」)、以及内核里的 **Binder 驱动**(`/dev/binder`,负责转发)。相比普通 IPC 的两次用户/内核拷贝,Binder 靠 **mmap 把内核缓冲区与接收方用户空间映射到同一物理页**,实现**只需一次拷贝**;配合 AIDL 自动生成的 Stub/Proxy,跨进程调用写起来就像本地方法。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 为什么需要 Binder / IPC

Linux 进程内存隔离:一个进程不能直接读写另一进程的内存。Android 的四大组件、系统服务常跨进程(系统服务在 `system_server`,媒体/输入等在独立进程)。Android 没直接用 Linux 的 pipe/socket/shm,而自研 **Binder**:一次拷贝、自带调用方身份(UID/PID)、面向对象(C/S + 代理)、由内核驱动统一管理。

### 2. 架构与四大角色

- **Client**:调用方,持有 Server 的代理(Proxy)。
- **Server**:服务方,真正的 Binder 实体。
- **ServiceManager**:「DNS」——把服务 name 映射成 Binder 引用(handle),Client 按名查询拿到代理。
- **Binder 驱动**:在内核,是三者之间的转发中枢,所有跨进程数据都经它。

### 3. 一次拷贝(copy-once)原理

- 普通 IPC(socket/pipe):发送方用户态 → 内核态(第一次拷贝)→ 接收方用户态(第二次拷贝)。
- Binder 只拷贝一次:接收方进程启动时 `mmap` 一段内存给 Binder 驱动,这块**内核缓冲区与接收方用户空间映射到同一物理页**。发送方把数据从自己用户态拷进这块内核缓冲区(唯一一次拷贝),接收方用户态就能直接读到——省掉了第二次拷贝。
- 安全:内核驱动控制访问,数据不暴露给第三方。代价:单事务有大小上限(约 1MB)。

Binder 与常见 IPC 机制对比:

| 机制 | 拷贝次数 | 调用方身份 | 特点 / 适用 |
|---|---|---|---|
| **Binder** | **1 次**(mmap) | 自带 UID/PID,不可伪造 | 面向对象 C/S,Android IPC 主力 |
| 共享内存(ashmem) | 0 次 | 无,需自管同步 | 大数据 / 大图,但要自管并发 |
| Socket / pipe | 2 次 | 可查,对端需校验 | 通用、跨用户 / 网络 |
| System V IPC(shm / 消息队列 / 信号量) | 2 次 | — | 老式 IPC,Android 较少用 |

### 4. AIDL 与 Stub/Proxy 代理模式

**AIDL**(Android Interface Definition Language)定义跨进程接口,编译器生成两份代码:

- **Stub**(服务端):继承 `Binder`,实现 `onTransact`——按 code 反序列化参数 → 调真正实现 → 写返回值。
- **Proxy**(客户端):实现接口,把方法调用序列化成 `Parcel` → `transact()` 交给驱动 → 等返回。

Client 拿到的是 **Proxy**,调用看起来像本地方法,实则跨进程——这就是「面向对象的 IPC」。

### 5. Binder 驱动与协议

- 设备节点 `/dev/binder`(另有 `/dev/hwbinder`、`/dev/vndbinder` 分别给 HWBinder / Vendor)。
- 通过 `ioctl` + 命令字通信:`BC_`(Binder Command,用户→驱动)、`BR_`(Binder Return,驱动→用户)。
- 每个进程一个 **binder 线程池**,默认上限 **15** 个线程(外加主线程);并发调用多时排队,耗尽会阻塞。
- binder 节点(node)与引用(ref)用引用计数管理生命周期。

### 6. Service 注册与发现

Server 启动后把自己的 Binder 实体注册到 `ServiceManager`(name → handle);Client 调 `ServiceManager.getService(name)` 拿到 Binder 引用 → 包成 Proxy。`ServiceManager` 本身是个特殊的 Binder 服务(固定 handle=0)。

### 7. 跨进程传对象:Parcel / IBinder / Ashmem

- **Parcel**:扁平化打包基本类型、String、IBinder、Parcelable 对象。
- **IBinder**:跨进程的句柄,传的是引用而非对象本身。
- **大对象**:Binder 单事务约 1MB 上限,大图 / 大 buffer 用 **Ashmem(匿名共享内存)** 或 `MemoryFile`/`FileDescriptor` 传,避免拷贝与超限。

### 8. 死亡通知与安全

- **linkToDeath**:Client 给远端 Binder 注册死亡回调,Server 进程挂了收到通知 → 清理引用(避免持有死引用)。
- **调用方身份**:Binder 驱动每次调用都带上调用方的 **UID/PID**,不可伪造;系统权限校验(`checkCallingPermission` 等)基于此——是 Android 鉴权的基础。

## 实践经验 / 踩坑

1. **oneway 乱序** —— `oneway` 异步调用不保证到达/执行顺序;需顺序就别用 oneway,或拆接口。
2. **主线程同步阻塞** —— 同步 binder 调用等待返回,别在主线程调远程重方法(可能 ANR)。
3. **超 1MB 传输** —— Binder 单事务约 1MB 上限;大数据用 Ashmem / 文件 / ContentProvider。
4. **AIDL 不向后兼容** —— 改/删方法签名坑老客户端;加方法放末尾、注意 versioning。
5. **binder 线程耗尽** —— 并发调用太多排队阻塞(默认 15);排查耗时 binder 调用、减少嵌套。
6. **linkToDeath 未清理** —— 持有已死远端引用或回调未解绑 → 泄漏 / 空指针。

## 待深入 / 下一步
- [ ] 读 Binder 驱动源码(kernel `drivers/android/binder`)
- [ ] 读 `ServiceManager` 注册 / 查询流程
- [ ] 对照 AIDL 生成的 Stub/Proxy 代码

## 参考资料
- 官方 IPC:https://developer.android.com/guide/components/processes-and-threads
- AIDL:https://developer.android.com/guide/components/aidl
- Binder 驱动源码:https://android.googlesource.com/kernel/common/+/refs/heads/android-mainline/drivers/android/binder.c
- Binder(framework API):https://developer.android.com/reference/android/os/Binder
- ServiceManager:`frameworks/native/libs/binder`