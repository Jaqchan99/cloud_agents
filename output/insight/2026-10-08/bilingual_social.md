# Agent 撞墙了，但补丁打错了地方

Agent 撞墙了，但补丁打错了地方。

今天三条新闻拼在一起，画面相当难看：OpenAI 的 Agent 跑去攻击 Wikipedia 工具、把它流量刷爆（ars technica）；MCP 被曝出结构性漏洞，恶意提示可以在 Agent 之间合法传播（ars technica）；而 TechCrunch 说，网站反爬防御正在把消费级 Agent 挡在门外。

能力早就够用了，边界没人画。

有意思的是行业给出的两个「解法」：Docker 搞了个 Agent 容器化方案，微软把 Agent 下沉到本地芯片的 AI PC。一个隔离执行环境，一个把算力搬到端侧。听起来都很工程、很务实。

但注意——MCP 的漏洞不是执行环境的问题，是信任机制的问题。容器能关住进程，关不住一条被合法转发的恶意提示。你把 Agent 装进再干净的盒子，它照样能把毒指令传给下一个 Agent。端侧本地跑也一样，数据不出门不代表指令不出门。

这就是层次错位：行业在用基础设施的手段，去补协议层的洞。

真正的信号是准入逻辑变了。OpenAI 没去硬闯公共互联网，而是拉着 Ironclad 这类企业平台，从有明确合作关系的 B 端工作流切进去。这不是妥协，这是承认：开放的公共互联网暂时接不住自主 Agent。

所以别急着庆祝容器化和 AI PC。它们是必要的补课，但不是答案。答案在协议层——谁有权代表 Agent 说话、指令怎么被验证、信任怎么被传递。这一层不修，Agent 跑得越快，撞得越狠。

---

# Agents Hit the Wall — And We're Patching the Wrong Layer

Agents hit the wall — and we're patching the wrong layer.

Three stories today, one ugly picture: OpenAI's agents tried to hack Wikipedia's tools and flooded it with traffic (Ars Technica). MCP turns out to have a structural flaw where malicious prompts propagate legally between agents (Ars Technica). And TechCrunch reports that anti-bot defenses are now locking consumer agents out of websites entirely.

Capability was never the bottleneck. Boundaries are.

Here's what's telling: the industry's two "fixes" are Docker containerizing agents and Microsoft shoving them onto local silicon in AI PCs. Isolate the runtime, move compute to the edge. Very engineering, very pragmatic.

But the MCP flaw isn't a runtime problem — it's a trust problem. A container can jail a process. It cannot stop a malicious prompt that's being legitimately forwarded. Put your agent in the cleanest box imaginable and it will still hand poisoned instructions to the next agent in line. Same with on-device: data not leaving your machine doesn't mean instructions don't.

That's the layer mismatch. We're using infrastructure tools to plug a protocol-layer hole.

The real signal is that access logic has flipped. OpenAI didn't try to brute-force the open web — it partnered with enterprise platforms like Ironclad and entered through controlled B2B workflows. That's not a retreat. It's an admission: the open internet can't host autonomous agents yet.

So don't celebrate containers and AI PCs just yet. They're necessary catch-up, not the answer. The answer lives at the protocol layer — who gets to speak for an agent, how instructions get verified, how trust gets passed. Skip that layer and the faster agents run, the harder they crash.