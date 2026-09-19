# Agent 的战争已经不在模型里了，在配置文件和评估指标里

Agent 的竞争焦点已经不在模型能力上了，在配置文件和评估指标里。

今天 Anthropic 一口气做了三件事：Claude Code 重启 Projects，让多个 Agent 在云端被统一编排、共享记忆（https://www.theverge.com/ai-artificial-intelligence/997134/anthropic-claude-code-projects）；Claude Code 开始在没有 Claude.md 时读取 AGENTS.md，等于承认跨工具的配置约定比自家格式更重要（https://code.claude.com/docs/en/changelog）；同一天，Ax-check 上线，把「Agent 能不能用你的产品」变成一个可量化指标（https://www.ax-check.com/）。

这三件事单独看都不性感，但合在一起是一条清晰的线：Agent 正在从「演示能做什么」进入「怎么被编排、怎么被配置、怎么被评估」的基础设施阶段。

我的判断是：接下来 12 个月，Agent 生态的胜负手不是谁的模型强，而是谁定义了互操作标准。AGENTS.md 这种看似不起眼的约定，比一次 benchmark 提升重要得多——因为标准一旦被跨工具采用，切换成本就从模型转移到了生态。

有意思的是，同一天 The Verge 报道头部实验室在安全叙事下主动放缓超级智能节奏（https://www.theverge.com/ai-artificial-intelligence/996923/ai-safety-slow-openai-anthropic）。这看起来矛盾，其实不矛盾：能力扩张的边界被安全重新定义的同时，工程化的扩张一点没停。放缓的是「更大模型」的叙事，加速的是「Agent 怎么落地」的基建。

所以别盯着下一次模型发布了。去看谁在写配置文件、谁在定义评估口径、谁在管多 Agent 的记忆。那才是真正在砌墙的地方。

---

# The Agent War Has Left the Model. It's Now in Config Files and Eval Metrics.

The agent race stopped being about model capability. It's now about config files and eval metrics.

Anthropic did three things today that look unrelated but aren't. Claude Code relaunched Projects for orchestrating multiple agents in the cloud with shared memory (https://www.theverge.com/ai-artificial-intelligence/997134/anthropic-claude-code-projects). Claude Code now reads AGENTS.md when there's no Claude.md — effectively admitting that cross-tool config conventions matter more than its own format (https://code.claude.com/docs/en/changelog). And Ax-check launched, turning "can agents actually use your product?" into a measurable metric (https://www.ax-check.com/).

None of these are sexy on their own. Together they draw one clear line: agents are moving from "look what it can do" demos into infrastructure — how they're orchestrated, how they're configured, how they're evaluated.

My take: over the next 12 months, the agent ecosystem won't be won by whoever has the strongest model. It'll be won by whoever defines the interop standards. A boring convention like AGENTS.md matters more than another benchmark bump, because once a standard gets adopted across tools, switching costs migrate from the model to the ecosystem.

The interesting counterpoint: same day, The Verge reported that frontier labs are deliberately slowing the superintelligence narrative under a safety framing (https://www.theverge.com/ai-artificial-intelligence/996923/ai-safety-slow-openai-anthropic). That looks contradictory but isn't. Capability expansion is being reframed by safety, while engineering expansion hasn't slowed at all. What's slowing is the "bigger model" story. What's accelerating is the "how do agents actually ship" infrastructure.

So stop watching for the next model drop. Watch who's writing the config files, who's defining the eval criteria, who's managing multi-agent memory. That's where the walls are actually going up.