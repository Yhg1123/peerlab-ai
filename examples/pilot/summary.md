# PeerLab 实验报告

- Run: `f933591e5bc347dba5e21e997163854e`
- Mode: live / Status: complete
- Dataset SHA-256: `58ba9588a64e5d8cb030aa446b691d9d34f699dcff55ccabafe50922eb2d2c98`
- 实际请求尝试: 30 / 计划: 30

正确率仅针对收到回答的样本；错误、跳过和未执行不当作错误答案，必须结合覆盖率阅读。截断回答计为未通过。

| 模型 | 条件 | 正确 / 已返回 | 已返回 / 计划 | 修正错误 | 改错原答案 | 有效配对 |
|---|---|---:|---:|---:|---:|---:|
| deepseek / deepseek-flash | baseline | 2 / 3 | 3 / 3 | 0 | 0 | 3 |
| deepseek / deepseek-flash | self | 2 / 3 | 3 / 3 | 0 | 0 | 3 |
| deepseek / deepseek-flash | peer | 2 / 3 | 3 / 3 | 0 | 0 | 3 |
| kimi / kimi-k2.6 | baseline | 3 / 3 | 3 / 3 | 0 | 0 | 3 |
| kimi / kimi-k2.6 | self | 3 / 3 | 3 / 3 | 0 | 0 | 3 |
| kimi / kimi-k2.6 | peer | 3 / 3 | 3 / 3 | 0 | 0 | 3 |

API 已返回的 total_tokens 合计：11166。缺失用量及失败请求的费用未知，不估算账单。

## 如何解释

这是自建小题库上的探索实验，不是通用模型排行榜。一次采样不能支持显著性结论；题目可能已被模型见过。
self 与 peer 都在同一 baseline 上增加一次审稿和一次修订；调用次数相同，但 token、延迟与费用并不相同。
seed 仅控制本地执行顺序及展示，不保证云端模型确定性。重复样本彼此不独立，不能当成独立题目扩大样本量。
客观判分只检查最终 answer，不判断解释质量。盲评是展示层匿名，页面源数据含映射，不适合对抗性评审。
