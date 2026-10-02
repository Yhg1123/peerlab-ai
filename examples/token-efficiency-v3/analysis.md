# Token 效率实验

Run: `ae7a0ade07df4f86ac0bbb4397b85d84` · partial · 请求尝试 256

| 模型 | 条件 | 正确/返回/计划 | 已知输入 token | 已知输出 token | 已知总 token | JSON失败 | 未完整输出 | 请求失败 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | answer_first_bounded | 3/32/32 | 4518 | 1863 | 6381 | 0 | 0 | 0 |
| deepseek | evidence_first_bounded | 10/32/32 | 4518 | 1735 | 6253 | 0 | 0 | 0 |
| deepseek | answer_first_unbounded | 2/32/32 | 4070 | 4046 | 8116 | 0 | 0 | 0 |
| deepseek | evidence_first_unbounded | 22/32/32 | 4070 | 4375 | 8445 | 0 | 0 | 0 |
| kimi | answer_first_bounded | 6/31/32 | 4636 | 2984 | 7620 | 0 | 0 | 1 |
| kimi | evidence_first_bounded | 7/32/32 | 4766 | 3031 | 7797 | 0 | 0 | 0 |
| kimi | answer_first_unbounded | 7/32/32 | 4318 | 11356 | 15674 | 5 | 3 | 0 |
| kimi | evidence_first_unbounded | 7/32/32 | 4318 | 8004 | 12322 | 0 | 1 | 0 |

## 配对比较

| 模型 | 左 → 右 | 配对/缺失 | 正确次数 | 总token节省 | 改善/退步 | 缺用量配对 |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | answer_first_bounded → evidence_first_bounded | 32/0 | 3 → 10 | 2.0% | 10/3 | 0 |
| deepseek | answer_first_unbounded → evidence_first_unbounded | 32/0 | 2 → 22 | -4.1% | 20/0 | 0 |
| deepseek | answer_first_bounded → answer_first_unbounded | 32/0 | 3 → 2 | -27.2% | 0/1 | 0 |
| deepseek | evidence_first_bounded → evidence_first_unbounded | 32/0 | 10 → 22 | -35.1% | 16/4 | 0 |
| kimi | answer_first_bounded → evidence_first_bounded | 31/1 | 6 → 7 | 1.2% | 5/4 | 0 |
| kimi | answer_first_unbounded → evidence_first_unbounded | 32/0 | 7 → 7 | 21.4% | 5/5 | 0 |
| kimi | answer_first_bounded → answer_first_unbounded | 31/1 | 6 → 6 | -96.2% | 1/1 | 0 |
| kimi | evidence_first_bounded → evidence_first_unbounded | 32/0 | 7 → 7 | -58.0% | 3/3 | 0 |

每个比较只使用同模型、同题、同重复中两边都返回的配对。用量缺失时仅在两边用量均已知的子集计算节省，详见 analysis.json；未知不按零计。总 token = 输入 + 输出，缓存明细保存在原始 usage 中。这些是返回用量，不是账单；失败请求可能已计费。短提示词改变了措辞，不保证语义完全等价。有限采样、小题集，结果不能推断统计显著、不劣性或普遍有效。
