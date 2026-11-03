# Agent 越能干，越不可信：能力与攻击面同源的一周

这周两件事放在一起看，味道很冲。

LongCat-2.5 把原生多模态和 Agent 行动能力绑在一起卖，逻辑很顺：感知越强、操作越自然，Agent 才越像真的能干活。同一天，一篇后门研究告诉你，同一套预训练管线可以被投毒，定向植入触发行为。

这不是巧合，是同一个硬币。能力从哪来，攻击面就从哪来。

更值得警惕的是落地速度。Momentic 这类产品让 Agent 直接「像用户一样」操作真实应用去抓 bug，这是 Agent 商业化最健康的一步——从通用助手叙事退到具体工程环节。但换个角度看，Agent 越深入生产系统，预训练里埋的触发行为破坏力就越大。落地每快一步，安全验证的欠账就多一分。

行业现在的定价逻辑是「能不能干」，而不是「敢不敢信」。模型厂商比的是 benchmark 和 demo 流畅度，采购方问的是能不能省人力，几乎没人问：这条训练数据供应链，我验证过吗？

Agent 的信任边界不会自己长出来。它得靠数据来源审计、行为可观测性、权限最小化这些又土又慢的工程手段堆出来。谁先把「可信」做成可交付的指标，谁才配谈企业级 Agent。

能干是入场券，可信才是护城河。这周的新闻，把这句话从口号变成了账单。

---

# The More Capable the Agent, the Less Trustworthy: When Capability and Attack Surface Share a Root

Two stories this week deserve to be read together.

LongCat-2.5 sells native multimodality as the key to agentic tasks — stronger perception, more natural action, a more useful agent. Same week, a backdoor paper shows the same pretraining pipeline can be poisoned to plant targeted trigger behaviors.

That's not a coincidence. It's the same coin. Capability and attack surface come from the same place.

The part that should worry you is the deployment speed. Momentic puts agents directly into real apps, using them like a user to catch bugs — arguably the healthiest commercialization move in the space, trading the general-assistant story for a concrete engineering loop. But flip it: the deeper agents go into production, the more damage a pretrained trigger can do. Every step faster in deployment is a step further behind on verification.

The industry is pricing 'can it do the job,' not 'should I trust it.' Vendors compete on benchmarks and demo smoothness. Buyers ask whether it saves headcount. Almost nobody asks: have I audited this training data supply chain?

Trust boundaries for agents won't emerge on their own. They get built from unglamorous, slow engineering — data provenance audits, behavior observability, least-privilege action scopes. Whoever turns 'trustworthy' into a deliverable metric first gets to talk about enterprise agents seriously.

Capable is the ticket. Trustworthy is the moat. This week turned that from a slogan into an invoice.