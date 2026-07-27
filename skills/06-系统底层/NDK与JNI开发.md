---
title: NDK 与 JNI 开发
domain: 06-系统底层
level: 了解
target: 熟悉
importance: 中
last_assessed:
last_reviewed: 2026-07-27
next_review: 2026-08-26
tags: [NDK, JNI, CMake, Native, Rust]
related: [音视频开发, 移动端安全, Binder 通信原理]
---

# NDK 与 JNI 开发

## 概述
**NDK**(Native Development Kit)让 Android 用 C/C++ 写 native 库、编译成 `.so`,经 **JNI**(Java Native Interface)被 Java/Kotlin 调用。JNI 是 JVM 规范定义的桥梁,ART(而非 Dalvik)在运行时把 `native` 方法调用路由到 `.so` 里导出的符号。**何时用**:CPU 密集型(图像/音视频编解码/加密/游戏)、复用已有 C/C++ 库(OpenSSL/FFmpeg/SQLite)、核心逻辑 native 化增加逆向门槛。**何时不该用**:一般业务代码——收益小,且带来体积增大、调试困难、GC 管不到的 native 内存泄漏。NDK 不是「写 Android 的更快方式」,而是「在必要处下沉到 native」的工具。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. NDK 定位与适用场景

- **NDK 是什么**:一套工具链(clang/llvm、CMake、gabixx STL、调试器 LLDB)+ 一组**稳定 API**(在 `minSdkSupported` 范围内跨版本可用的 `<android/log.h>`、`<android/asset_manager.h>`、`<jni.h>` 等)。把 C/C++ 源码编译成各 ABI 的 `.so`,打包进 APK。
- **适用**:CPU 密集(图像滤波、音视频编解码、AES/RSA 加密、物理引擎、游戏);**复用成熟 C/C++ 库**(OpenSSL、FFmpeg、SQLite、libyuv);**反逆向**(把授权/计费/安全校验下沉 native,配合 ollvm 混淆)。
- **不适用**:常规业务(网络/DB/UI)——收益微小,代价是**体积↑、调试难、GC 管不到的内存、跨 ABI 维护成本**。能用 Kotlin 解决就别下沉。

### 2. JNI 机制与 native 方法注册

- **调用链**:Kotlin/Java 声明 `external fun` / `native` 方法 → ART 经 JNI 找到 `.so` 中对应函数 → 执行 → 结果 marshal 回 Java。
- **导出符号**:C++ 需 `extern "C"`(关掉 name mangling)+ `JNIEXPORT`(visibility)+ `JNICALL`(调用约定):
  ```cpp
  extern "C" JNIEXPORT jstring JNICALL
  Java_com_example_Foo_bar(JNIEnv* env, jobject thiz) { ... }
  ```
- **注册方式**:
  - **静态注册**:按命名约定 `Java_包_类_方法`(`.`→`_`、`_`→`_1`)自动绑定,首次调用按名查找;简单但名字暴露、首次有查找开销。
  - **动态注册 `RegisterNatives`**:`JNI_OnLoad` 里显式给 `JNINativeMethod[]` 数组(Java 方法名 + 签名 + C 函数指针);可任意命名(配合混淆更安全)、首次更快、可控;推荐生产用。
- **类型映射**:`jint`/`jlong`/`jboolean`/`jobject`/`jstring`/`jbyteArray`/`jclass`;基本类型直接传,对象类型走引用。
- **方法签名**(JNI descriptor):`(参数描述符)返回描述符`,如 `(Ljava/lang/String;[BI)V` = `void f(String, byte[], int)`;`I`=int、`J`=long、`Z`=boolean、`Ljava/lang/String;`=String、`[`=数组。用 `javap -s` 生成。
- **字符串/数组访问配对**:`GetStringUTFChars` ↔ `ReleaseStringUTFChars`、`GetByteArrayElements` ↔ `ReleaseByteArrayElements`(带 `JNI_ABORT`/`JNI_COMMIT` 模式);忘 Release 会拷贝泄漏或锁死。

### 3. 引用管理与 JNIEnv 线程亲和

- **局部引用 Local Reference**:`FindClass`/`NewObject`/`CallObjectMethod` 返回的、函数内临时引用,**方法返回时自动释放**;但**长循环/递归里会堆积**,需手动 `DeleteLocalRef`,否则 Local Reference Table 溢出(典型报错 `JNI ERROR (app bug): local reference table overflow (max=512)`)。
- **全局引用 GlobalRef**:`NewGlobalRef` 创建,跨方法/跨线程持有,手动 `DeleteGlobalRef` 释放;常用于缓存 `jclass`(`FindClass` 返回的是局部引用,要长期持有必须升级成全局)。**弱全局引用** `NewWeakGlobalRef` 不阻止 GC 回收。
- **引用泄漏** = native 长期持有 Java 对象的全局引用 → GC 永远回收不掉 → 内存泄漏;生命周期结束务必 `DeleteGlobalRef`。
- **JNIEnv 线程亲和**:`JNIEnv` **不能跨线程**,每线程一个。native 创建的线程要 Java 交互须 `JavaVM`→`AttachCurrentThread`(拿到该线程 Env)→ 干活 → `DetachCurrentThread` 退出前 detach;Java 调入的线程自带 Env 无需 attach。漏 detach 会泄漏 TLS 且 ART 报警告。

### 4. 构建与 ABI

- **CMakeLists.txt** + `android { externalNativeBuild { cmake { ... } } }`;`find_library(log LIB_LOG)` 拿 `__android_log_print`。
- **ABI**(应用二进制接口,与 CPU 指令集+调用约定绑定):
  - `arm64-v8a` —— **当前主流**,64 位 ARM,几乎所有真机。
  - `armeabi-v7a` —— 老 32 位 ARM,部分低端/老机。
  - `x86` / `x86_64` —— 模拟器为主。
  - `armeabi`(无 v7a)、`mips` —— **已废弃**,NDK r17 起移除。
- **降体积**:
  - **ABI splits**:按架构分包,每 ABI 一个 APK(老做法)。
  - **App Bundle** 上传后 Google Play **按设备 ABI 自动分发**(更省);国内多渠道走 splits。
  - 编译期优化:`-Oz`(体积优先)、`-flto`、`strip` 符号(Release 默认 strip)、`-ffunction-sections -fdata-sections` + `--gc-sections`、剔除未用代码。
- **STL 选择**:`c++_shared`(动态链接 `libc++_shared.so`,多 .so 共享省内存,但要打包进 APK)vs `c++_static`(静态,单 .so 体积大但无依赖)。多 native 模块用 `c++_shared`。
- **NDK 版本 ↔ minSdk**:NDK 有**最低支持 minSdk**(r23+ 是 API 21+);低于则用旧 NDK。`ANDROID_PLATFORM` 指定。

### 5. 异常与崩溃

- **Java 异常**:native 调 Java 方法可能抛 Java `Exception`;但 native **不会**自动跳转,需 `ExceptionCheck()`/`ExceptionOccurred()` 检查、`ExceptionClear()` 清掉,然后**立即 return**(不能在 pending exception 时继续调 JNI,行为未定义)。
- **native 崩溃 = 信号**:`SIGSEGV`(段错误/空指针)、`SIGABRT`(assert/abort)、`SIGBUS` —— **不走 Java try/catch**,进程被杀。
- **排查工具链**:
  - **tombstone**:系统在崩溃时把栈落盘(`/data/tombstones/`),含寄存器、backtrace、fault address。
  - **addr2line**:`$NDK/toolchains/llvm/prebuilt/.../bin/llvm-addr2line -e libxxx.so -f -C -i <PC 地址>` 把崩溃 PC 还原成源码 `函数:行号`(前提:用未 strip 的 `.so` 或保留 debug 符号)。
  - **ndk-stack**:`adb logcat | ndk-stack -sym obj/local/<abi>/`,自动把 native 栈符号化。
  - **LLDB**:AS 里 Native 调试器,断点/单步。
- **崩溃上报**:Bugly/xCrash 等捕获信号、读 `/proc/self/maps` 找 `.so` 基址,把 PC `偏移地址` 上报;符号表要**单独存档**(构建时保留 unstripped `.so`)。
- **区别**:Crash = 进程被杀的 native/Java 致命错误;ANR = 主线程长时间无响应(5s 输入超时),不杀进程但弹「等待/关闭」。

### 6. Rust 进 Android

- **为什么 Rust**:无 GC 的内存安全(所有权 + 借用检查)+ 数据竞争无内存安全(无 `data race`)、与 C ABI 兼容、AOSP 已大量引入(蓝牙、Keystore、Binder 等)。新 native 模块优选。
- **桥接方案**:
  - **jni-rs**:直接调 JNI,Rust 写 native 方法,灵活但要手写 JNI 引用管理。
  - **cxx**:Rust ↔ C++ 安全互操作,生成头文件,**只暴露安全子集**,适合与已有 C++ 共存。
  - **UniFFI**:Mozilla 出,从 Rust 接口**生成 Kotlin/Swift/Python 绑定**,适合做跨平台 SDK。
- **选择**:全新模块优先 Rust;老 C++ 库继续 JNI/Rust cxx 渐进替换。
- **交叉编译**:配 `cargo-ndk` + NDK target(`aarch64-linux-android` 等),输出 `.so` 走标准 JNI 加载或 cxx。

### 7. 性能与踩坑

- **JNI 调用有开销**:Java↔native 边界切换 + 参数 marshal(jstring 要拷/转编码、jarray 要 pin/拷贝);**不要在热路径里来回频繁横跳**(如每像素调一次 native)——批量传数组进 native 处理完再返回。
- **缓存 ID**:`GetMethodID`/`GetFieldID`/`GetStaticMethodID` 是**查表操作**(慢),务必缓存成 `static jmethodID`(配合全局 `jclass`)。每次调方法现查是经典性能坑。
- **别在 native 长期持有 Java 引用**:要持有用 `NewGlobalRef`,且严格管理生命周期;否则 GC 回收不掉 → 泄漏,或被 GC 后变野指针 → 崩溃。
- **忘 ExceptionCheck**:调 Java 方法后没检查异常就继续 → 未定义行为(可能崩、可能静默错误)。
- **native 线程忘 detach**:`AttachCurrentThread` 后没 `DetachCurrentThread` → TLS 泄漏、退出时 ART 警告。用 `pthread_key_create` 注册析构或 RAII 包装。
- **Release 不配对**:`Get...Elements` 没 `Release...` → 数据不写回 / 内存泄漏;`GetStringUTFChars` 没 `ReleaseStringUTFChars` → 同上。
- **FindClass 缓存陷阱**:`FindClass` 在 `JNI_OnLoad` 里用 `FindClass(env, "com/x/Foo")` 能找到(此时有类加载器上下文);但在某些 native 线程里 `FindClass` 会失败(类加载器不同)——所以**缓存 `jclass` 全局引用**而非每次 Find。

## 实践经验 / 踩坑

1. **Local Reference 溢出** —— 大循环里 `NewStringUTF`/`NewObject` 不释放 → `local reference table overflow`;循环内 `DeleteLocalRef`。
2. **缓存忘升级全局引用** —— `static jclass` 存了局部引用,方法返回后被回收 → 野指针;`NewGlobalRef` 升级。
3. **热路径横跳** —— 每帧每像素调 native → marshal 开销爆;传 `ByteBuffer`/数组指针批量处理。
4. **动态注册名混淆** —— 用 `RegisterNatives` 后混淆 native 方法名,反编译 Java 看不到真实符号;静态注册名暴露。
5. **崩溃没符号** —— Release strip 后线上 tombstone 只有地址 → 必须存档 unstripped `.so` 才能 addr2line。
6. **c++_static 重复** —— 多个 native 模块各 `c++_static` 链 STL → 体积/冲突;统一 `c++_shared`。

## 待深入 / 下一步

- [ ] 手写一个 CMake + JNI 小工程(动态注册 + 全局引用缓存)
- [ ] 实践 addr2line / ndk-stack 符号化一次崩溃
- [ ] 试用 cxx 或 jni-rs 写一个 Rust native 模块
- [ ] 读 JNI 规范的引用与信号章节

## 参考资料

- NDK 官方:https://developer.android.com/ndk
- JNI 指南:https://developer.android.com/training/articles/perf-jni
- JNI 规范:https://docs.oracle.com/en/java/javase/17/docs/specs/jni/index.html
- CMake + NDK:https://developer.android.com/studio/projects/gradle-external-native-builds
- ABI 管理:https://developer.android.com/ndk/guides/abis
- Rust 进 Android(cxx):https://github.com/dtolnay/cxx
