# Agent 越能干，越不该被信任

Agent 越能干，越不该被信任。

这周两件事摆在一起看，味道很冲。一边是 LongCat-2.5 把原生多模态和 Agent 行动能力深度绑定，卖点是让智能体更自然地理解和操作真实环境（https://longcat.ai/blog/longcat-2.5/）。另一边，一篇预训练投毒研究直接指出：同一套训练管线，正是植入定向后门、劫持 Agent 行为的通道（https://arxiv.org/abs/2610.37741）。

这不是巧合，是结构性的。能力越强，攻击面越大，而且两者共用同一条供应链。你没法只要前者不要后者。

更扎心的是落地速度。Momentic 这类产品已经把 Agent 塞进软件测试流程，让它像用户一样点应用、找 bug（https://momentic.ai/）。方向没错——高重复、高维护的工程环节确实该被 Agent 接管。但这也意味着 Agent 开始拿到真实系统的操作权限，一旦预训练阶段被埋了触发行为，破坏半径直接从「答错一句话」变成「在生产环境里做错一串操作」。

行业现在的定价逻辑还停在「能不能干」上，谁 demo 惊艳谁拿钱。但真正该被定价的是「敢不敢信」：训练数据从哪来、有没有完整性校验、Agent 的权限边界怎么收。这些问题不解决，落地越快，雷埋得越深。

能干是入场券，可信才是护城河。现在大部分团队只买了前者。

---

# The More Capable the Agent, the Less It Deserves Trust

Your agent got more capable this week. It also got easier to hijack.

Look at two things that landed side by side. LongCat-2.5 binds native multimodality tightly to agentic action — the pitch is that agents finally understand and operate real environments naturally (https://longcat.ai/blog/longcat-2.5/). Meanwhile, a pretraining-poisoning paper shows the exact same training pipeline is a clean channel for planting targeted backdoors that hijack agent behavior (https://arxiv.org/abs/2610.37741).

That's not a coincidence. Capability and attack surface grow from the same root, and they share a supply chain. You don't get to buy one without the other.

The scarier part is how fast this is hitting production. Momentic already drops agents into software testing — they use your app like a user and catch bugs (https://momentic.ai/). Right call: repetitive, high-maintenance engineering work is exactly what agents should own. But it also means agents now hold real operational permissions. If a trigger behavior was baked in at pretraining, the blast radius jumps from "wrong sentence" to "wrong sequence of actions in prod."

The industry is still pricing agents on capability — whoever demos best raises the round. What actually needs pricing is trust: where the training data came from, whether integrity was verified, how tightly the agent's permissions are scoped. Skip those, and the faster you ship, the deeper the mine.

Capable gets you in the door. Trustworthy is the moat. Most teams only bought the first one.