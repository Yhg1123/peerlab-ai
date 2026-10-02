# Token 效率实验

Run: `33399d5f51554e6d8cdb3286ecda39a0` · partial · 请求尝试 96

| 模型 | 条件 | 正确/返回/计划 | 已知输入 token | 已知输出 token | 已知总 token | JSON失败 | 未完整输出 | 请求失败 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | verbose_explain | 3/12/12 | 1445 | 1392 | 2837 | 0 | 0 | 0 |
| deepseek | verbose_answer | 3/12/12 | 1445 | 116 | 1561 | 1 | 0 | 0 |
| deepseek | compact_explain | 3/12/12 | 1205 | 1790 | 2995 | 0 | 1 | 0 |
| deepseek | compact_answer | 3/11/12 | 1108 | 105 | 1213 | 0 | 0 | 1 |
| kimi | verbose_explain | 3/12/12 | 1490 | 3875 | 5365 | 3 | 1 | 0 |
| kimi | verbose_answer | 3/12/12 | 1490 | 217 | 1707 | 0 | 0 | 0 |
| kimi | compact_explain | 3/12/12 | 1274 | 3014 | 4288 | 1 | 0 | 0 |
| kimi | compact_answer | 3/12/12 | 1274 | 211 | 1485 | 0 | 0 | 0 |

## 配对比较

| 模型 | 左 → 右 | 配对/缺失 | 正确题数 | 总token节省 | 改善/退步 | 缺用量配对 |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | verbose_explain → compact_answer | 11/1 | 3 → 3 | 53.9% | 0/0 | 0 |
| deepseek | verbose_explain → compact_explain | 12/0 | 3 → 3 | -5.6% | 0/0 | 0 |
| deepseek | verbose_answer → compact_answer | 11/1 | 3 → 3 | 15.5% | 0/0 | 0 |
| deepseek | verbose_explain → verbose_answer | 12/0 | 3 → 3 | 45.0% | 0/0 | 0 |
| deepseek | compact_explain → compact_answer | 11/1 | 3 → 3 | 57.3% | 0/0 | 0 |
| kimi | verbose_explain → compact_answer | 12/0 | 3 → 3 | 72.3% | 0/0 | 0 |
| kimi | verbose_explain → compact_explain | 12/0 | 3 → 3 | 20.1% | 0/0 | 0 |
| kimi | verbose_answer → compact_answer | 12/0 | 3 → 3 | 13.0% | 0/0 | 0 |
| kimi | verbose_explain → verbose_answer | 12/0 | 3 → 3 | 68.2% | 0/0 | 0 |
| kimi | compact_explain → compact_answer | 12/0 | 3 → 3 | 65.4% | 0/0 | 0 |

每个比较只使用同模型、同题、同重复中两边都返回的配对。用量缺失时仅在两边用量均已知的子集计算节省，详见 analysis.json；未知不按零计。总 token = 输入 + 输出，缓存明细保存在原始 usage 中。这些是返回用量，不是账单；失败请求可能已计费。短提示词改变了措辞，不保证语义完全等价。单次采样、小题集，结果不能推断统计显著、不劣性或普遍有效。
