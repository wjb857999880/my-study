---
title: 端侧 AI 与智能端开发
domain: 13-AI与端智能
level: 了解
target: 掌握
importance: 高
last_assessed:
last_reviewed: 2026-07-27
next_review: 2026-08-26
tags: [端侧AI, ML Kit, Gemini Nano, TFLite, 推理优化]
related: [Jetpack Compose, 音视频开发, 移动端安全]
---

# 端侧 AI 与智能端开发

## 概述
**端侧 AI(On-device AI)** 把推理从云端搬到手机本地执行:输入不离开设备,隐私天然可控、无网络往返故**延迟低**、可离线工作、零云端算力成本与流量消耗。代价是受限于端侧**算力/内存/功耗/发热/模型体积**——大模型塞不进、长时间推理会触发温控降频。2026 年 Android 正从操作系统转向**智能系统**:Google I/O 26 把 **Gemini Nano** 定为系统级能力,以 `AICore` 经 Google Play 服务下发(不占系统镜像),叠加 **ML Kit** 开箱能力与 **Google AI Edge** 自定义模型工具链,端侧 AI 已是 Android 工程师的新基建。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 端侧 AI 的定位与价值
云端 vs 端侧的权衡是选型起点。

- **端侧优势**:隐私(数据不出端)、低延迟(无网络往返)、离线可用、零云端成本/流量、可个性化(本地数据可读)。
- **端侧代价**:算力有限(移动 NPU 远弱于云端 GPU 集群)、内存受限(常驻模型挤占 App 预算)、**功耗与发热**(持续推理降频)、模型体积(打包进 APK 或动态下发都重)、更新慢(模型随 App/Play 服务升级,不像云端可随时换)。
- **趋势**:Android 把 AI 下沉到系统层,Google I/O 26 定调「智能系统」——AI 不再是某 App 的功能,而是 OS 级、可被各 App 复用的能力(总结、智能回复、听写、校对)。
- **选型**:开箱通用能力走 ML Kit/Gemini Nano;自有模型走 TFLite/MediaPipe;复杂任务走云端 LLM API;高可用走**端云协同**(端侧小模型兜底 + 云端大模型主路径)。

### 2. ML Kit 开箱即用能力
Google 封装的**免 ML 知识**移动端能力集合,统一 API、多数能力**离线**、通过 **Google Play 服务**下发(不增 APK 体积、随 Play 服务更新)。

- **视觉**:`Text Recognition`(OCR 文字识别)、`Face Detection`(人脸检测)、`Barcode Scanning`(条码/二维码)、`Image Labeling`(图像分类)、`Object Detection`(目标检测)、`Pose Detection`/`Segmentation`(姿态/分割)、`Digital Ink Recognition`(手写识别)。
- **自然语言**:`Language ID`、`Translation`(离线翻译,需下语言模型)、`Smart Reply`(智能回复)、`Entity Extraction`(实体抽取)。
- **优势**:无需 ML 背景、统一 Kotlin/Java API、与 CameraX/Firebase 联动、Play 服务分发。
- **注意**:依赖 Google Play 服务(国内设备/ HMS 环境不可用)、部分模型需首次联网下载、精度低于自训练大模型。

### 3. 端侧大模型:Gemini Nano 与 AICore
系统级端侧 LLM,代表 Android「智能系统」的核心。

- **AICore**:承载 Gemini Nano 的**系统服务**,通过 **Google Play 服务更新**(独立于系统镜像,可平滑升级模型版本),App 以依赖形式接入,按需下载模型而非常驻。
- **Private Compute Core(PCC)**:隔离的数据处理沙箱,端侧 AI 中间数据(输入/输出)不向应用/网络泄露,经**私有计算服务**处理,保证隐私。
- **能力**:文本总结、智能回复、听写转写、校对/改写等系统级 AI 任务。
- **可用性限制**:Android 14+ 起步、**仅特定机型**有 NPU 算力与内存支持;能力受机型/区域/Play 服务版本约束 → **必须做可用性检测 + 降级兜底**。
- **Google AI Edge**:涵盖 Gemini Nano、ML Kit、MediaPipe、TFLite 的端侧 AI 工具链总称,负责从云端到端侧的模型转换与部署。

### 4. 自定义模型部署与推理
自有训练模型上端的标准链路:**训练 → 转换 → 量化 → 推理 → Delegate 加速**。

- **TFLite(TensorFlow Lite)**:端侧推理事实标准。`Converter` 把 `tf`/`keras`(或经 ONNX 从 PyTorch)模型转成 `.tflite` 平面文件;运行时用 `Interpreter` 加载并跑前向。
- **Delegate 硬件加速**:`GPU Delegate`(通用 GPU)、`NNAPI Delegate`(Android 8.1+,走厂商 NPU/DSP,主推)、`CPU`(兜底)。同一模型可按设备能力选 Delegate,推理吞吐差几倍。
- **量化(Quantization)**:权重从 float32 压成 **int8/int4**,模型体积降 4~8 倍、推理快、内存省,代价是**精度下降**;`int8` 训练后量化(`PT2V`)最常用,`int4` 更激进。
- **模型瘦身**:剪枝(pruning,去冗余连接)、蒸馏(distillation,大模型教小模型)、低秩分解。
- **替代推理引擎**:`MNN`(阿里,跨平台、推理快)、`NCNN`(腾讯,移动端优化、无依赖)、`ONNX Runtime Mobile`(微软,多框架模型)、`MediaPipe`(Google,封装常见任务管线:人脸/手势/分割/分类,开箱即用)。

### 5. 大模型对接与 Agent
当任务超出端侧能力,对接云端 LLM 与编排。

- **云端 LLM API**:流式输出走 **SSE**(Server-Sent Events)/chunk 增量渲染;关注 **token 与上下文窗口**管理(超长截断、滑动窗口、摘要压缩),`API key`/凭证**绝不能硬编码进客户端**(走自家后端代理或短期令牌)。
- **Function Calling / Tool Use**:LLM 返回结构化调用意图,客户端执行真实函数(查数据库/开页面/调系统 API)再把结果回灌——端侧是「手」,云端 LLM 是「脑」。
- **RAG(检索增强生成)**:外挂知识库,流程 = 文档切片 → `Embedding` 向量化 → 存**向量库** → 检索相关片段塞进 prompt,缓解幻觉、给最新知识。
- **端云协同**:端侧小模型(快、隐私、离线)先答,置信度低或复杂请求再上云端大模型;端侧负责 Embedding 检索/初步分类,云端负责生成。
- **Agent 编排**:多步规划 + 工具调用 + 记忆;移动端通常作为执行体(权限/系统能力)而非推理核心。

### 6. 工程化(下发、调度、降级、合规)
端侧 AI 的工程难度往往在模型本身之外。

- **模型下发与版本**:大模型不打进 APK(撑爆体积),走**首次启动/按需下载 + CDN**,带**版本号与灰度**;旧版本与新模型需兼容判断;模型校验完整性防篡改。
- **推理线程**:绝不阻塞主线程;用**专用线程或协程 Dispatcher**(`Dispatchers.Default` 或自建单线程),**并发限制**(同一模型 Interpreter 非线程安全时需串行或池化多实例)。
- **内存峰值**:模型常驻 vs 用完释放的权衡(常驻省加载耗时但占内存);大模型加载前后配对 `close()`/释放;警惕**温控降频**(持续推理触发系统限频,延迟反而上升)。
- **输入预处理耗时**:resize/归一化/向量化的开销可能超推理本身,要复用对象、避免 GC 抖动。
- **降级兜底链**:机型不支持(无 NPU/Android 版本低)→ 模型未下载 → 推理失败 → 超时 → 回退到云端 API 或纯规则,每一层都要有兜底。
- **埋点**:推理耗时分布(P50/P99)、成功率、 Delegate 命中、降级触发率、电量影响——模型上线后这些比精度更重要。
- **合规**:用户数据上端侧仍需告知;权限(相机/麦克风/存储)按需申请;隐私政策声明数据去向。

### 7. 典型场景
- **图像识别**:商品识别/地标识别/内容审核/拍照翻译(OCR + 翻译)。
- **语音**:实时语音转写 ASR、TTS 朗读、声纹/唤醒词。
- **AR + AI**:ARCore 叠加实时目标检测/姿态估计/场景理解。
- **智能搜索/摘要**:本地相册语义搜索、长文本总结(Gemini Nano)、智能回复。
- **个性化推荐**:端侧用户行为 Embedding,隐私不出端。
- **交互**:手势识别、手写识别、表情驱动。

## 实践经验 / 踩坑
- **主线程推理**:把 `Interpreter.run()` 写在主线程 → 直接 ANR。一律丢专用线程/协程,并设超时。
- **模型打进 APK**:几十 MB 的 `.tflite` 直接塞 `assets`,包体积爆炸 + 首启慢。改按需下载 + 版本管理。
- **Delegate 漏兜底**:只写了 NNAPI,在无 NPU 设备上崩。需 try-catch 逐级回退 NNAPI → GPU → CPU。
- **量化精度翻车**:直接 int8 量化未做校准,某些类别精度暴跌。量化前跑代表性数据集做校准验证,保留 float 版对比。
- **同一 Interpreter 多线程并发**:多协程共享一个 `Interpreter` 导致结果错乱或崩溃。要么串行排队,要么按并发数建实例池。
- **端侧大模型可用性假设**:假设 Gemini Nano 全机型可用 → 大量设备走降级。务必运行时查可用性再决定路径。
- **API key 泄露**:LLM `API key` 直接写进客户端 → 被反编译盗用。走自家后端代理,客户端只持短期令牌。

## 待深入 / 下一步
- [ ] 用 MediaPipe Tasks 跑一个手部/人脸检测 Demo,体验开箱管线
- [ ] TFLite 完整链路:训一个模型 → 转 `.tflite` → int8 量化 → NNAPI Delegate
- [ ] 接入云端 LLM API,实现流式 SSE + Function Calling 调本地能力
- [ ] 端云协同 Demo:端侧小模型预分类 + 云端大模型生成
- [ ] 推理埋点体系:耗时 P50/P99、Delegate 命中率、降级率

## 参考资料
- ML Kit 官方:https://developers.google.com/ml-kit
- Google AI Edge(端侧 AI 工具链总览):https://ai.google.dev/edge
- AICore / Gemini Nano(端侧大模型):https://developer.android.com/ai/aicore
- Android 上的 AI 总览:https://developer.android.com/ai
- TensorFlow Lite 官方:https://www.tensorflow.org/lite
- Android NNAPI:https://developer.android.com/ndk/guides/neuralnetworks
