---
title: 混合开发与 WebView
domain: 03-UI
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-27
next_review: 2026-08-26
tags: [WebView, JSBridge, 混合开发, H5, 小程序]
related: [Jetpack Compose, 移动端安全, 性能与稳定性体系]
---

# 混合开发与 WebView

## 概述
混合开发指在 **Native App 内嵌 H5/React/Vue 页面**,让一部分业务(活动页、营销、规则)用 Web 技术栈渲染、其余保留原生。它存在是因为:**利**——动态发版绕过商店审核、跨端复用(Web/iOS/Android 一份)、活动页快速迭代;**弊**——性能/体验差于原生、能力受容器限制、复杂交互成本高。**JSBridge** 是连接两端的通信通道:Native 暴露能力(相机、定位、登录、支付),JS 调用它,再把结果回调回去。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 混合开发定位与选型

- **形态**:H5 / React / Vue 页面跑在 `WebView` 里,通过 JSBridge 调原生能力。
- **利**:动态发版(绕过商店审核)、跨端复用、活动/营销页快速上线、人才/Web 生态复用。
- **弊**:启动慢、滚动/动画体验差、内存高、能力受限、复杂交互(手势、多选)成本高。
- **选型维度**:页面类型(活动/营销适合,核心交互页慎用)、迭代频率(高→H5)、性能要求(高→Native)。
- **vs RN/Flutter**:二者用 **自绘引擎**(RN 映射原生组件、Flutter Skia 自绘),渲染不走 WebView,性能接近原生但仍需桥接调原生 API;H5 混合最轻量、最动态、体验最差。

### 2. WebView 体系

| 组件 | 职责 | 关键回调/方法 |
|------|------|--------------|
| `WebView` | 视图容器,渲染页面 | `loadUrl`、`evaluateJavascript` |
| `WebViewClient` | **页面级**事件 | `shouldOverrideUrlLoading`、`onPageStarted/Finished`、`onReceivedError`、`shouldInterceptRequest` |
| `WebChromeClient` | **浏览器 chrome** | `onProgressChanged`、`onJsAlert/onJsPrompt/onJsConfirm`、`onReceivedTitle`、`onShowFileChooser` |
| `WebSettings` | 配置 | JS 开关、缓存模式、DOM storage、UA、混合内容、缩放 |
| `CookieManager` | cookie 读写同步 | `setCookie`、`flush` |

- **内核**:系统 **Chromium 内核**(各厂商/系统版本不一致,碎片化严重);Android 5.0+ 可用独立更新的 WebView APK。
- `WebSettings` 常开项:`setJavaScriptEnabled(true)`、`setDomStorageEnabled(true)`、`setUseWideViewPort`、`setMixedContentMode`(HTTPS 页面是否允许 HTTP 资源)。

### 3. Native 调 JS 与 JS 调 Native

**Native → JS**:
- `evaluateJavascript(js, callback)`(API 19+):**异步、可拿返回值**,**推荐**。
- `loadUrl("javascript:...")`:会刷新页面、**无返回值**,旧用法。

**JS → Native**(三种主流方式):
- `addJavascriptInterface(obj, "name")`:直接注入 Java 对象,JS 调 `window.name.method()`。**API < 4.2 有远程代码执行漏洞**(反射拿 Runtime 执行任意命令);4.2+ 需在被调方法上加 `@JavascriptInterface` 注解。
- **拦截 scheme / prompt**:`shouldOverrideUrlLoading` 拦自定义 url、`onJsPrompt` 拦 prompt 消息——**JsBridge 主流做法**,绕过 `addJavascriptInterface` 漏洞。
- `postMessage` / `MessagePort`(WebView 与 JS 双向消息通道,适合大数据/流式)。

### 4. JSBridge 设计

- 注入**统一 JS 对象**(如 `window.NativeBridge`),所有原生能力走它。
- JS 调用:把 `命令名 + 参数 + 回调 id` 序列化成消息(走 prompt 或 schema)。
- Native 端拦截 → 解析 → 分发到具体 **handler**。
- 异步结果:Native 用 `evaluateJavascript` 调 `NativeBridge._onCallback(回调id, result)` 回灌。
- **权限校验**:域名白名单(只信任自家域)、敏感 API 二次鉴权(如支付/通讯录)、版本协商(Bridge API 版本号)。

### 5. 性能优化

- **WebView 初始化耗时**(首次创建慢,百毫秒级)→ **预创建 / 池化**复用 WebView 实例。
- **首屏白屏**(DNS + 资源加载)→ **离线包**:预置 HTML/JS/CSS 到本地,`shouldInterceptRequest` 拦截请求本地返回;预加载下一个可能打开的页。
- JS 长任务阻塞渲染 → 拆任务、Web Worker。
- 开启**硬件加速**(`android:hardwareAccelerated="true"`)。
- 内存:每个 WebView 实例约几十 MB,注意复用与及时销毁。

### 6. 混合栈与容器

- **统一容器**:标题栏、加载态、错误态、网络重试统一封装,JS 只关心内容。
- **灰度与降级**:H5 异常 / 加载失败 → 回退 Native 页,保证可用性。
- **小程序容器**:微信/支付宝小程序底层即**增强版 WebView + JSBridge + 双线程模型**——**渲染层 WebView**、**逻辑层 JSCore**,两线程通信经 native 中转,隔离 JS 直接操作 DOM 防止阻塞渲染。
- **多进程隔离**:WebView 跑**独立进程**,OOM/崩溃不拖垮主进程(`android:process=":web"`)。
- 与 **RN/Flutter 混合栈**:多引擎管理、页面栈统一(如 FlutterBoost / 多 FlutterEngine)。

### 7. 安全与坑

- **远程 JS 调 native 接口风险**(中间人/恶意 H5):**域名白名单** + 敏感接口鉴权;`addJavascriptInterface` 漏洞已提。
- **HTTPS 混合内容**:`setMixedContentMode(MIXED_CONTENT_NEVER_ALLOW)` 默认禁 HTTP 资源。
- **内存泄漏**:WebView 持有 Activity → 用 `ApplicationContext` 创建 + `webView.destroy()` + 从父容器 `removeView(webView)` 再销毁。
- **cookie 同步**:`CookieManager.flush()` 持久化(异步 `setCookie` 后别忘)。
- **多窗口**:`supportMultipleWindows(true)` + `WebChromeClient.onCreateWindow` 处理 `target="_blank"`。
- ** onPageFinished 不可靠**:部分场景资源未全加载完就回调,JS 调用需自行判断 ready。

## 实践经验 / 踩坑

1. **addJavascriptInterface 漏洞** —— 低版本注入对象被反射攻击,改用 `onJsPrompt`/schema 拦截式 JsBridge,且 `@JavascriptInterface` 注解不可省。
2. **白屏** —— 首次打开冷启动慢,先预创建 WebView + 离线包 + 骨架屏过渡。
3. **内存泄漏** —— Activity 销毁但 WebView 没释放,LeakCanary 报泄漏;务必 `removeView` + `destroy` + 弱引用。
4. **cookie 丢失** —— 登录态 cookie 没同步进 WebView,需 `CookieManager.setCookie` + `flush`,且注意同步时机(在 `loadUrl` 之前)。
5. **JS 调 Native 时序** —— 页面没 ready 就调 Bridge,得拦 `onPageFinished`/自定义 ready 事件再注入。
6. **碎片化** —— 各厂商 WebView 行为不一致(尤其旧机型),需做特性检测与降级。
7. **重复创建 WebView** —— 每个页面 new 一个 WebView 导致内存暴涨,用池化或单 WebView 容器复用。

## 待深入 / 下一步
- [ ] 读微信 JsBridge / 小程序双线程模型实现
- [ ] 动手写一个 `onJsPrompt` 式 JSBridge(含回调 id、权限校验)
- [ ] 离线包方案:diff 更新、签名校验、`shouldInterceptRequest` 本地返回

## 参考资料
- 官方 WebView 指南:https://developer.android.com/develop/ui/webapps/webview
- `WebSettings`:https://developer.android.com/reference/android/webkit/WebSettings
- `WebView`:https://developer.android.com/reference/android/webkit/WebView
- `addJavascriptInterface` 安全(WebView 安全最佳实践):https://developer.android.com/privacy-and-security/security/webview
- `shouldInterceptRequest`:https://developer.android.com/reference/android/webkit/WebViewClient#shouldInterceptRequest(android.webkit.WebView,%20android.webkit.WebResourceRequest)
