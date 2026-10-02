# 多维度分析

Percentile bootstrap resamples task clusters, not independent repeats; 2000 draws, fixed seed 2026100301.

Intervals describe this selected task set, are not adjusted for multiple comparisons and do not establish noninferiority.

Latency covers returned responses only; timeout durations and server load/cache are uncontrolled.

Contract checks field structure and evidence length/order, not semantic truth of explanations.

Scope rows overlap; categories/reference groups cannot be summed together.

## 按任务类别

| 模型 | 条件 | 范围 | 正确/返回/计划 | 契约合格且正确 | 延迟中位数ms | 延迟P90ms |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | answer_first_bounded | all | 3/32/32 | 3 | 975.5 | 1177.9 |
| deepseek | answer_first_bounded | category:代码理解 | 2/2/2 | 2 | 1015.5 | 1027.9 |
| deepseek | answer_first_bounded | category:机器学习 | 0/12/12 | 0 | 1001.5 | 1200.6 |
| deepseek | answer_first_bounded | category:概率推理 | 0/14/14 | 0 | 899.0 | 1124.5 |
| deepseek | answer_first_bounded | category:约束规划 | 0/2/2 | 0 | 964.0 | 1096.0 |
| deepseek | answer_first_bounded | category:结构化输出 | 1/2/2 | 1 | 905.5 | 976.3 |
| deepseek | answer_first_bounded | reference:generated | 0/24/24 | 0 | 945.5 | 1175.7 |
| deepseek | answer_first_bounded | reference:manual | 3/8/8 | 3 | 997.0 | 1165.9 |
| deepseek | evidence_first_bounded | all | 10/32/32 | 7 | 1017.0 | 1364.1 |
| deepseek | evidence_first_bounded | category:代码理解 | 0/2/2 | 0 | 748.5 | 780.1 |
| deepseek | evidence_first_bounded | category:机器学习 | 4/12/12 | 2 | 1112.5 | 1396.1 |
| deepseek | evidence_first_bounded | category:概率推理 | 4/14/14 | 3 | 880.0 | 1156.9 |
| deepseek | evidence_first_bounded | category:约束规划 | 1/2/2 | 1 | 1044.5 | 1064.1 |
| deepseek | evidence_first_bounded | category:结构化输出 | 1/2/2 | 1 | 860.5 | 878.5 |
| deepseek | evidence_first_bounded | reference:generated | 8/24/24 | 5 | 1054.0 | 1370.7 |
| deepseek | evidence_first_bounded | reference:manual | 2/8/8 | 2 | 860.5 | 1050.8 |
| deepseek | answer_first_unbounded | all | 2/32/32 | 2 | 1129.0 | 1560.7 |
| deepseek | answer_first_unbounded | category:代码理解 | 2/2/2 | 2 | 1156.5 | 1257.7 |
| deepseek | answer_first_unbounded | category:机器学习 | 0/12/12 | 0 | 1335.0 | 1560.7 |
| deepseek | answer_first_unbounded | category:概率推理 | 0/14/14 | 0 | 983.5 | 1640.5 |
| deepseek | answer_first_unbounded | category:约束规划 | 0/2/2 | 0 | 953.5 | 1072.3 |
| deepseek | answer_first_unbounded | category:结构化输出 | 0/2/2 | 0 | 959.5 | 998.3 |
| deepseek | answer_first_unbounded | reference:generated | 0/24/24 | 0 | 1173.0 | 1534.1 |
| deepseek | answer_first_unbounded | reference:manual | 2/8/8 | 2 | 1019.0 | 1661.9 |
| deepseek | evidence_first_unbounded | all | 22/32/32 | 22 | 1184.5 | 1507.1 |
| deepseek | evidence_first_unbounded | category:代码理解 | 2/2/2 | 2 | 1050.5 | 1079.7 |
| deepseek | evidence_first_unbounded | category:机器学习 | 4/12/12 | 4 | 1291.5 | 1649.5 |
| deepseek | evidence_first_unbounded | category:概率推理 | 12/14/14 | 12 | 1160.0 | 1379.7 |
| deepseek | evidence_first_unbounded | category:约束规划 | 2/2/2 | 2 | 788.5 | 850.5 |
| deepseek | evidence_first_unbounded | category:结构化输出 | 2/2/2 | 2 | 922.0 | 1036.4 |
| deepseek | evidence_first_unbounded | reference:generated | 15/24/24 | 15 | 1205.0 | 1497.7 |
| deepseek | evidence_first_unbounded | reference:manual | 7/8/8 | 7 | 1039.5 | 1236.7 |
| kimi | answer_first_bounded | all | 6/31/32 | 6 | 1885.0 | 2843.0 |
| kimi | answer_first_bounded | category:代码理解 | 2/2/2 | 2 | 1362.5 | 1382.1 |
| kimi | answer_first_bounded | category:机器学习 | 0/12/12 | 0 | 2350.5 | 2947.4 |
| kimi | answer_first_bounded | category:概率推理 | 2/13/14 | 2 | 1725.0 | 1925.2 |
| kimi | answer_first_bounded | category:约束规划 | 0/2/2 | 0 | 3056.0 | 3642.4 |
| kimi | answer_first_bounded | category:结构化输出 | 2/2/2 | 2 | 1810.5 | 1870.1 |
| kimi | answer_first_bounded | reference:generated | 1/24/24 | 1 | 1956.0 | 2825.0 |
| kimi | answer_first_bounded | reference:manual | 5/7/8 | 5 | 1862.0 | 2909.4 |
| kimi | evidence_first_bounded | all | 7/32/32 | 2 | 2140.0 | 2706.8 |
| kimi | evidence_first_bounded | category:代码理解 | 0/2/2 | 0 | 1338.5 | 1362.9 |
| kimi | evidence_first_bounded | category:机器学习 | 0/12/12 | 0 | 2521.0 | 2744.8 |
| kimi | evidence_first_bounded | category:概率推理 | 4/14/14 | 1 | 1967.5 | 2416.9 |
| kimi | evidence_first_bounded | category:约束规划 | 2/2/2 | 0 | 2402.0 | 2440.4 |
| kimi | evidence_first_bounded | category:结构化输出 | 1/2/2 | 1 | 1866.0 | 1965.2 |
| kimi | evidence_first_bounded | reference:generated | 4/24/24 | 1 | 2180.0 | 2670.4 |
| kimi | evidence_first_bounded | reference:manual | 3/8/8 | 1 | 1959.0 | 2630.6 |
| kimi | answer_first_unbounded | all | 7/32/32 | 7 | 5376.0 | 10202.0 |
| kimi | answer_first_unbounded | category:代码理解 | 2/2/2 | 2 | 2565.5 | 2666.7 |
| kimi | answer_first_unbounded | category:机器学习 | 0/12/12 | 0 | 7030.5 | 11283.8 |
| kimi | answer_first_unbounded | category:概率推理 | 3/14/14 | 3 | 6145.5 | 9978.8 |
| kimi | answer_first_unbounded | category:约束规划 | 0/2/2 | 0 | 4839.0 | 5318.2 |
| kimi | answer_first_unbounded | category:结构化输出 | 2/2/2 | 2 | 2560.0 | 2719.2 |
| kimi | answer_first_unbounded | reference:generated | 1/24/24 | 1 | 6772.5 | 11133.4 |
| kimi | answer_first_unbounded | reference:manual | 6/8/8 | 6 | 3499.5 | 9225.6 |
| kimi | evidence_first_unbounded | all | 7/32/32 | 7 | 3341.5 | 7715.4 |
| kimi | evidence_first_unbounded | category:代码理解 | 0/2/2 | 0 | 2743.0 | 3031.0 |
| kimi | evidence_first_unbounded | category:机器学习 | 0/12/12 | 0 | 4964.0 | 7715.4 |
| kimi | evidence_first_unbounded | category:概率推理 | 4/14/14 | 4 | 3174.5 | 7089.9 |
| kimi | evidence_first_unbounded | category:约束规划 | 2/2/2 | 2 | 2729.5 | 2888.3 |
| kimi | evidence_first_unbounded | category:结构化输出 | 1/2/2 | 1 | 2550.0 | 2805.2 |
| kimi | evidence_first_unbounded | reference:generated | 4/24/24 | 4 | 3676.0 | 7248.9 |
| kimi | evidence_first_unbounded | reference:manual | 3/8/8 | 3 | 2898.5 | 9712.2 |

## 两次采样的稳定性

| 模型 | 条件 | 完整任务 | 始终正确 | 对错变化 | 均可解析任务 | 答案完全相同 |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | answer_first_bounded | 16 | 1 | 1 | 16 | 4 |
| deepseek | evidence_first_bounded | 16 | 1 | 8 | 16 | 4 |
| deepseek | answer_first_unbounded | 16 | 1 | 0 | 16 | 4 |
| deepseek | evidence_first_unbounded | 16 | 9 | 4 | 16 | 8 |
| kimi | answer_first_bounded | 15 | 2 | 1 | 15 | 3 |
| kimi | evidence_first_bounded | 16 | 2 | 3 | 16 | 3 |
| kimi | answer_first_unbounded | 16 | 3 | 1 | 9 | 3 |
| kimi | evidence_first_unbounded | 16 | 2 | 3 | 15 | 6 |

## 数值误差敏感性（不改原判分）

| 模型 | 条件 | 数值题返回 | 有限数值答案 | 误差≤1e-6 | ≤1e-4 | ≤1e-2 | 绝对误差中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | answer_first_bounded | 28 | 26 | 0 | 3 | 12 | 0.09482053212914848 |
| deepseek | evidence_first_bounded | 28 | 26 | 9 | 16 | 22 | 1.6915549911178385e-05 |
| deepseek | answer_first_unbounded | 28 | 28 | 0 | 6 | 12 | 0.08382446031746033 |
| deepseek | evidence_first_unbounded | 28 | 28 | 17 | 19 | 27 | 2.5224454897054827e-07 |
| kimi | answer_first_bounded | 27 | 27 | 1 | 4 | 14 | 0.001948543550690185 |
| kimi | evidence_first_bounded | 28 | 14 | 6 | 10 | 13 | 1.1339394723058893e-06 |
| kimi | answer_first_unbounded | 28 | 20 | 1 | 4 | 9 | 0.036097173893104906 |
| kimi | evidence_first_unbounded | 28 | 10 | 6 | 10 | 10 | 3.964996850569502e-07 |

## 整体配对与任务聚类区间

| 模型 | 比较 | 有效/缺失 | 改善/退步 | 正确率差 | 95%描述区间 | 总token节省 | 95%描述区间 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | order_bounded | 32/0 | 10/3 | 0.21875 | [0.0, 0.4375] | 0.020059551794389563 | [-0.0028387361936020815, 0.04295265054378554] |
| deepseek | order_unbounded | 32/0 | 20/0 | 0.625 | [0.40625, 0.8125] | -0.040537210448496896 | [-0.12409014387414957, 0.044672336278391074] |
| deepseek | remove_cap_answer_first | 32/0 | 0/1 | -0.03125 | [-0.09375, 0.0] | -0.2719009559630152 | [-0.4552108270586868, -0.14060339055089438] |
| deepseek | remove_cap_evidence_first | 32/0 | 16/4 | 0.375 | [0.125, 0.625] | -0.3505517351671197 | [-0.44661787967264155, -0.2701100835557098] |
| kimi | order_bounded | 31/1 | 5/4 | 0.03225806451612903 | [-0.20689655172413793, 0.25] | 0.011942257217847807 | [-0.040901287337075216, 0.06647316434236501] |
| kimi | order_unbounded | 32/0 | 5/5 | 0.0 | [-0.25, 0.21875] | 0.213857343371188 | [0.08174720683631144, 0.32954167999080725] |
| kimi | remove_cap_answer_first | 31/1 | 1/1 | 0.0 | [0.0, 0.0] | -0.9618110236220472 | [-1.22194053042599, -0.7066955663741643] |
| kimi | remove_cap_evidence_first | 32/0 | 3/3 | 0.0 | [-0.125, 0.125] | -0.5803514172117481 | [-0.8671741312598293, -0.3676439315958942] |

各题型的完整配对、输入/输出token与缺失数见 dimensions.json。区间不是总体能力估计；不能据区间覆盖0宣称等价。
