# AI News Telegram Bot

每日自动抓取 AI 主流资讯，通过 Telegram 推送，并支持通过 Telegram 对话调整推送偏好。

**当前版本：GitHub Actions 简化版**（无需服务器，完全免费）

---

## 功能

- **每日自动推送**：每天北京时间 09:00 推送精选 AI 资讯
- **DeepSeek AI 处理**：自动筛选、翻译、总结为中文
- **Telegram 对话调整**：发送自然语言消息即可调整推送内容
- **多源聚合**：覆盖 Arxiv、HuggingFace、OpenAI Blog、VentureBeat 等主流来源

---

## 快速部署

### 第一步：创建 Telegram Bot

1. 在 Telegram 搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`，按提示创建 Bot
3. 记录获得的 **Bot Token**（格式如 `123456789:ABCdefGhi...`）
4. 搜索 [@userinfobot](https://t.me/userinfobot) 获取你的 **Chat ID**

### 第二步：获取 API Keys

- **DeepSeek API Key**：在 [platform.deepseek.com](https://platform.deepseek.com) 注册获取

### 第三步：配置 GitHub Secrets

在你的 GitHub 仓库页面：**Settings → Secrets and variables → Actions → New repository secret**

添加以下 4 个 Secret：

| Secret 名称 | 说明 |
|-------------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 你的 Telegram Chat ID |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `GH_PAT` | GitHub Personal Access Token（需要 `repo` 权限，用于自动提交配置变更） |

> **GH_PAT 获取方式**：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token，勾选 `repo` 权限。

### 第四步：启用 GitHub Actions

1. 进入仓库的 **Actions** 页面
2. 如提示，点击 **"I understand my workflows, go ahead and enable them"**
3. 第一次可手动触发：点击 **AI 每日资讯推送** → **Run workflow**

---

## 调整推送内容

直接在 Telegram 向 Bot 发送消息：

```
我只想看关于大模型和 AI Agent 的新闻
每次推送改为 10 条
去掉论文类内容，只要行业新闻
帮我关注 AI 安全方向
过滤掉关于图像生成的内容
```

配置会在下一次 GitHub Actions 触发时（最多 15 分钟）自动更新。

**内置命令：**
- `/help` - 查看帮助
- `/config` - 查看当前配置
- `/status` - 检查 Bot 状态

---

## 项目结构

```
.
├── .github/
│   └── workflows/
│       ├── daily_push.yml          # 每日定时推送（UTC 01:00 = 北京 09:00）
│       └── telegram_handler.yml    # 每 15 分钟处理 Telegram 消息
├── src/
│   ├── news_fetcher.py             # 多源新闻抓取
│   ├── ai_processor.py             # DeepSeek AI 处理
│   └── telegram_client.py          # Telegram 消息发送
├── scripts/
│   ├── daily_push.py               # 每日推送主脚本
│   └── telegram_handler.py         # Telegram 命令处理脚本
├── config/
│   ├── user_config.json            # 用户偏好配置（自动更新）
│   └── last_update_id.txt          # 上次处理的消息 ID（自动更新）
└── requirements.txt
```

---

## 自定义推送时间

编辑 `.github/workflows/daily_push.yml` 中的 cron 表达式：

```yaml
- cron: "0 1 * * *"   # UTC 01:00 = 北京 09:00
- cron: "0 0 * * *"   # UTC 00:00 = 北京 08:00
- cron: "30 23 * * *" # UTC 23:30 = 北京 07:30（前一天 UTC）
```

---

## 新闻来源

| 来源 | 类型 |
|------|------|
| Arxiv AI / ML | 学术论文 |
| HuggingFace Blog | 技术博客 |
| OpenAI Blog | 行业动态 |
| Google AI Blog | 行业动态 |
| VentureBeat AI | 行业新闻 |
| The Verge AI | 行业新闻 |
| Hacker News | 社区讨论 |

---

## 升级到 VPS 完整版

如需实时响应 Telegram 消息（无 15 分钟延迟），可将 `telegram_handler.py` 改为 Webhook 模式部署到 VPS，使用 `python-telegram-bot` 的异步框架持续运行。
