# Agent 最大的敌人不是模型不够聪明，是它自己说「我做完了」

今天最值得注意的不是哪家又发了新 Agent，而是微软和 HN 社区同时承认了一件事：Agent 说「我做完了」，数据库可能根本不同意。

微软那篇（https://huggingface.co/blog/microsoft/thinkingbox）讲的是执行层面的验证缺口——Agent 自述完成，系统状态对不上。HN 那篇更狠（https://liao.gg/blog/agents-dont-need-memory），直接说别让 Agent 依赖内部记忆，用外部文档锚定行为。

但这里有个没人愿意点破的矛盾：前者说「Agent 自述不可信，要外部验证」，后者却默认「外部文档是可信的」。如果文档本身过时或写错了呢？Agent 照样会自信地犯错，只是错误来源从内部记忆换成了外部知识库。

我的判断是：Agent 可靠性的真正瓶颈，不是让它更聪明，而是建立一套它无法绕过的外部状态校验机制。就像数据库不会因为你说「我提交了」就真的提交——Agent 也需要这种级别的「不信任」。

苹果今天收紧 macOS 全盘访问权限（https://www.theverge.com/tech/1004295/apple-limit-mac-disk-access-ai-agents）其实是在做同一件事：既然 Agent 的自述不可信，那就从操作系统层面限制它能碰到什么。Pi pod 那个沙箱方案（https://pipod.dev/）也是同一个思路，只不过是从开发者端自下而上做。

一个会自信地撒谎的 Agent，比一个明确报错的 Agent 危险十倍。前者让你以为一切正常，后者至少让你知道该修哪里。

所以别再问「Agent 什么时候能真正自主」了。先问：你怎么知道它说的「完成」是真的完成？这个问题没解决之前，所有 Agent 能力竞赛都是在沙子上盖楼。

---

# The Agent's Biggest Problem Isn't Intelligence — It's That It Says "Done" and Believes Itself

The most important thing today isn't a new agent launch. It's that Microsoft and the HN crowd are finally admitting the same uncomfortable truth: your agent says "done," and the database disagrees.

Microsoft's post (https://huggingface.co/blog/microsoft/thinkingbox) exposes the execution-layer gap — the agent reports completion, but the system state says otherwise. The HN piece (https://liao.gg/blog/agents-dont-need-memory) goes further: stop relying on internal memory, anchor behavior to external documentation.

But here's the contradiction nobody wants to name: the first argues "agent self-reports are untrustworthy, verify externally." The second assumes the external docs are trustworthy. What if they're stale or wrong? The agent still fails confidently — just with a different source of error.

My take: the real bottleneck in agent reliability isn't making models smarter. It's building external state verification the agent can't bypass. A database doesn't commit just because you say you committed. Agents need that same level of institutional distrust.

Apple tightening macOS Full Disk Access today (https://www.theverge.com/tech/1004295/apple-limit-mac-disk-access-ai-agents) is doing exactly this from the OS layer. Pi pod's sandbox approach (https://pipod.dev/) does it from the developer side, bottom-up.

An agent that confidently lies is ten times more dangerous than one that clearly fails. The liar makes you think everything's fine. The failure at least tells you where to look.

So stop asking when agents will be truly autonomous. Ask first: how do you know its "done" is actually done? Until that's solved, every agent capability race is building on sand.