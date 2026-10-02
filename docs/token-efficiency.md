# Token 效率实验：把用量和质量一起测

`python -m peerlab efficiency` 使用两个独立因素，各两个水平：

| 条件 | 系统提示词 | 输出要求 |
|---|---|---|
| verbose_explain | 常规完整表述 | answer + 简短 explanation |
| verbose_answer | 常规完整表述 | 仅 answer |
| compact_explain | 压缩表述 | answer + 简短 explanation |
| compact_answer | 压缩表述 | 仅 answer |

题目全文始终相同，没有删条件、改精度、提供参考答案。模型参数保持不变，每个条件独立调用，不传递其他条件的输出。压缩版本意图保留原要求，但措辞变化本身也可能影响行为；不能声称只改变了 token 数量。实验不要求模型展示隐藏思考过程。

```bash
# 完全离线预览：2模型 × 3题 × 4条件 = 24次请求
python -m peerlab efficiency --dry-run

# 真实调用，可能产生供应商费用
python -m peerlab efficiency --output runs/token-pilot

# 完全离线重算分数、配对统计、HTML和CSV
python -m peerlab analyze-efficiency runs/token-pilot/run.json --output runs/token-recheck
```

每个题目/重复构成一个区组；题目区组顺序和区组内的模型/条件顺序分别随机打乱，串行执行。seed只固定调度顺序，不固定供应商采样；一次重复不是确定性复现。`--repeats`可增加同题采样，不会增加独立题型。两模型每题每重复共8次请求。

默认最多24次聊天请求，每次最多700输出token，90秒超时、无自动重试。运行前校验预算；每次调用前落盘pending记录。中断和错误保留，绝不重跑后覆盖。max_tokens上限相同是为了避免把截断当作节省；输入和失败请求费用不受该输出上限约束。

分析首先核验数据集哈希、精确数值参考、调用顺序、冻结提示词、预算和每条判分。这里的核验是文件内部一致性，不是供应商签名认证。审稿实验的旧schema与本协议分开，不改变已发表数据。

统计按模型分开，主要比较verbose_explain→compact_answer；四条次要比较分别固定另一个因素。每个比较只使用同模型/题目/重复两边均返回的配对。HTTP错误是缺失；错误JSON、错误答案或截断是返回但失败。逐题保留改善和退步，不能用总正确数相同推出逐题无损。

每个token指标只在两侧该项用量均已知的配对子集求和：`节省比例 = 1 - 右侧总和 / 左侧总和`。未知值不补零，缺失数在分析中报告。它是总和的比例，不是逐题节省百分比的平均。`tokens_per_correct`包含该配对集合中错误答案花掉的token；零正确或用量缺失时返回null，不能解释为零成本。它只衡量本题集的答案，不衡量被删除解释的可读性或审计价值。

保留完整usage，按供应商返回的prompt_tokens/completion_tokens/total_tokens计数，不用字符串长度猜token。缓存命中不等于没有输入token；不同模型tokenizer和输入/输出/缓存计费不同，不把总token节省直接换算成人民币节省，不跨模型比较token效率。供应商文档：[DeepSeek用量字段](https://api-docs.deepseek.com/api/create-chat-completion/)、[DeepSeek缓存说明](https://api-docs.deepseek.com/guides/kv_cache/)、[Kimi用量字段](https://platform.kimi.com/docs/api/chat)（访问于2026-10-02）。本项目未测量账单金额或控制服务端缓存。
