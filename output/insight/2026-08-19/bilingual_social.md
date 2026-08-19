# Agent 的下一站不是更聪明，而是更便宜

别再问 Agent 能做什么了，该问它花多少钱。

今天两条新闻放在一起看，信号很明确：Agent 的工程化重心正在从功能扩展转向资源效率。HuggingFace 上 IBM 的研究在量化 Agent 到底需要多少记忆——不是拍脑袋给个 128K 上下文，而是用方法算出成本与性能的平衡点（https://huggingface.co/blog/ibm-research/altk-evolve-hmm）。另一边，开源社区推出了 fx，一个号称 tiny、open、native 的编码 Agent，摆明了要把资源门槛拉下来（https://fx.sh）。

这不是巧合。Agent 从 demo 走向生产，第一个撞墙的不是模型能力，而是账单。跑一个 Agent 要多少次 token 调用？要多少显存？要多少推理延迟？这些问题不解决，Agent 永远停在玩具阶段。

研究界在量化，工程界在轻量化，两条路指向同一个终点：Agent 要成为基础设施，必须可衡量、可负担。别再追着 benchmark 跑了，先看看你的成本曲线。

---

# The Next Frontier for Agents Isn't Smarter — It's Cheaper

Stop asking what agents can do. Ask what they cost.

Two stories today make the shift unmistakable: the engineering focus for AI agents is moving from capability to resource efficiency. IBM Research published a method to quantify how much memory an agent actually needs — not a hand-wavy 128K context, but a calculated trade-off between cost and performance (https://huggingface.co/blog/ibm-research/altk-evolve-hmm). Meanwhile, the open-source community shipped fx, a self-described tiny, open, native coding agent, explicitly targeting lower resource barriers (https://fx.sh).

This isn't coincidence. When agents move from demo to production, the first wall isn't model smarts — it's the bill. How many token calls per task? How much VRAM? How much latency? Until these are answered, agents stay toys.

Researchers are quantifying; engineers are slimming down. Both roads lead to the same place: for agents to become infrastructure, they must be measurable and affordable. Stop chasing benchmarks — look at your cost curve.