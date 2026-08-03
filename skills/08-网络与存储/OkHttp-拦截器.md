---
title: OkHttp 拦截器
domain: 08-网络与存储
level: 了解
target: 精通
importance: 中
last_assessed:
last_reviewed: 2026-07-05
next_review: 2026-08-03
tags: [网络, 拦截器]
related: [Retrofit]
---

# OkHttp 拦截器

## 概述
**OkHttp** 是 Android/Java 生态最主流的 HTTP 客户端,也是 **Retrofit 的默认底层引擎**。它把一次网络请求建模成一条**拦截器责任链(Interceptor Chain)**:`Call` 把 `Request` 交给链头,依次穿过重试、桥接(补头)、缓存、连接、真正发包(CallServer),再原路返回 `Response`。这种设计让**横切关注点(日志/鉴权/加密/重试/动态 BaseUrl)都能写成一段拦截器插进链里**、不侵入业务。除拦截器外,OkHttp 还内建**连接池复用、HTTP/2 多路复用、透明 GZIP、响应缓存、异步 Dispatcher 调度**,几乎是一套高性能网络栈的事实标准。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 为什么用 OkHttp / 它解决什么

早期 Android 用 `HttpURLConnection`(或 Apache HttpClient),手写连接管理 / 缓存 / 重试繁琐且坑多。OkHttp 凭 **连接池复用(keep-alive)、HTTP/2·HTTP/3 支持、透明 GZIP 压缩、响应缓存、统一重试/重定向、责任链可插拔拦截器、API 简洁** 成为首选。它是**传输层**客户端——只管把 `Request` 变成 `Response`;上面再叠 Retrofit(注解接口 + 转换)做业务层封装。

### 2. 一次请求的旅程

- `OkHttpClient` 是配置与共享资源的持有者(连接池 / Dispatcher / 拦截器列表),**应全局单例**。
- `client.newCall(request)` 生成 `Call`(实际是 `RealCall`),代表一次可执行请求,**只能执行一次**。
- `call.execute()`(同步,阻塞当前线程)或 `call.enqueue(callback)`(异步,交给 Dispatcher)。
- 最终都进入 `RealCall.getResponseWithInterceptorChain()`:把所有拦截器串成链,链尾拿到 `Response`。

### 3. 责任链是灵魂(核心心智模型)

- `Interceptor` 只一个方法 `Response intercept(Chain chain)`,链上每个节点调 `chain.proceed(request)` 把请求交给下一个、拿到下游返回的 Response 再加工。
- 内置链顺序(从外到内):
  `用户拦截器(addInterceptor)` → `RetryAndFollowUpInterceptor` → `BridgeInterceptor` → `CacheInterceptor` → `ConnectInterceptor` → `网络拦截器(addNetworkInterceptor)` → `CallServerInterceptor`。

![OkHttp拦截器责任链](../考核/okhttp-interceptor-chain.png)

- **关键区别**:
  - `addInterceptor`(**应用拦截器**):在**最外层**,只调一次(含重定向),连缓存命中也经过;适合日志 / 鉴权 / 统计。
  - `addNetworkInterceptor`(**网络拦截器**):在 `ConnectInterceptor` 之后、`CallServer` 之前,**每次真实网络请求都走**(含每次重定向),缓存命中**不走它**;适合看真实报文 / 压缩 / 连接复用。

应用拦截器 vs 网络拦截器对比(高频考点):

| | 应用拦截器 `addInterceptor` | 网络拦截器 `addNetworkInterceptor` |
|---|---|---|
| 链中位置 | 最外层(在 RetryAndFollowUp 之前) | Connect 之后、CallServer 之前 |
| 调用次数 | **整体 1 次** | 每次真实网络请求(含每次重定向) |
| 缓存命中 | **仍会调用** | **不调用**(短路在 CacheInterceptor) |
| 看到的响应 | 重定向后的最终响应 | 每跳原始网络响应(含 gzip) |
| 典型用途 | 鉴权 / 统计 / 离线缓存 / 业务日志 | 真实报文 / 压缩 / 连接复用观测 |

### 4. 五大内置拦截器

- **RetryAndFollowUpInterceptor**:失败重试、跟随重定向(3xx)、认证重试(401);限制最多 20 次跟随,防死循环。
- **BridgeInterceptor**:补全请求头(`Host`/`Connection`/`Accept-Encoding: gzip`/`Cookie`/`User-Agent`)、解压 gzip 响应。
- **CacheInterceptor**:命中缓存直接返回、按 HTTP 缓存语义决定用缓存还是发起条件请求。
- **ConnectInterceptor**:建立 / 复用连接(从连接池取或新建 `RealConnection`、TLS 握手、HTTP/2 协商)。
- **CallServerInterceptor**:链尾,真正把请求写进 socket、读回响应(写头、写 body、解析 status line / headers)。

### 5. 同步 vs 异步 + Dispatcher 调度

- **同步 `execute()`**:阻塞调用线程直接跑拦截器链;别在主线程调(会 ANR)。
- **异步 `enqueue()`**:进 `Dispatcher` 调度:
  - 两个双端队列 `readyAsyncCalls`(待运行) / `runningAsyncCalls`(运行中)。
  - 限额:`maxRequests = 64`(全局并发上限)、`maxRequestsPerHost = 5`(同 host 上限)。
  - 超额的先进 `readyAsyncCalls`;有空位(某请求完成)时按 host 重排后晋升到 `runningAsyncCalls`。
  - 用一个 `ExecutorService`(无界缓存线程池,`SynchronousQueue`)跑,每个 `AsyncCall` 最终以同步方式执行拦截器链。

### 6. 连接池与复用

- 每条 `RealConnection` 是一个 TCP(+TLS)连接,持有 `Socket`;HTTP/2 一条连接可多路复用多个并发流。
- `ConnectionPool` 默认:**最多 5 个空闲连接、keep-alive 5 分钟**,后台清理线程回收超时空闲连接。
- 复用条件:同 `Address`(host / port / dns / 代理 / ssl 等)的空闲连接直接拿来用,省 TCP + TLS 握手——这是 OkHttp 快的核心。
- 自定义 `Dns` / `SocketFactory` / `SSLSocketFactory` / `ProxySelector` 会影响路由选择与连接复用。

### 7. 缓存策略(CacheInterceptor)

- 显式给 `client.cache = Cache(dir, size)` 才生效;基于 **DiskLruCache** 落盘。
- 默认只缓存 GET 且响应头允许缓存的(`Cache-Control` / `Expires`)。
- 命中且未过期 → 直接返回缓存(此时**不进网络层、不触发 `addNetworkInterceptor`**)。
- 过期但有 `ETag` / `Last-Modified` → 发**条件请求**(`If-None-Match` / `If-Modified-Since`),服务器回 304 即用本地缓存,省 body 流量。
- `CacheStrategy` 负责决定「用缓存还是发网络」。

### 8. 自定义拦截器实战 + 为什么 Retrofit 建立在它之上

- 典型自定义:统一加鉴权头、结构化日志(请求 / 耗时 / 状态码)、失败重试 / 限流、请求体加密、动态 BaseUrl。
- 写法:实现 `intercept`,必要时 `val newReq = chain.request().newBuilder()...build()` 再 `chain.proceed(newReq)`。
- **与 Retrofit 关系**:Retrofit 把注解接口(`@GET`/`@POST`)翻译成 `Call`,用 `Converter`(JSON ↔ 对象)和 `CallAdapter`(返回 `Call` / `LiveData` / 协程等)做上层封装,**真正发请求的还是 OkHttp 的拦截器链**——所以在拦截器层加的日志 / 鉴权,对 Retrofit 接口同样生效。

## 实践经验 / 踩坑

1. **拦截器位置选错** —— 应用层日志 / 鉴权用 `addInterceptor`(只一次、含缓存命中);想看真实网络报文用 `addNetworkInterceptor`(每请求、不含缓存命中)。混用导致日志对不上。
2. **Dispatcher 队列满排队** —— `maxRequests=64` / `perHost=5`,接口慢时同 host 请求堆积等待;调大限额或换并发模型,别在它上面无谓阻塞。
3. **`OkHttpClient` 不复用** —— 每次请求 `new OkHttpClient()` 各起连接池 / Dispatcher 线程池,资源泄漏;应全局单例(或按配置少量复用)。
4. **缓存不生效** —— 没给 `Cache` 目录 / 后端没返回 `Cache-Control` / 用了非 GET;且缓存命中也不进 `addNetworkInterceptor`,排查时别看错地方。
5. **`Response.body()` 只能读一次** —— 是一次性流,读完即关;要多次读用 `peekBody()` 或手动缓存(注意大响应的内存)。
6. **责任链断掉** —— 拦截器里忘调 `chain.proceed()`(请求发不出去)、或改了 request 却没把 `newRequest` 传给 `proceed`(改动无效)。
7. **连接复用失败** —— 自定义 SSL / 代理 / DNS 导致每请求新建连接(不明显但握手开销高);确保同 `Address`、别频繁换配置。

## 待深入 / 下一步

- [ ] 读 `RealInterceptorChain` 与 `ConnectInterceptor` 连接建立源码
- [ ] HTTP/2 多路复用在 `RealConnection` 上的实现
- [ ] `CacheInterceptor` 的 `CacheStrategy` 算法细节

## 参考资料

- OkHttp 官网:https://square.github.io/okhttp/
- 拦截器 Wiki(应用 vs 网络拦截器):https://github.com/square/okhttp/wiki/Interceptors
- 源码:https://github.com/square/okhttp
- 缓存 / 连接 API:https://square.github.io/okhttp/4.x/okhttp/okhttp3/-cache/