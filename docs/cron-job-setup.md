# cron-job.org 配置指南

## 为什么需要外部触发器

GitHub Actions 的 `schedule`（cron）触发在免费仓库上极不可靠：
- 实测平均延迟 86 分钟（设定 15 分钟）
- 高峰期可能 5 小时无触发
- 整点附近经常被跳过

解决方案：用 **cron-job.org**（免费）在精确时间调用 GitHub API，
触发 `workflow_dispatch`。这和你手动点"Run workflow"效果完全相同，
但完全自动、准时。

---

## 第一步：获取 GitHub Personal Access Token

1. 打开 GitHub → 右上角头像 → **Settings**
2. 左侧最底部 → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token (classic)**
5. 填写：
   - Note: `cron-job-trigger`
   - Expiration: `No expiration`（或 1 year）
   - Scopes: 勾选 `repo` → `workflow`
6. 点击 **Generate token**，复制保存（只显示一次）

> 如果已有 `GH_PAT`，可以直接复用同一个 token（需有 `workflow` 权限）。

---

## 第二步：注册 cron-job.org

1. 打开 [cron-job.org](https://cron-job.org)
2. 注册免费账号（邮箱即可）
3. 登录后进入 **Dashboard**

---

## 第三步：创建定时任务

点击右上角 **CREATE CRONJOB**，按以下填写：

### 基本设置

| 字段 | 值 |
|------|---|
| Title | `AI News Bot 每日推送` |
| URL | `https://api.github.com/repos/Jaqchan99/cloud_agents/actions/workflows/daily_push.yml/dispatches` |
| Request method | **POST** |

### Headers（点击 "ADVANCED" 展开）

添加以下两个 Header：

| Header Name | Header Value |
|-------------|-------------|
| `Authorization` | `Bearer 你的GitHub_TOKEN` |
| `Accept` | `application/vnd.github+json` |
| `Content-Type` | `application/json` |
| `X-GitHub-Api-Version` | `2022-11-28` |

### Request Body

```json
{"ref": "main"}
```

### 执行时间

点击 **Schedule** 选项卡：

- 选择 **"Custom"（自定义）**
- Minute: `0`
- Hours: `1`（UTC 01:00 = 北京 09:00）
- Days of month: `*`
- Months: `*`
- Days of week: `*`

> 也可以在"Simple"模式选 **Daily**，时间选 `01:00`（UTC）

### 其他设置

- **Timezone**: 选 `UTC`
- **Request timeout**: 30 seconds
- **On failure**: 勾选发邮件通知

---

## 第四步：保存并测试

1. 点击 **CREATE** 保存
2. 在任务列表找到刚创建的任务
3. 点击 **Run now** 手动触发一次测试
4. 去 GitHub Actions 页面确认是否出现了新的运行记录

---

## 触发后的流程

```
每天 UTC 01:00
cron-job.org（100% 准时）
    ↓ HTTP POST
GitHub API（workflow_dispatch）
    ↓
daily_push.yml 运行
    ↓
推送天气 + AI 早报到 Discord
    ↓
写入 last_push_date.txt（防重复）
```

discord_handler（每 15 分钟）作为备用守卫：
若 cron-job.org 当天未成功触发（网络问题等），
discord_handler 在北京时间 08:00-23:00 内
任意一次运行时检测并补发。

---

## 验证配置是否生效

cron-job.org 任务运行后，去 GitHub 仓库：
**Actions → AI 每日资讯推送**

应看到一条 `workflow_dispatch` 来源的运行记录，
触发时间精确在 UTC 01:00 前后（通常 < 1 分钟误差）。

---

## 常见问题

**Q：cron-job.org 发送失败怎么看？**
- cron-job.org Dashboard → 任务详情 → **Execution history**
- 可以看到每次请求的 HTTP 响应码，正常应为 `204`

**Q：GitHub API 返回 404？**
- 检查 URL 中的用户名和仓库名是否正确
- 检查 workflow 文件名是否为 `daily_push.yml`

**Q：GitHub API 返回 401 Unauthorized？**
- Token 过期或无 `workflow` 权限，重新生成

**Q：GitHub API 返回 422？**
- Request Body 中 `"ref": "main"` 确认分支名正确
