"""
Discord Interactions FastAPI Server

处理所有 Discord interaction 类型：
  Type 1: PING（端点验证）
  Type 2: APPLICATION_COMMAND（Slash Commands）
  Type 3: MESSAGE_COMPONENT（按钮/下拉菜单点击）

Ed25519 签名验证（pynacl）。
长耗时操作使用延迟响应（type 5）+ 后台任务 + 编辑回复。
配置变更通过 GitHub API 持久化到仓库。
"""
import sys
import json
import os
import asyncio
import base64
import hashlib
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import httpx

# ── Path setup ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from insight_engine.config import load_insight_config, save_insight_config, get_default_insight_config
from insight_engine.config_panel import build_config_panel, get_config_panel_content
from prompts import get as get_prompt

# ── Constants ───────────────────────────────────────────────────────────
PUBLIC_KEY: str = os.environ.get("DISCORD_PUBLIC_KEY", "")
APP_ID: str = os.environ.get("DISCORD_APP_ID", "")
DISCORD_API: str = "https://discord.com/api/v10"
GITHUB_API: str = "https://api.github.com"
GITHUB_TOKEN: str = os.environ.get("GH_PAT", "")
GITHUB_REPO: str = os.environ.get("GITHUB_REPOSITORY", "")

THREAD_POOL = ThreadPoolExecutor(max_workers=4)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"
INSIGHT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "insight_config.json"
LAST_PUSH_DATE_PATH = Path(__file__).parent.parent / "config" / "last_push_date.txt"
THOUGHT_CONTEXT_PATH = Path(__file__).parent.parent / "config" / "today_thought_context.json"

app = FastAPI(title="AI News Bot — Discord Interactions")

_github_rate_limit_until = 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/health")
async def health():
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════════════════
# Ed25519 signature verification
# ═══════════════════════════════════════════════════════════════════════════
def verify_signature(signature: str, timestamp: str, body: bytes) -> None:
    if not PUBLIC_KEY:
        raise HTTPException(500, "DISCORD_PUBLIC_KEY not configured")
    try:
        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        message = f"{timestamp}{body.decode()}".encode()
        verify_key.verify(message, bytes.fromhex(signature))
    except (BadSignatureError, ValueError) as e:
        raise HTTPException(401, f"invalid request signature: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Main interaction endpoint
# ═══════════════════════════════════════════════════════════════════════════
@app.post("/interactions")
async def handle_interaction(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    verify_signature(signature, timestamp, body)

    data = json.loads(body)
    t = data.get("type")

    if t == 1:
        return {"type": 1}

    if t == 2:
        return await handle_slash_command(data)

    if t == 3:
        return await handle_message_component(data)

    return {"type": 4, "data": {"content": "Unknown interaction type."}}


# ═══════════════════════════════════════════════════════════════════════════
# Slash command router
# ═══════════════════════════════════════════════════════════════════════════
async def handle_slash_command(data: dict) -> dict:
    name = data.get("data", {}).get("name", "")
    token = data.get("token", "")

    if name == "push":
        asyncio.create_task(deferred_github_trigger(token, "daily_push.yml", "push"))
        return {"type": 5}

    if name == "insight":
        asyncio.create_task(deferred_github_trigger(token, "insight_engine.yml", "insight"))
        return {"type": 5}

    if name == "config":
        return await cmd_config()

    if name == "insight-config":
        return await cmd_insight_config()

    if name == "thought":
        return await cmd_thought()

    if name == "status":
        return await cmd_status()

    return {"type": 4, "data": {"content": f"未知命令: /{name}"}}


# ═══════════════════════════════════════════════════════════════════════════
# Immediate commands
# ═══════════════════════════════════════════════════════════════════════════

async def cmd_config() -> dict:
    config = _load_user_config()
    lang = config.get("language", "zh")
    cfg_str = json.dumps(config, ensure_ascii=False, indent=2)
    prefix = "⚙️ **Current Config:**" if lang == "en" else "⚙️ **当前配置：**"
    return {"type": 4, "data": {"content": f"{prefix}\n```json\n{cfg_str}\n```"}}


async def cmd_insight_config() -> dict:
    cfg = load_insight_config()
    panel = get_config_panel_content(cfg)
    return {"type": 4, "data": panel}


async def cmd_thought() -> dict:
    if THOUGHT_CONTEXT_PATH.exists():
        with open(THOUGHT_CONTEXT_PATH, "r", encoding="utf-8") as f:
            ctx = json.load(f)
        from thought_generator import format_thought_question_message
        msg = format_thought_question_message(ctx, lang="zh")
        return {"type": 4, "data": {"content": msg}}
    return {"type": 4, "data": {"content": "📭 今日暂无思考题，等待日报推送后自动生成。"}}


async def cmd_status() -> dict:
    last_push = "未知"
    if LAST_PUSH_DATE_PATH.exists():
        last_push = LAST_PUSH_DATE_PATH.read_text().strip()
    return {"type": 4, "data": {"content": f"📊 **推送状态**\n最近推送日期：{last_push}"}}


# ═══════════════════════════════════════════════════════════════════════════
# Deferred: trigger GitHub Actions workflow
# ═══════════════════════════════════════════════════════════════════════════

async def deferred_github_trigger(token: str, workflow_file: str, label: str):
    """通过 GitHub API 触发 workflow，避免 Fly.io 256MB 内存限制。"""
    try:
        ok = await _trigger_workflow(workflow_file)
        if ok:
            label_cn = "推送" if label == "push" else "Insight Engine 深度解读"
            await _edit_response(token, f"✅ **{label_cn}** 已提交到 GitHub Actions，请稍候查看对应频道。")
        else:
            await _edit_response(token, f"❌ 触发失败，请检查 GitHub Actions 状态或稍后重试。")
    except Exception as e:
        await _edit_response(token, f"❌ 触发异常：{e}")


async def _trigger_workflow(workflow_file: str) -> bool:
    """POST /repos/{owner}/{repo}/actions/workflows/{file}/dispatches"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("[GitHub] GITHUB_TOKEN 或 GITHUB_REPOSITORY 未配置")
        return False

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    global _github_rate_limit_until
    now = time.time()
    if now < _github_rate_limit_until:
        print(f"[GitHub] 频率限制中，跳过触发 {workflow_file}")
        return False

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json={"ref": "main"}, headers=headers)
        if resp.status_code == 204:
            print(f"[GitHub] 已触发 workflow: {workflow_file}")
            return True
        if resp.status_code == 429:
            _github_rate_limit_until = now + 60
        print(f"[GitHub] 触发失败 ({resp.status_code}): {resp.text}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Message Component handler (insight config panel)
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message_component(data: dict) -> dict:
    custom_id = data.get("data", {}).get("custom_id", "")
    token = data.get("token", "")

    parts = custom_id.split(":", 2)
    if len(parts) < 2 or parts[0] != "insight":
        return {"type": 4, "data": {"content": "Invalid component."}}

    action = parts[1]
    param = parts[2] if len(parts) > 2 else ""

    cfg = load_insight_config()

    if action == "toggle_format":
        formats = cfg.get("formats", [])
        if param in formats:
            formats.remove(param)
        else:
            formats.append(param)
        cfg["formats"] = formats

    elif action == "toggle_push":
        cfg["push_to_discord"] = not cfg.get("push_to_discord", True)

    elif action == "set_lang":
        cfg["language"] = param

    elif action == "rerun":
        asyncio.create_task(_deferred_rerun(token, cfg))
        panel = get_config_panel_content(cfg)
        panel["content"] = "⏳ **正在提交重跑...**\n\n" + panel.get("content", "")
        return {"type": 7, "data": panel}

    else:
        return {"type": 7, "data": get_config_panel_content(cfg)}

    save_insight_config(cfg)
    asyncio.create_task(_persist_config_to_github(cfg))
    return {"type": 7, "data": get_config_panel_content(cfg)}


async def _deferred_rerun(token: str, cfg: dict):
    """触发 insight engine 重跑（通过 GitHub Actions）。"""
    try:
        ok = await _trigger_workflow("insight_engine.yml")
        if ok:
            panel = get_config_panel_content(load_insight_config())
            panel["content"] = "✅ **Insight Engine 已提交重跑！** 完成后结果将推送至此频道。\n\n" + panel.get("content", "")
            await _edit_response(token, panel.get("content", ""), components=panel.get("components"))
        else:
            panel = get_config_panel_content(cfg)
            panel["content"] = "❌ 重跑触发失败，请稍后重试或检查 GitHub Actions。\n\n" + panel.get("content", "")
            await _edit_response(token, panel.get("content", ""), components=panel.get("components"))
    except Exception as e:
        await _edit_response(token, f"❌ 重跑异常：{e}")


# ═══════════════════════════════════════════════════════════════════════════
# Discord API helpers (async via httpx)
# ═══════════════════════════════════════════════════════════════════════════

async def _edit_response(token: str, content: str, components: Optional[list] = None):
    """PATCH /webhooks/{app_id}/{token}/messages/@original — 编辑延迟响应"""
    url = f"{DISCORD_API}/webhooks/{APP_ID}/{token}/messages/@original"
    payload = {"content": content}
    if components:
        payload["components"] = components
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.patch(url, json=payload)
        if resp.status_code not in (200, 204):
            print(f"[Discord] 编辑响应失败 ({resp.status_code}): {resp.text}")


# ═══════════════════════════════════════════════════════════════════════════
# Config persistence to GitHub
# ═══════════════════════════════════════════════════════════════════════════

async def _persist_config_to_github(config: dict):
    """将 insight_config.json 写入 GitHub 仓库（通过 API）。"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("[Config] GitHub API 未配置，跳过持久化")
        return

    content_str = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    content_b64 = base64.b64encode(content_str.encode()).decode()

    file_path = "config/insight_config.json"
    api_url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        sha = ""
        try:
            resp = await client.get(api_url, headers=headers)
            if resp.status_code == 200:
                sha = resp.json().get("sha", "")
        except Exception:
            pass

        payload = {
            "message": "chore: update insight_config.json via Discord interactions",
            "content": content_b64,
            "branch": "main",
        }
        if sha:
            payload["sha"] = sha

        try:
            resp = await client.put(api_url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                print("[Config] 已持久化 insight_config.json 到 GitHub")
            else:
                print(f"[Config] 持久化失败 ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[Config] 持久化异常: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Local config helpers
# ═══════════════════════════════════════════════════════════════════════════

def _load_user_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "push_channel": "discord",
        "language": "zh",
        "focus_topics": ["大语言模型", "AI Agent", "开源模型", "多模态"],
        "include_keywords": [],
        "exclude_keywords": [],
        "max_items": 8,
        "hours_back": 72,
        "push_time": "01:00",
        "include_hacker_news": True,
        "user_note": "",
        "weather_location": "Shanghai",
        "enabled_sources": [
            "TechCrunch AI", "VentureBeat AI", "The Verge AI",
            "Ars Technica", "HuggingFace Blog", "OpenAI Blog",
            "Google AI Blog", "Arxiv AI", "Arxiv ML",
        ],
    }


# ── Entrypoint ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
