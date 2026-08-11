---
title: AI 辅助开发工作流
domain: 07-工程化
level: 了解
target: 精通
importance: 中
last_assessed:
last_reviewed: 2026-07-27
next_review: 2026-11-04
tags: [AI编程, Copilot, Cursor, Claude Code, 提效]
related: [Code Review 与代码质量, CI/CD 流水线与发布, 自动化测试]
---

# AI 辅助开发工作流

## 概述
AI 编程工具已从**行级补全**演进到**自主 Agent**(规划 + 工具调用 + 循环直到完成)。2026 年 JD 普遍把"熟悉 Copilot / Cursor / Claude Code"列为加分项。核心心智:**让 AI 理解项目靠喂足高质量上下文(规则文件 / 记忆 / 技能),而非更大模型**;AI 是 **copilot(副驾)不是 autopilot(自驾)**——人负责目标、权衡、验收,AI 负责机械执行、样板生成、模式套用。提效最显著在"重复 / 样板 / 大范围机械改动",复杂设计仍靠人。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 工具谱系与定位
按"自主程度"从低到高:
- **GitHub Copilot**:IDE 内**行/块补全** + Copilot Chat;Copilot Agent / Workspace 可半自主改多文件、跑命令。生态最广,IDE 集成成熟。
- **Cursor**:**AI 原生编辑器**(VSCode fork),强项是大上下文检索 + **Agent 模式**(Composer / Tab),代码库感知深。
- **Claude Code / Agent SDK**:**命令行自主 Agent**,工具调用 + 长任务循环(读改文件、跑测试、提交),可脚本化、接入 CI;Agent SDK 供二次开发多 Agent。
- **JetBrains AI Assistant**:IDE 内对话 / 补全 / 重构,与 Android Studio 深度集成。
- 定位差异:**补全型**(Copilot Inline、Tab)提效单点;**Agent 型**(Claude Code、Cursor Agent、Copilot Agent)接管多步任务。`vibe coding` 趋势——用自然语言驱动生成,但对生产代码仍需严格把关。

### 2. 上下文工程
模型再强,**上下文不够等于白搭**。
- **上下文窗口**:有限 token,塞太满降速增本;核心信号被稀释 → 回答跑偏。
- **prompt cache**(`缓存命中`):相同前缀复用 KV cache,降本提速;**改文件 / 动前缀即缓存失效**——稳定结构优先。
- **规则文件**:`CLAUDE.md` / `.cursorrules` / `AGENTS.md`,注入项目约定(架构分层、命名、依赖版本、禁区、测试命令、提交规范)。**版本化管理**,团队共享。
- **memory(记忆)**:跨会话持久的事实(用户偏好、决策、踩坑)。
- **skills(技能)**:可复用工作流(如"生成 Repository 模板")。
- 心智:**喂足高质量上下文 > 换更大模型**。

### 3. Agent 与工作流
演进:**补全 → 对话 → 自主 Agent**。
- **自主 Agent** = 规划(拆解目标)+ 工具调用(读改文件 / 执行命令 / 搜索)+ 循环(验证、修正、直到达成停止条件)。
- Agent 关键四要素:**工具集、规划、验证、停止条件**。无验证的 Agent 会跑飞。
- **多 Agent 编排**:并行(多 agent 各管一模块)或流水线(一写实现、一写测试、一 review)。Agent SDK / 子 agent 模式实现。
- **何时用 Agent**:目标明确、可验证的多步任务(迁移、批量重构、补测试);**单轮问答**仍用 Chat(查 API、解释片段)。
- 反模式:**给 Agent 模糊目标 + 无验证 + 无停止条件**(如"重构整个项目")→ 跑飞、改一堆、难回滚。Agent 前先确认"成功长什么样、怎么验证"。

### 4. 落地场景
- **脚手架 / 样板**:生成 Activity / ViewModel / Repository / Composable 模板,Hilt module、Retrofit 接口。
- **重构与迁移**:大范围机械改动(View → Compose、Java → Kotlin、库升级改 API),Agent 跨文件改 + 跑测试验证。
- **写测试 / TDD + AI**:先写失败测试(Red),让 AI 实现(Green),人 Refactor;或反向让 AI 补测试。
- **代码评审与安全审查**:贴 diff 让 AI 找 bug、注入、坏味道;`/code-review`、`/security-review`。
- **文档生成 / 更新**:KDoc、README、变更说明,改完代码顺手更新。
- **调试排错**:贴报错栈 / 失败日志让 AI 定位;`/verify` 跑起来观察。
- **读陌生代码库**:让 Agent 概览架构、解释数据流,快速上手。
- **正则 / 复杂 SQL / 数据转换**:人写易错的领域,描述清楚规则让 AI 出初稿,人验证边界。

### 5. 工程化集成
- **提交规范**:AI 生成代码**同样过 review / CI / 测试**,标准不降;`Co-Authored-By` 标注 AI 辅助。
- **PR 流程**:大改动拆小 PR,每个 PR 单一职责、可独立 review / 回滚;AI 改动也要写清楚"为什么这么改"。
- **CI 接入 AI**:自动 review、依赖 / 安全扫描、PR summary 生成、测试结果解读。
- **人 + AI review**:AI 初筛(机械问题、风格、常见漏洞、漏测边界)+ 人把关(架构、业务正确性、权衡、领域知识)。
- **本地 vs 云 Agent**:敏感代码 / 密钥倾向**本地或私有部署**模型;公开云端便宜但需脱敏,看清厂商数据政策(是否用于训练)。
- 与自动化测试联动:Agent 改完**先跑测试再交付**,失败的测试阻断合入(见 [[自动化测试]]、[[CI-CD流水线与发布]])。

### 6. 风险与红线
- **幻觉**:编造不存在的 API / 类 / 字段 / 库版本。**必须验证**(编译、查文档、跑测试),不可轻信方法签名。
- **隐私外泄**:敏感代码 / 密钥 / 内部数据发云端 → 脱敏或本地模型。
- **开源协议污染**:AI 吐出 GPL / 受限许可证代码混入专有项目,法务风险。审查生成片段来源。
- **盲目接受 → bug / 安全漏洞**:注入、弱加密、过度复杂实现、错误的并发处理。
- **过度依赖**:不读不验,长此以往自身能力退化;调试 / 架构能力需手动维持。
- 红线:**生产密钥不入 prompt**;**安全相关代码(加密、鉴权、输入校验)人必须复核**。

### 7. 提效度量
不能只看**代码量 / commit 数**(易注水、可能引入技术债)。看:
- **代码质量**:可读性、复杂度、测试覆盖。
- **cycle time(交付周期)**:从开工到合并的时间。
- **bug 率 / 返工率**:线上缺陷、PR 打回次数。
- 提效梯度:**机械 / 重复 / 样板 > 阅读 / 调试 > 复杂设计 / 权衡**(后者仍靠人)。
- DORA 指标(部署频率、变更前置时间、变更失败率、恢复时间)是更稳健的团队度量;个体层面警惕"AI 让我写更多代码"的产出错觉。

## 实践经验 / 踩坑
1. **规则文件先写**:项目初始就把 `CLAUDE.md` 写清(架构、命名、禁区、测试命令),省掉反复纠正。
2. **小步快跑**:Agent 任务拆小、每步可验证(跑测试),别一次甩大目标。
3. **幻觉必验**:AI 给的 API / 依赖版本先查官方文档或编译验证,别直接信。
4. **改文件即缓存失效**:稳定上下文结构(规则文件、system prompt 置顶),提升 `缓存命中`。
5. **密钥 / 敏感信息脱敏**:用占位符或本地模型,绝不上传真实凭证。
6. **安全代码人审**:加密、鉴权、SQL / 输入校验,逐行复核,不盲接。
7. **Agent 失控停止**:无明确停止条件 + 无验证 → 跑飞改一堆。设 `verify` 检查点。
8. **生成代码先读再合**:不读就接受 = 把别人的代码合进自己项目;读不懂的部分要么改懂、要么不要。
9. **大改动在分支 / worktree**:Agent 跨文件改易乱,隔离工作区 + 频繁提交,出问题能回滚。
10. **别让 AI 编造依赖**:它会"推荐"不存在的库(`幻觉`),`build.gradle` 加依赖前先到 Maven Central 核实坐标与版本。
11. **保留人工"难点"**:架构决策、并发模型、性能权衡刻意自己先想,AI 只做对照 / 查漏,维持核心能力不退化。

## 待深入 / 下一步
- [ ] Claude Agent SDK 多 Agent 编排实战
- [ ] prompt cache 命中率优化(上下文结构化)
- [ ] CI 接入 AI 自动 review / 安全扫描
- [ ] TDD + AI 工作流落地(见 [[自动化测试]])
- [ ] 本地大模型(Ollama)处理敏感代码
- [ ] `CLAUDE.md` 与 skills 沉淀团队工程约定

## 参考资料
- Anthropic Agent 指南(有效 Agent / multi-agent):https://www.anthropic.com/engineering
- GitHub Copilot 文档:https://docs.github.com/copilot
- Cursor 文档:https://docs.cursor.com
- Claude Code 文档:https://docs.claude.com/claude-code
- JetBrains AI Assistant:https://www.jetbrains.com/ai
- Google DORA 研究(AI 对研发效能影响):https://cloud.google.com/dora