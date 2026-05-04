# Notion 知识库配置指南

## 数据库结构

每条思考记录包含以下字段：

| Property 名称 | 类型 | 说明 |
|--------------|------|------|
| 标题 | Title | 思考题前 50 字（自动生成） |
| 问题 | Text | 完整思考题 |
| 回答 | Text | DeepSeek 整理后的你的观点 |
| 信息源 | Multi-select | 关联的新闻来源 |
| 关键词 | Multi-select | AI 提取的核心概念 |
| 日期 | Date | 记录日期（北京时间） |
| 原文链接 | Text | 相关文章 URL |

---

## 第一步：创建 Notion Integration

1. 打开 [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. 点击 **"+ New integration"**
3. 填写：
   - Name: `AI News Bot`
   - Associated workspace: 选择你的工作区
4. 点击 **"Submit"**
5. 复制 **"Internal Integration Token"**（以 `secret_` 开头）
   → 这是 `NOTION_TOKEN`

---

## 第二步：创建 Notion 数据库

1. 在 Notion 新建一个 **Full page database**（全页数据库）
2. 命名为 `AI 思考记录` 或任意名称
3. 按以下添加字段（点击 **+ Add a property**）：

| 字段名 | 类型 |
|--------|------|
| 标题 | Title（默认已有，改名为"标题"） |
| 问题 | Text |
| 回答 | Text |
| 信息源 | Multi-select |
| 关键词 | Multi-select |
| 日期 | Date |
| 原文链接 | Text |

4. 获取数据库 ID：
   - 打开数据库页面，复制浏览器地址栏 URL
   - 格式：`https://www.notion.so/你的名字/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=...`
   - `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` 部分（32位字符）就是数据库 ID
   → 这是 `NOTION_DATABASE_ID`

---

## 第三步：授权 Integration 访问数据库

1. 打开你的数据库页面
2. 点击右上角 **"..."** → **"Connections"**（或 "Add connections"）
3. 搜索并选择 `AI News Bot`（你刚创建的 Integration）
4. 点击确认授权

---

## 第四步：在 GitHub 配置 Secrets

进入仓库 **Settings → Secrets and variables → Actions**，添加：

| Secret 名称 | 值 |
|------------|---|
| `NOTION_TOKEN` | `secret_xxxxxxxxxx`（你的 Integration Token） |
| `NOTION_DATABASE_ID` | 数据库 ID（32位字符） |

---

## 使用流程

配置完成后，每天使用流程如下：

```
09:00  收到 AI 日报（Discord）
       ↓
09:00  收到今日思考题（同一频道）
       ↓
任意时间  在 Discord 回复你的想法
         可以说「参考第2、3条」指定信息来源
       ↓
（等待 discord_handler 下次触发，最多几十分钟）
       ↓
收到 Bot 回复：整理后的观点 + Notion 链接
```

---

## 可用命令

| 命令 | 说明 |
|------|------|
| `!thought` | 重新查看今日思考题 |
| `!push` | 立即推送今日日报（同时生成思考题） |

---

## Notion 未配置时的行为

如果没有配置 `NOTION_TOKEN`，Bot 仍然会：
- 正常发送思考题
- 正常整理你的回复为结构化观点
- 在回复中显示整理结果

只是不会写入 Notion 数据库。配置后立即生效，无需重新推送。
