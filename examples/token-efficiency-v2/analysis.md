# Token 效率实验

Run: `cb271745c85346c3b4db8fae38ce1422` · complete · 请求尝试 288

| 模型 | 条件 | 正确/返回/计划 | 已知输入 token | 已知输出 token | 已知总 token | JSON失败 | 未完整输出 | 请求失败 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | verbose_explain | 13/48/48 | 5670 | 5143 | 10813 | 2 | 0 | 0 |
| deepseek | compact_answer | 17/48/48 | 4710 | 450 | 5160 | 0 | 0 | 0 |
| deepseek | compact_evidence | 40/48/48 | 5622 | 3122 | 8744 | 0 | 0 | 0 |
| kimi | verbose_explain | 18/48/48 | 5830 | 14357 | 20187 | 8 | 5 | 0 |
| kimi | compact_answer | 17/48/48 | 4966 | 1581 | 6547 | 1 | 1 | 0 |
| kimi | compact_evidence | 22/48/48 | 5830 | 5556 | 11386 | 0 | 0 | 0 |

## 配对比较

| 模型 | 左 → 右 | 配对/缺失 | 正确题数 | 总token节省 | 改善/退步 | 缺用量配对 |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | verbose_explain → compact_answer | 48/0 | 13 → 17 | 52.3% | 4/0 | 0 |
| deepseek | compact_answer → compact_evidence | 48/0 | 17 → 40 | -69.5% | 23/0 | 0 |
| deepseek | verbose_explain → compact_evidence | 48/0 | 13 → 40 | 19.1% | 27/0 | 0 |
| kimi | verbose_explain → compact_answer | 48/0 | 18 → 17 | 67.6% | 3/4 | 0 |
| kimi | compact_answer → compact_evidence | 48/0 | 17 → 22 | -73.9% | 10/5 | 0 |
| kimi | verbose_explain → compact_evidence | 48/0 | 18 → 22 | 43.6% | 9/5 | 0 |

每个比较只使用同模型、同题、同重复中两边都返回的配对。用量缺失时仅在两边用量均已知的子集计算节省，详见 analysis.json；未知不按零计。总 token = 输入 + 输出，缓存明细保存在原始 usage 中。这些是返回用量，不是账单；失败请求可能已计费。短提示词改变了措辞，不保证语义完全等价。有限采样、小题集，结果不能推断统计显著、不劣性或普遍有效。
