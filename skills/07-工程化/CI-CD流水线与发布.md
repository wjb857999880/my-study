---
title: CI/CD 流水线与发布
domain: 07-工程化
level: 了解
target: 精通
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-11-06
tags: [CI, CD, 发布]
related: [Gradle 构建配置, 自动化测试]
---

# CI/CD 流水线与发布

## 概述
把构建-测试-发布自动化:**CI**(每次提交自动构建 + 跑测试 + 静态检查,GitHub Actions / GitLab CI / Bitrise)、**CD**(自动打包、签名、分发到测试渠道 / 商店)。流水线串联:代码提交 → Lint + 单测 → 构建 APK/AAB → 签名 → 内测分发(Firebase / 蒲公英)→ 灰度 → 商店发布。配合质量门禁(测试通过率、包体积阈值)与产物管理。提升交付速度与质量一致性。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. CI/CD 概念与价值
- **CI(持续集成)**:每次代码提交自动**构建 + 跑测试 + 静态检查**,尽早发现集成问题。核心是「频繁集成、自动验证」。
- **CD(持续交付 / 部署)**:自动**打包、签名、分发**,把通过验证的产物送到测试渠道 / 商店,甚至自动发布。
价值:缺陷左移(早发现)、交付可重复(同一产物从构建到发布)、释放人工打包时间、质量门禁强制一致。

### 2. 典型 Android 流水线阶段
`代码提交 → 检出 → 装 JDK/Android SDK → 缓存 → Lint/Detekt 静态检查 → 单元测试 → 构建 APK/AAB → 签名 → 上传产物 →(分发:内测 / 灰度 / 商店)`。前半段是 CI(每次提交),后半段(签名 + 分发)是 CD(发版触发)。失败应在最早阶段快速失败。

### 3. GitHub Actions 工作流配置
`.github/workflows/ci.yml`,关键步骤(setup-java + setup-gradle):

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'        # AGP 8.x 要求 JDK 17+
      - uses: gradle/actions/setup-gradle@v3   # 管理缓存
      - run: ./gradlew assembleDebug test lint
      - uses: actions/upload-artifact@v4
        with: { name: apk, path: app/build/outputs/apk/**/*.apk }
```

触发(`on:`):PR 上跑检查、push 到 main 上构建分发。

### 4. 缓存与提速
Gradle 构建慢、CI 额度有限,缓存是刚需:
- **`gradle/actions/setup-gradle`**:自动管理 Gradle 依赖与配置缓存(取代旧 `setup-java` 的 `cache: 'gradle'`)。
- **Gradle 配置缓存(configuration cache)**:复用配置阶段结果,提速明显(CI 上有坑,需逐步适配)。
- **构建缓存(build cache)**:同输入复用任务输出;可上**远程构建缓存**让全团队 / CI 共享。
- **`concurrency`**:同分支新提交时取消旧的进行中 run,省额度:

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

### 5. 静态检查与质量门禁
CI 内挂静态分析,把问题挡在合入前:**Android Lint**(官方,资源 / API / 性能问题)、**Detekt**(Kotlin 代码风格 / 坏味道)、**ktlint**(格式)、**SonarQube**(综合质量)。配合 PR 上的必过检查(branch protection),不达标不准合入——否则 CI 形同虚设。

### 6. 构建、签名与产物管理
- **产物**:CI 构建出 APK(测试分发)与 AAB(商店发布);用 `actions/upload-artifact` 存档,供后续步骤或人工下载。
- **签名**:发布包必须正确签名。Debug 用默认调试签名;Release 用正式 keystore。
- **变体**:发版跑 `assembleRelease` / `bundleRelease`,注意混淆 / R8 只在 release 生效——别用 debug 包验证体积 / 混淆。

### 7. 分发与发布
- **内测分发**:Firebase App Distribution / 蒲公英 / TestFlight(iOS),CI 自动上传给测试人员。
- **商店发布**:**Gradle Play Publisher** 插件直接从 CI 上架 Google Play(内部 / 封闭 / 开放 / 生产分轨道);或调 Play Developer API。
- **灰度发布**:按比例放量,配合服务端开关逐步放大,便于及时回滚。
- **AAB + Dynamic Delivery**:商店按设备下发所需 ABI / 分辨率,减小安装体积(见 [[包体积优化]])。

### 8. 密钥与机密管理
签名密钥、API token、服务账号 JSON **绝不进仓库**:
- 用 GitHub **Encrypted Secrets**(仓库设置加密,workflow 里 `${{ secrets.X }}` 引用)。
- 签名 keystore 作为 secret / artifact 注入,构建后不留存。
- 服务账号(Play 发布用)JSON 存 secret,注意权限最小化。
泄露的签名密钥能让攻击者发布「同包名」恶意更新——是最严重的安全风险之一。

## 实践经验 / 踩坑

1. **JDK 版本**:AGP 8.x **要求 JDK 17+**,CI 写 java-version 11 会构建失败。版本要和本地一致(17 或 21)。
2. **不开缓存**:每次重下依赖、重跑配置,CI 又慢又费额度。务必用 `gradle/actions/setup-gradle`。
3. **签名密钥提交进仓库**:一旦 push 到远端即视为泄露,需轮换。用 secrets 注入;历史里有的也要清。
4. **无 concurrency group**:快速连推会触发多个相同 workflow 并行,白烧额度。加 `cancel-in-progress`。
5. **debug 当 release 验收**:debug 不混淆、不压缩资源,体积 / 行为与线上不同。发版指标必须用 release 构建。
6. **检查不强制**:CI 跑了但不阻断合入 = 没跑。开 branch protection 让必过检查成为门槛。
7. **secrets 误打印**:workflow 日志可能泄漏注入的值;敏感步骤关掉日志回显,token 用后即弃。

## 待深入 / 下一步
- [ ] Gradle 配置缓存在 CI 的适配坑
- [ ] 远程构建缓存(remote build cache)搭建与共享
- [ ] AAB + Play App Signing(Google 托管上传密钥)与 Dynamic Delivery
- [ ] 多 flavor / build variant 的矩阵构建与产物分流
- [ ] 自动化发版与版本号管理(fastlane / 发布脚本)

## 参考资料
- GitHub Actions 构建 Gradle:https://docs.github.com/actions/use-guides/building-and-testing-java-with-gradle
- actions/setup-java:https://github.com/actions/setup-java
- gradle/actions/setup-gradle:https://github.com/gradle/actions
- Gradle Play Publisher:https://github.com/Triple-T/gradle-play-publisher