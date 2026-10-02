# PeerLab 实验报告

- Run: `78aefa6b6e614449bb10038bae23959f`
- Mode: live / Status: partial
- Protocol: independent / Arms: baseline, self, peer, peer_independent
- Dataset SHA-256: `5e8206fe4cf3edb50437b15ede8d3980205a6355cc59f51cbc270e49c752b568`
- 实际请求尝试: 150 / 计划: 168

正确率仅针对收到回答的样本；错误、跳过和未执行不当作错误答案，必须结合覆盖率阅读。截断回答计为未通过。

| 模型 | 条件 | 正确 / 已返回 | 已返回 / 计划 | 修正错误 | 改错原答案 | 有效配对 |
|---|---|---:|---:|---:|---:|---:|
| deepseek / deepseek-flash | baseline | 0 / 12 | 12 / 12 | 0 | 0 | 12 |
| deepseek / deepseek-flash | self | 3 / 11 | 11 / 12 | 3 | 0 | 11 |
| deepseek / deepseek-flash | peer | 5 / 11 | 11 / 12 | 5 | 0 | 11 |
| deepseek / deepseek-flash | peer_independent | 7 / 10 | 10 / 12 | 7 | 0 | 10 |
| kimi / kimi-k2.6 | baseline | 0 / 10 | 10 / 12 | 0 | 0 | 10 |
| kimi / kimi-k2.6 | self | 5 / 10 | 10 / 12 | 5 | 0 | 10 |
| kimi / kimi-k2.6 | peer | 5 / 9 | 9 / 12 | 5 | 0 | 9 |
| kimi / kimi-k2.6 | peer_independent | 6 / 10 | 10 / 12 | 6 | 0 | 10 |

API 已返回的 total_tokens 合计：80658。缺失用量及失败请求的费用未知，不估算账单。

## 如何解释

这是自建小题库上的探索实验，不是通用模型排行榜。一次采样不能支持显著性结论；题目可能已被模型见过。
self 与 peer 都在同一 baseline 上增加一次审稿和一次修订；调用次数相同，但 token、延迟与费用并不相同。
若启用 peer_independent：审稿者额外看到自己在候选答案出现前的 baseline；复用已发生的调用，不多求解一次。比较包含额外上下文与审稿提示变化，不能单独归因为锚定效应。
seed 仅控制本地执行顺序及展示，不保证云端模型确定性。重复样本彼此不独立，不能当成独立题目扩大样本量。
客观判分只检查最终 answer，不判断解释质量。盲评是展示层匿名，页面源数据含映射，不适合对抗性评审。
