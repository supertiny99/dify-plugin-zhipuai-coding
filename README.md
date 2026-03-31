# ZHIPU AI Coding Plan - Dify Plugin

智谱 AI 编码套餐（Coding Plan）的 Dify 模型供应商插件，使用 Coding 专属 API 端点。

## 概述

GLM Coding Plan 是专为 AI 编码场景打造的订阅套餐。本插件使用 Coding 专属端点 `https://open.bigmodel.cn/api/coding/paas/v4`，与通用 API 端点不同。

## 支持的模型

| 模型 | 上下文窗口 | 最大输出 | 说明 |
|------|-----------|---------|------|
| GLM-5.1 | 200K | 128K | 最新旗舰基座，编程能力对齐 Claude Opus |
| GLM-5-Turbo | 200K | 128K | 龙虾增强基座，复杂长任务执行连续性好 |
| GLM-5 | 200K | 128K | 旗舰模型（Max/Pro 套餐） |
| GLM-4.7 | 200K | 128K | 高智能模型，编程更强、更稳 |
| GLM-4.6 | 200K | 128K | 超强性能，高级编码能力 |
| GLM-4.5 | 128K | 96K | 通用模型 |
| GLM-4.5-Air | 128K | 96K | 高性价比模型 |

### 特性支持

- ✅ 流式输出（Streaming）
- ✅ 工具调用（Multi Tool Call）
- ✅ 思维链/推理模式（Thinking / Agent Thought）
- ✅ response_format 结构化输出

## 安装

### 方式一：从 GitHub 安装（推荐）

1. 在 Dify 控制台，进入 **插件** 页面
2. 点击 **Install plugin from GitHub**
3. 输入仓库地址：`https://github.com/supertiny99/dify-plugin-zhipuai-coding`
4. 选择版本 → 选择 `llm-provider.difypkg`
5. 完成安装

### 方式二：上传安装包

1. 从 [Releases](https://github.com/supertiny99/dify-plugin-zhipuai-coding/releases) 下载 `llm-provider.difypkg`
2. 在 Dify 控制台，进入 **插件** 页面
3. 点击 **Upload Plugin** 上传 `.difypkg` 文件

### 方式三：远程调试

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入远程调试地址和密钥
python -m main
```

## 配置

1. 前往 [智谱开放平台](https://open.bigmodel.cn/) 注册账号
2. 订阅 [GLM Coding Plan](https://open.bigmodel.cn/pricing)
3. 获取 [API Key](https://open.bigmodel.cn/usercenter/apikeys)
4. 在 Dify 设置 → 模型供应商中填入 API Key

> **注意**: API 端点默认为 Coding 专属端点 `https://open.bigmodel.cn/api/coding/paas/v4/`，请勿使用通用端点。

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 .env (参考 .env.example)
cp .env.example .env

# 本地调试
python -m main

# 打包
dify plugin package . -o dist/llm-provider.difypkg
```

## 许可

MIT
