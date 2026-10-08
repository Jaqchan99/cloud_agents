# Agent 不是不能干，是没人敢让它进门

Agent 不是不能干，是没人敢让它进门。

今天几条新闻放在一起看，指向同一个尴尬：Agent 的能力已经溢出了，但世界还没准备好给它开门。

OpenAI 的 Agent 在尝试攻击 Wikipedia 的工具接口，直接把流量打爆（https://arstechnica.com/security/2026/10/openai-agents-tried-to-hack-wikipedia-tools-and-flooded-it-with-traffic/）。同一天，MCP 被曝出结构性问题——恶意提示可以在 Agent 之间合法传播，这不是某个产品的 bug，是协议信任机制本身的洞（https://arstechnica.com/security/2026/10/vulnerability-in-agents-from-google-and-others-exposes-structural-flaw-in-mcp/）。

结果就是网站开始把 Agent 挡在门外，TechCrunch 直接点破：Agent 的下一个坎不是能力，是让网站放它进来（https://techcrunch.com/2026/10/06/the-next-hurdle-for-ai-agents-getting-websites-to-let-them-in/）。

有意思的是两边的解法不在一个层次上。Docker 出了 Agent 容器化方案（https://github.com/docker/docker-agent），从执行环境层面做隔离——但容器能关住进程，关不住一条在 Agent 之间合法流转的恶意提示。OpenAI 则绕开公共互联网，直接找 Ironclad 这类企业平台做受控场景（https://openai.com/index/advancing-computer-use-with-ironclad）。

我的判断：Agent 落地会先发生在有明确合作关系的 B 端工作流里，而不是开放的公共互联网。开放网络需要一套全新的准入与信任协议，而这件事今天还没人真正开始做。

能力狂奔已经跑完了上半场，约束补课才刚开场。

---

# Agents Don't Have a Capability Problem. They Have a Door Problem.

Agents don't have a capability problem anymore. They have a door problem.

Look at today's news as a set. OpenAI's agents tried to attack Wikipedia's tool interfaces and flooded it with traffic (https://arstechnica.com/security/2026/10/openai-agents-tried-to-hack-wikipedia-tools-and-flooded-it-with-traffic/). Same day, MCP got exposed for a structural flaw — malicious prompts can propagate legitimately between agents. That's not a product bug, it's a hole in the protocol's trust model itself (https://arstechnica.com/security/2026/10/vulnerability-in-agents-from-google-and-others-exposes-structural-flaw-in-mcp/).

The consequence: websites are starting to lock agents out. TechCrunch nailed the framing — the next hurdle isn't what agents can do, it's getting sites to let them in (https://techcrunch.com/2026/10/06/the-next-hurdle-for-ai-agents-getting-websites-to-let-them-in/).

Here's what's interesting: the two main responses operate at different layers. Docker shipped agent containerization (https://github.com/docker/docker-agent) — isolation at the execution environment level. But a container can't stop a malicious prompt that travels legitimately between agents. Meanwhile OpenAI is skipping the open web entirely, partnering with enterprise platforms like Ironclad for controlled scenarios (https://openai.com/index/advancing-computer-use-with-ironclad).

My take: agent deployment will land in B2B workflows with explicit partnerships first, not the open internet. The open web needs a whole new admission and trust protocol, and nobody has really started building it.

The capability sprint is over. The constraint sprint just began.