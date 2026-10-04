# 多维度分析

Percentile bootstrap resamples task clusters, not independent repeats; 2000 draws, fixed seed 2026100301.

Intervals describe this selected task set, are not adjusted for multiple comparisons and do not establish noninferiority.

Latency covers returned responses only; timeout durations and server load/cache are uncontrolled.

Contract checks field structure and evidence length/order, not semantic truth of explanations.

Scope rows overlap; categories/reference groups cannot be summed together.

## 按任务类别

| 模型 | 条件 | 范围 | 正确/返回/计划 | 契约合格且正确 | 延迟中位数ms | 延迟P90ms |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | native_control | all | 26/32/32 | 26 | 1175.0 | 1446.7 |
| deepseek | native_control | category:代码理解 | 2/2/2 | 2 | 973.0 | 1006.6 |
| deepseek | native_control | category:机器学习 | 8/12/12 | 8 | 1237.0 | 1446.7 |
| deepseek | native_control | category:概率推理 | 12/12/12 | 12 | 1176.0 | 1263.8 |
| deepseek | native_control | category:结构化输出 | 4/6/6 | 4 | 1105.0 | 1322.5 |
| deepseek | native_control | reference:generated | 20/24/24 | 20 | 1182.0 | 1440.1 |
| deepseek | native_control | reference:manual | 6/8/8 | 6 | 1050.5 | 1263.9 |
| deepseek | native_explicit | all | 28/32/32 | 28 | 1160.5 | 1611.8 |
| deepseek | native_explicit | category:代码理解 | 2/2/2 | 2 | 1172.5 | 1239.3 |
| deepseek | native_explicit | category:机器学习 | 9/12/12 | 9 | 1392.5 | 1671.2 |
| deepseek | native_explicit | category:概率推理 | 11/12/12 | 11 | 973.5 | 1234.6 |
| deepseek | native_explicit | category:结构化输出 | 6/6/6 | 6 | 1030.0 | 1397.0 |
| deepseek | native_explicit | reference:generated | 20/24/24 | 20 | 1168.0 | 1584.8 |
| deepseek | native_explicit | reference:manual | 8/8/8 | 8 | 1123.5 | 1367.0 |
| kimi | native_control | all | 10/32/32 | 10 | 3966.5 | 5531.5 |
| kimi | native_control | category:代码理解 | 2/2/2 | 2 | 2643.5 | 2795.9 |
| kimi | native_control | category:机器学习 | 0/12/12 | 0 | 5063.5 | 7635.9 |
| kimi | native_control | category:概率推理 | 4/12/12 | 4 | 3966.5 | 4151.6 |
| kimi | native_control | category:结构化输出 | 4/6/6 | 4 | 2293.5 | 2657.0 |
| kimi | native_control | reference:generated | 4/24/24 | 4 | 4146.0 | 6500.1 |
| kimi | native_control | reference:manual | 6/8/8 | 6 | 2378.0 | 2846.6 |
| kimi | native_explicit | all | 25/30/32 | 25 | 3817.0 | 6279.0 |
| kimi | native_explicit | category:代码理解 | 2/2/2 | 2 | 2731.5 | 2810.3 |
| kimi | native_explicit | category:机器学习 | 7/12/12 | 7 | 5206.5 | 7672.2 |
| kimi | native_explicit | category:概率推理 | 10/10/12 | 10 | 3744.5 | 4116.1 |
| kimi | native_explicit | category:结构化输出 | 6/6/6 | 6 | 2075.5 | 2251.0 |
| kimi | native_explicit | reference:generated | 17/22/24 | 17 | 4680.0 | 6655.0 |
| kimi | native_explicit | reference:manual | 8/8/8 | 8 | 2084.5 | 2692.1 |

## 两次采样的稳定性

| 模型 | 条件 | 完整任务 | 始终正确 | 对错变化 | 均可解析任务 | 答案完全相同 |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | native_control | 16 | 12 | 2 | 16 | 12 |
| deepseek | native_explicit | 16 | 13 | 2 | 16 | 9 |
| kimi | native_control | 16 | 5 | 0 | 15 | 10 |
| kimi | native_explicit | 14 | 10 | 3 | 14 | 9 |

## 数值误差敏感性（不改原判分）

| 模型 | 条件 | 数值题返回 | 有限数值答案 | 误差≤1e-6 | ≤1e-4 | ≤1e-2 | 绝对误差中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | native_control | 24 | 24 | 20 | 21 | 24 | 1.1281070745605692e-07 |
| deepseek | native_explicit | 24 | 24 | 20 | 23 | 23 | 9.004433730759598e-10 |
| kimi | native_control | 24 | 5 | 4 | 4 | 4 | 1.1281070745605692e-07 |
| kimi | native_explicit | 22 | 22 | 17 | 17 | 21 | 3.3985367886568696e-07 |

## 整体配对与任务聚类区间

| 模型 | 比较 | 有效/缺失 | 改善/退步 | 正确率差 | 95%描述区间 | 总token节省 | 95%描述区间 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | explicit_native_type | 32/0 | 4/2 | 0.0625 | [-0.09375, 0.21875] | -0.1669877970456004 | [-0.20435528415980914, -0.1296583841329689] |
| kimi | explicit_native_type | 30/2 | 16/0 | 0.5333333333333333 | [0.3, 0.7333333333333333] | -0.0993890020366599 | [-0.20714806709891126, 0.01989305479835559] |

各题型的完整配对、输入/输出token与缺失数见 dimensions.json。区间不是总体能力估计；不能据区间覆盖0宣称等价。
