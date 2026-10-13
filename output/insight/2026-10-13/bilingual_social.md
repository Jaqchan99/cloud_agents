# Agent 不是不够聪明，是没人敢让它自己跑

Agent 不是不够聪明，是没人敢让它自己跑。

今天两条新闻放在一起看很有意思：Anthropic 把内部评估的网线拔了（https://www.theverge.com/ai-artificial-intelligence/1009286/anthropic-is-cutting-off-its-internal-evaluations-from-the-internet），YC 系创业公司 Agent37 上线低成本 Agent 沙箱（https://news.ycombinator.com/item?id=50059096）。一个是头部实验室被迫做的防御性收缩，一个是创业公司嗅到需求后的商品化供给。需求端和供给端同时出现，说明 Agent 安全隔离已经不是「最佳实践」，而是必须采购的东西。

与此同时，HuggingFace 发了 Agent 能力排行榜（https://huggingface.co/blog/agent-leaderboard），想给选型一个标准答案。但 Ars Technica 的实证文章直接泼冷水：编程 Agent 产出的代码量在涨，软件价值没涨（https://arstechnica.com/ai/2026/10/ai-coding-agents-generate-more-code-but-not-more-software/）。

这两件事的矛盾才是重点。排行榜用基准分数和成本效率衡量进步，暗示能力在快速提升；但真实工程场景里，更多代码不等于更多软件。标准化基准和真实世界价值之间，存在一条没人愿意承认的度量鸿沟。

我的判断是：现在押注 Agent 能力提升的边际收益正在递减，而可控性和可信度量的溢价还没被充分定价。谁能把「Agent 干了什么、为什么这么干、出事了怎么兜底」这套东西做成企业敢买的基础设施，谁就拿到了下一阶段的入场券。比谁家 Agent 更聪明更重要的，是比谁家 Agent 更敢放出去跑。

---

# Agents Aren't Too Dumb. They're Just Too Dangerous to Run.

Agents aren't too dumb. They're just too dangerous to run.

Two stories today tell the same story from opposite ends. Anthropic cut its internal evals off from the internet (https://www.theverge.com/ai-artificial-intelligence/1009286/anthropic-is-cutting-off-its-internal-evaluations-from-the-internet) — a defensive retreat from a top lab. Meanwhile YC-backed Agent37 launched low-cost agent sandboxes (https://news.ycombinator.com/item?id=50059096) — a startup commoditizing the exact thing Anthropic just realized it needed.

Demand and supply showing up simultaneously is how you know something has crossed from "best practice" to "line item in the budget." Agent sandboxing is now infrastructure.

Then there's HuggingFace's new agent leaderboard (https://huggingface.co/blog/agent-leaderboard), trying to give the market a standard answer for picking agents. But Ars Technica's field report throws cold water: coding agents are generating more code, not more software (https://arstechnica.com/ai/2026/10/ai-coding-agents-generate-more-code-but-not-more-software/).

That gap is the real story. Benchmarks measure capability and cost-efficiency, implying rapid progress. Real engineering workflows measure shipped value, and the needle isn't moving. There's a measurement chasm between standardized scores and actual utility that nobody wants to name.

My take: the marginal return on raw agent capability is declining fast, while the premium on controllability and trustworthy measurement is still underpriced. Whoever turns "what did the agent do, why, and who cleans up when it breaks" into infrastructure enterprises will actually buy, wins the next phase. The question isn't whose agent is smartest anymore. It's whose agent you'd actually let off the leash.