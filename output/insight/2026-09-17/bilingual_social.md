# MCP 一天之内接管了你的家和你的生意，但没人管谁在开门

MCP 今天完成了身份跃迁：从开发者协议变成了物理世界的接口标准。

Google 让任意 Agent 控制你的智能家居设备，Meta 让编码 Agent 接管 WhatsApp Business 的配置运维。两家巨头同时选 MCP 而不是自建协议，说明接口标准之争基本收敛了——接下来争的是谁掌握被接入的设备和账户。

同一天，OpenAI 上线 Sponsored Agents，把广告从展示位变成可被调用的代理，直接接进 HubSpot 和 Shopify 的交易链路。Agent 调用哪个商家代理，本身成了可售卖的库存。

能力扩张的速度很惊人。但 TechCrunch 那篇说得很直白：AI 实验室在忙着搞内部审计，也许该先把前门关上。

我的观点是：审计是事后追责，入口权限是事前防线。当 Agent 能开你家灯、能改你企业账户设置、能替你决定买谁的东西时，「谁能启动这个 Agent、它能触达什么范围」比「出事之后谁来背锅」重要一个量级。

更微妙的是，这两件事其实是一件事。Pentad 那篇讲 Agent 舰队需要 OS 而不是更大的 Harness——如果编排层真的升维成操作系统，那入口权限和调度控制本来就该是内核的一部分，而不是外挂一个合规模块。现在行业的状态是：能力层已经跑到了 OS 级抽象，安全层还停在日志和审计报告。

MCP 收敛是好事，标准统一降低摩擦。但标准统一也意味着攻击面统一。一个协议同时连着你的客厅、你的客服后台和你的支付链路，这个协议的身份认证和权限模型，现在配得上它的权限范围吗？

没看到有人认真回答这个问题。

---

# MCP just got the keys to your house and your business. Nobody's watching the door.

MCP crossed a line today. It stopped being a developer protocol and became the interface to the physical world.

Google now lets any agent control your smart home devices. Meta lets coding agents handle WhatsApp Business setup and ops. Both picked MCP over building their own — which means the protocol war is basically over. The next fight is over who owns the devices and accounts being connected.

Same day, OpenAI launched Sponsored Agents: ads that aren't placements but callable agents, wired straight into HubSpot and Shopify checkout flows. Which merchant agent your agent decides to call is now sellable inventory.

Impressive velocity. But read the TechCrunch piece: AI labs are staffing up internal auditors while leaving the front door wide open.

Here's my take. Auditing is accountability after the fact. Access control is the defense before it. When an agent can flip your lights, reconfigure your business account, and decide who you buy from, "who can launch this agent and what can it reach" matters an order of magnitude more than "who gets blamed afterward."

And these aren't two separate problems. Pentad argues agent fleets need an OS, not a bigger harness. If the orchestration layer really becomes an operating system, then permissions and scheduling aren't a bolt-on compliance module — they're kernel primitives. Right now the capability layer is already at OS-level abstraction while the safety layer is still writing audit logs.

MCP converging is good. Less friction. But a single standard also means a single attack surface. One protocol now touches your living room, your support backend, and your payment rails. Does its auth and permission model actually match that blast radius?

Haven't seen anyone seriously answer that yet.