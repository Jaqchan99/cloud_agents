# Agent 要花钱了，但没人说清楚谁负责

同一天，Shopify 把商品目录开放给更多 AI Agent，让它们能直接浏览下单；Amex 则发布了防止 Agent 未授权消费的框架。一个在踩油门，一个在装刹车。

这不是巧合，是 Agent 电商最核心的矛盾第一次被摆到台面上：开放入口和约束出口，谁说了算？

Shopify 的算盘很清楚——Agent 代用户下单能放大交易量，入口越自由越好（https://www.theverge.com/news/1010365/shopify-opens-its-catalog-up-to-more-ai-agents）。但 Amex 的立场同样清楚：一旦 Agent 误购、重复下单、被 prompt injection 劫持去刷单，纠纷算谁的？所以它必须先划出授权边界（https://techcrunch.com/2026/10/13/amex-introduces-a-framework-to-prevent-ai-agents-from-making-unauthorized-purchases/）。

问题在于，这两套逻辑目前没有共同的语法。授权粒度是「单笔上限」还是「品类白名单」？Agent 越权时，是模型厂商、平台、还是用户担责？没人给出标准答案。

我的判断是：Agent 电商的瓶颈从来不是模型会不会下单——它早就会了。瓶颈是金融机构愿不愿意把「花钱」这个动作交给一个概率性系统。而支付机构开放授权的前提，恰恰是端侧可信执行和安全红队验证先到位。这就是为什么端侧 Agent 和机器人红队测试（https://techcrunch.com/2026/10/13/laplace-intelligence-red-teams-robots-and-self-driving-cars-before-the-real-world/）和今天的电商新闻是同一件事的两面。

谁先定义 Agent 的授权标准，谁就掌握下一代流量和风控的主动权。这比谁的模型更强重要得多。

---

# Agents Are Ready to Spend. Nobody Agreed on Who's Liable.

Shopify opened its catalog to more AI agents today. Amex shipped a framework to stop those same agents from spending money they shouldn't.

One is flooring the gas. The other is installing the brake. Same day, same problem.

This is the first time the core tension of agentic commerce has been forced into the open: who controls the entry point, and who controls the exit?

Shopify's bet is obvious — agents that buy on a user's behalf inflate transaction volume, so the entry should be as frictionless as possible (https://www.theverge.com/news/1010365/shopify-opens-its-catalog-up-to-more-ai-agents). Amex's position is equally obvious: the moment an agent mis-buys, double-orders, or gets hijacked by prompt injection to drain a card, someone has to eat the loss. So it draws the authorization boundary first (https://techcrunch.com/2026/10/13/amex-introduces-a-framework-to-prevent-ai-agents-from-making-unauthorized-purchases/).

Here's the catch: these two logics don't share a grammar yet. Is authorization a per-transaction cap, a category whitelist, or something else? When an agent oversteps, does the model vendor, the platform, or the user pay? Nobody has answered.

My take: the bottleneck was never whether models can transact — they've been able to for a while. The bottleneck is whether financial institutions will hand the act of spending to a probabilistic system. And that hinges on on-device trusted execution and safety red-teaming maturing first — which is exactly why today's robotics red-team news (https://techcrunch.com/2026/10/13/laplace-intelligence-red-teams-robots-and-self-driving-cars-before-the-real-world/) and the commerce news are two sides of one story.

Whoever defines the authorization standard for agents owns the next generation of distribution and risk control. That matters far more than whose model benchmarks higher.