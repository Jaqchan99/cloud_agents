# Agent 最大的敌人不是能力不够，是你不敢让它联网

Agent 最大的敌人不是能力不够，是你不敢让它联网。

今天三件事放在一起看，结论很清楚：Anthropic 把内部评估环境的网络直接切断了（https://www.theverge.com/ai-artificial-intelligence/1009286/anthropic-is-cutting-off-its-internal-evaluations-from-the-internet），YC 项目 Agent37 在卖低成本沙箱（https://news.ycombinator.com/item?id=50059096），HuggingFace 上线了 Agent 能力排行榜（https://huggingface.co/blog/agent-leaderboard）。一个头部实验室被迫收缩，一个创业公司在卖隔离，一个平台在给 Agent 打分。

这不是三条新闻，这是一条产业链的雏形：需求端已经痛到要断网自救，供给端开始把「安全隔离」商品化，中间层开始试着给 Agent 定标准。

但真正扎心的是 Ars Technica 那篇观察——AI 编程 Agent 产出的代码量在涨，软件价值没涨（https://arstechnica.com/ai/2026/10/ai-coding-agents-generate-more-code-but-not-more-software/）。排行榜在算基准分数和成本效率，真实工程世界里代码多了不等于软件多了。度量体系和真实价值之间，有一道没人愿意承认的鸿沟。

我的判断：2026 年 Agent 的竞争焦点不是谁更聪明，是谁能先证明自己「可控」。Anthropic 断网不是保守，是清醒——它比谁都清楚，一个能越界的 Agent 在评估环境里意味着什么。沙箱会成为标配，不是加分项。而排行榜如果不能把「真实产出」纳入度量，就只是又一张好看的营销图。

能力不是问题。信任才是。谁先把信任做成基础设施，谁就拿到下一轮的入场券。

---

# The Agent Bottleneck Isn't Capability — It's That You Can't Let It Online

The biggest enemy of agents isn't weak capability — it's that you can't bring yourself to let them online.

Three things landed today, and together they tell one story. Anthropic cut its internal evaluation environments off from the internet entirely (https://www.theverge.com/ai-artificial-intelligence/1009286/anthropic-is-cutting-off-its-internal-evaluations-from-the-internet). YC's Agent37 is selling low-cost sandboxes (https://news.ycombinator.com/item?id=50059096). HuggingFace shipped an agent capability leaderboard (https://huggingface.co/blog/agent-leaderboard). One top lab retreating, one startup selling isolation, one platform trying to score agents.

That's not three headlines. That's the skeleton of a supply chain: demand-side pain bad enough to justify going offline, supply-side starting to commoditize safety isolation, and a middle layer trying to define the standard.

But here's the part that stings. Ars Technica observed that AI coding agents are producing more code without producing more software (https://arstechnica.com/ai/2026/10/ai-coding-agents-generate-more-code-but-not-more-software/). The leaderboard measures benchmark scores and cost efficiency. The real world measures whether anything actually got built. There's a gap between the metric and the value, and nobody wants to name it.

My read: the 2026 agent race isn't about who's smartest. It's about who can prove they're controllable first. Anthropic going offline isn't caution — it's clarity. They know better than anyone what a boundary-crossing agent means inside an eval environment. Sandboxes will become table stakes, not a feature. And a leaderboard that can't measure real output is just another pretty marketing chart.

Capability isn't the problem. Trust is. Whoever turns trust into infrastructure gets the next ticket in.