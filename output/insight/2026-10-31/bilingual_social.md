# Agent 的瓶颈不是能力，是信任

Agent 的瓶颈不是能力，是信任。

同一天看到两组数据，几乎把行业现状摊开了：Zest 已经能跨多人偏好协调、用短信完成真实餐厅预订（https://techcrunch.com/2026/10/30/zests-new-ai-agent-finds-restaurants-and-books-reservations-over-text/），OpenAI 把 Agent 塞进了 ServiceNow 的工作流和 Legora 的法律操作系统（https://openai.com/index/openai-servicenow-partnership-expansion）。另一边，DoorDash 说它从 AI Agent 收到的订单只有「数百单」（https://techcrunch.com/2026/10/30/doordash-said-its-only-received-several-hundred-orders-from-ai-agents/）。

不是技术不行。是没人敢把真实生活交给它。

企业侧敢用，是因为有流程、有审核、有人兜底——Agent 出错，损失可控。消费侧不敢用，是因为一次订错餐厅、一次下错单，代价直接落在用户身上，没有回滚。所以渗透率卡在「数百单」，不是需求不存在，是信任没建立。

这也解释了 OpenAI 为什么这时候推失准检测（https://openai.com/index/how-we-detect-frontier-model-misalignment）：Agent 越往真实世界走，越需要一条可观测、可干预的边界。YC Labs 在 Minecraft 里跑 Agent 集群（https://labs.ycombinator.com/projects/games/index.html），看的是能力上限和涌现行为；OpenAI 看的是行为越界。两边其实在回答同一个问题：这个系统在没人盯着的时候，还值不值得信。

结论很直接：下一阶段的竞争，不是谁的 Agent 更能干，是谁先让用户敢放手。企业工作流是信任的试验田，消费场景才是终局考场。现在还在极早期，别被 demo 骗了。

---

# The agent bottleneck isn't capability — it's trust

The agent bottleneck isn't capability. It's trust.

Two data points landed on the same day and basically mapped the whole industry: Zest now coordinates multi-person preferences and books real restaurant reservations over text (https://techcrunch.com/2026/10/30/zests-new-ai-agent-finds-restaurants-and-books-reservations-over-text/), while OpenAI pushed agents into ServiceNow workflows and Legora's legal OS (https://openai.com/index/openai-servicenow-partnership-expansion). Meanwhile DoorDash says it has received only "several hundred" orders from AI agents (https://techcrunch.com/2026/10/30/doordash-said-its-only-received-several-hundred-orders-from-ai-agents/).

The tech works. Nobody trusts it with their actual life yet.

Enterprises adopt because there are workflows, approvals, and humans in the loop — when the agent screws up, the blast radius is contained. Consumers don't, because a wrong reservation or a wrong order lands directly on them with no rollback. That's why adoption is stuck at "several hundred." The demand isn't missing. The trust is.

Which is exactly why OpenAI is shipping misalignment detection now (https://openai.com/index/how-we-detect-frontier-model-misalignment). The further agents reach into the real world, the more you need an observable, interruptible boundary. YC Labs runs agent swarms in Minecraft (https://labs.ycombinator.com/projects/games/index.html) to probe capability ceilings and emergent behavior; OpenAI watches for behavior crossing the line. Both are answering the same question: is this system still worth trusting when no one's watching?

So the next competitive axis isn't who has the most capable agent. It's who gets users to let go first. Enterprise workflows are the trust testbed; consumer scenarios are the final exam. We're very early — don't let the demos fool you.