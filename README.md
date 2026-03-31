# ZHIPU AI Coding Plan - Dify Plugin

智谱 AI 编码套餐的 Dify 模型供应商插件，使用 Coding 专属 API 端点。

## 概述

GLM Coding Plan 是专为 AI 编码场景打造的订阅套餐。本插件使用 Coding 专属端点 `https://open.bigmodel.cn/api/coding/paas/v4`，与通用 API 端点不同。

## 支持的模型

| 模型 | 上下文窗口 | 说明 |
|------|-----------|------|
| GLM-5.1 | 200K | 最新旗舰基座，编程能力对齐 Claude Opus |
| GLM-5-Turbo | 200K | 龙虾增强基座，复杂长任务执行连续性好 |
| GLM-5 | 200K | 旗舰模型（Max/Pro 套餐） |
| GLM-4.7 | 200K | 高智能模型，编程更强、更稳 |
| GLM-4.6 | 200K | 超强性能，高级编码能力 |
| GLM-4.5 | 128K | 通用模型 |
| GLM-4.5-Air | 128K | 高性价比模型 |

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
```
