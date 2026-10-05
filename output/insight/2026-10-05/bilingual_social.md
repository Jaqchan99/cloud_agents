# Agent 的问题不是不够聪明，是没人能证明它干了什么

Agent 的问题不是不够聪明，是没人能证明它干了什么。

微软那篇 ThinkingBox 的案例值得反复看：Agent 自信地报告任务完成，数据库里却什么都没变。这不是 bug，这是架构级缺陷——Agent 的自我认知和外部真实状态之间，根本没有强制对齐机制。HN 上那篇「Agents don't need memory, they need documentation」其实在说同一件事，只是给出了相反的解法：与其强化不可靠的内部状态追踪，不如把状态外置成可审计的文档。两种路线之争，本质是在问一个问题——你信 Agent 的自述，还是信外部记录？

而苹果的动作把这个问题从技术层拉到了制度层。macOS 要收紧 Full Disk Access，理由写得很直白：AI Agent 让风险「实质性」上升。这是操作系统第一次把 Agent 当作一类需要系统性权限约束的主体，而不是普通应用。翻译一下：平台不再相信应用自己管好自己。

这两件事是一枚硬币的两面。内部不可验证，外部就必然收紧。企业侧的 ServiceNow AutoSynthData 补训练数据、OpenAI Dots 模糊企业软件和消费场景的边界，都是在同一重约束下抢地盘——谁先拿出「可被证明的 Agent」，谁就定标准。

所以别再问 Agent 能做什么了。该问的是：当它说「做完了」，你拿什么去验证。答不上来的产品，接下来会被 OS 和采购方一起教做人。

https://huggingface.co/blog/microsoft/thinkingbox
https://liao.gg/blog/agents-dont-need-memory
https://techcrunch.com/2026/10/02/apple-says-its-tightening-macos-full-disk-access-controls-due-to-new-risks-from-ai-agents/

---

# The Agent Problem Isn't Intelligence — It's Provability

Everyone's still asking what agents can do. The wrong question.

Microsoft's ThinkingBox writeup is the tell: an agent confidently reports the task is done, and the database disagrees. That's not a bug you patch. It's an architectural gap — nothing forces the agent's self-report to match external reality. The HN piece arguing agents need documentation, not memory, is circling the same wound from the opposite direction: don't trust the agent's internal state, make the state external and auditable. Two camps, one question — do you believe the agent, or the record?

Apple just moved that question from engineering to governance. macOS is tightening Full Disk Access explicitly because AI agents 'substantially' raise the risk. First time an OS treats agents as a distinct class of subject needing systemic permission limits rather than just another app. Read it plainly: the platform no longer trusts apps to police themselves.

These are two sides of one coin. If the inside can't be verified, the outside will get locked down. ServiceNow's AutoSynthData and OpenAI's Dots are both land grabs under that same constraint — whoever ships a provable agent first writes the standard.

Stop asking what agents can do. Start asking: when it says 'done,' what do you check it against. Products that can't answer that are about to get schooled by both the OS and the procurement team.

https://huggingface.co/blog/microsoft/thinkingbox
https://liao.gg/blog/agents-dont-need-memory
https://www.theverge.com/tech/1004295/apple-limit-mac-disk-access-ai-agents