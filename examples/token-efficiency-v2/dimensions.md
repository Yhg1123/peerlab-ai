# 多维度分析

Percentile bootstrap resamples task clusters, not independent repeats; 2000 draws, fixed seed 2026100301.

Intervals describe this selected task set, are not adjusted for multiple comparisons and do not establish noninferiority.

Latency covers returned responses only; timeout durations and server load/cache are uncontrolled.

Contract checks field structure and evidence length/order, not semantic truth of explanations.

Scope rows overlap; categories/reference groups cannot be summed together.

## 按任务类别

| 模型 | 条件 | 范围 | 正确/返回/计划 | 契约合格且正确 | 延迟中位数ms | 延迟P90ms |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | verbose_explain | all | 13/48/48 | 13 | 1169.5 | 1539.7 |
| deepseek | verbose_explain | category:事实约束 | 2/2/2 | 2 | 948.0 | 1074.4 |
| deepseek | verbose_explain | category:代码理解 | 4/4/4 | 4 | 1306.0 | 1340.2 |
| deepseek | verbose_explain | category:指令遵循 | 2/2/2 | 2 | 898.0 | 958.8 |
| deepseek | verbose_explain | category:数据分析 | 2/2/2 | 2 | 1003.5 | 1085.5 |
| deepseek | verbose_explain | category:机器学习 | 0/14/14 | 0 | 1442.5 | 1560.0 |
| deepseek | verbose_explain | category:概率推理 | 1/18/18 | 1 | 1080.5 | 1354.3 |
| deepseek | verbose_explain | category:约束规划 | 0/2/2 | 0 | 1356.0 | 1528.8 |
| deepseek | verbose_explain | category:结构化输出 | 0/2/2 | 0 | 1081.5 | 1267.5 |
| deepseek | verbose_explain | category:逻辑推理 | 2/2/2 | 2 | 1030.0 | 1154.0 |
| deepseek | verbose_explain | reference:generated | 1/24/24 | 1 | 1220.0 | 1543.3 |
| deepseek | verbose_explain | reference:manual | 12/24/24 | 12 | 1114.0 | 1398.4 |
| deepseek | compact_answer | all | 17/48/48 | 17 | 906.0 | 1123.0 |
| deepseek | compact_answer | category:事实约束 | 2/2/2 | 2 | 788.0 | 911.2 |
| deepseek | compact_answer | category:代码理解 | 4/4/4 | 4 | 704.0 | 837.6 |
| deepseek | compact_answer | category:指令遵循 | 2/2/2 | 2 | 729.0 | 816.2 |
| deepseek | compact_answer | category:数据分析 | 2/2/2 | 2 | 857.5 | 957.9 |
| deepseek | compact_answer | category:机器学习 | 0/14/14 | 0 | 970.0 | 1077.3 |
| deepseek | compact_answer | category:概率推理 | 4/18/18 | 4 | 951.5 | 1155.3 |
| deepseek | compact_answer | category:约束规划 | 0/2/2 | 0 | 832.0 | 870.4 |
| deepseek | compact_answer | category:结构化输出 | 1/2/2 | 1 | 899.5 | 1111.9 |
| deepseek | compact_answer | category:逻辑推理 | 2/2/2 | 2 | 879.0 | 979.0 |
| deepseek | compact_answer | reference:generated | 1/24/24 | 1 | 970.0 | 1127.0 |
| deepseek | compact_answer | reference:manual | 16/24/24 | 16 | 859.0 | 1031.3 |
| deepseek | compact_evidence | all | 40/48/48 | 27 | 1058.0 | 1299.3 |
| deepseek | compact_evidence | category:事实约束 | 2/2/2 | 2 | 828.0 | 836.8 |
| deepseek | compact_evidence | category:代码理解 | 4/4/4 | 2 | 1155.5 | 1261.3 |
| deepseek | compact_evidence | category:指令遵循 | 2/2/2 | 2 | 930.5 | 1006.9 |
| deepseek | compact_evidence | category:数据分析 | 2/2/2 | 2 | 957.5 | 1043.5 |
| deepseek | compact_evidence | category:机器学习 | 8/14/14 | 0 | 1124.5 | 1425.4 |
| deepseek | compact_evidence | category:概率推理 | 16/18/18 | 13 | 1040.5 | 1299.3 |
| deepseek | compact_evidence | category:约束规划 | 2/2/2 | 2 | 832.0 | 906.4 |
| deepseek | compact_evidence | category:结构化输出 | 2/2/2 | 2 | 1068.0 | 1081.6 |
| deepseek | compact_evidence | category:逻辑推理 | 2/2/2 | 2 | 1071.0 | 1172.6 |
| deepseek | compact_evidence | reference:generated | 17/24/24 | 8 | 1124.5 | 1351.2 |
| deepseek | compact_evidence | reference:manual | 23/24/24 | 19 | 953.5 | 1173.5 |
| kimi | verbose_explain | all | 18/48/48 | 18 | 4283.5 | 14222.3 |
| kimi | verbose_explain | category:事实约束 | 2/2/2 | 2 | 1733.5 | 1835.5 |
| kimi | verbose_explain | category:代码理解 | 4/4/4 | 4 | 3268.5 | 3630.9 |
| kimi | verbose_explain | category:指令遵循 | 2/2/2 | 2 | 1987.0 | 1994.2 |
| kimi | verbose_explain | category:数据分析 | 1/2/2 | 1 | 3756.5 | 4831.3 |
| kimi | verbose_explain | category:机器学习 | 0/14/14 | 0 | 12490.5 | 15016.5 |
| kimi | verbose_explain | category:概率推理 | 6/18/18 | 6 | 4481.5 | 12249.6 |
| kimi | verbose_explain | category:约束规划 | 0/2/2 | 0 | 11133.5 | 11641.1 |
| kimi | verbose_explain | category:结构化输出 | 1/2/2 | 1 | 2920.5 | 3038.5 |
| kimi | verbose_explain | category:逻辑推理 | 2/2/2 | 2 | 3062.0 | 3218.8 |
| kimi | verbose_explain | reference:generated | 1/24/24 | 1 | 6887.5 | 14486.7 |
| kimi | verbose_explain | reference:manual | 17/24/24 | 17 | 3163.0 | 11876.5 |
| kimi | compact_answer | all | 17/48/48 | 17 | 1126.5 | 1233.6 |
| kimi | compact_answer | category:事实约束 | 2/2/2 | 2 | 1009.5 | 1061.1 |
| kimi | compact_answer | category:代码理解 | 4/4/4 | 4 | 1137.5 | 1286.1 |
| kimi | compact_answer | category:指令遵循 | 1/2/2 | 1 | 1273.0 | 1325.0 |
| kimi | compact_answer | category:数据分析 | 0/2/2 | 0 | 981.5 | 1021.9 |
| kimi | compact_answer | category:机器学习 | 0/14/14 | 0 | 1154.5 | 1246.4 |
| kimi | compact_answer | category:概率推理 | 6/18/18 | 6 | 1126.5 | 1222.3 |
| kimi | compact_answer | category:约束规划 | 0/2/2 | 0 | 1012.5 | 1048.9 |
| kimi | compact_answer | category:结构化输出 | 2/2/2 | 2 | 1052.5 | 1078.5 |
| kimi | compact_answer | category:逻辑推理 | 2/2/2 | 2 | 1090.0 | 1101.2 |
| kimi | compact_answer | reference:generated | 1/24/24 | 1 | 1136.5 | 1223.4 |
| kimi | compact_answer | reference:manual | 16/24/24 | 16 | 1080.5 | 1288.8 |
| kimi | compact_evidence | all | 22/48/48 | 10 | 3001.0 | 4182.0 |
| kimi | compact_evidence | category:事实约束 | 2/2/2 | 2 | 1349.5 | 1363.5 |
| kimi | compact_evidence | category:代码理解 | 2/4/4 | 0 | 2770.0 | 2960.9 |
| kimi | compact_evidence | category:指令遵循 | 2/2/2 | 2 | 2418.0 | 2517.2 |
| kimi | compact_evidence | category:数据分析 | 2/2/2 | 0 | 1973.0 | 1995.4 |
| kimi | compact_evidence | category:机器学习 | 0/14/14 | 0 | 3700.0 | 4459.9 |
| kimi | compact_evidence | category:概率推理 | 8/18/18 | 1 | 3055.0 | 3783.8 |
| kimi | compact_evidence | category:约束规划 | 2/2/2 | 1 | 2490.0 | 2502.8 |
| kimi | compact_evidence | category:结构化输出 | 2/2/2 | 2 | 2376.5 | 2488.9 |
| kimi | compact_evidence | category:逻辑推理 | 2/2/2 | 2 | 2173.5 | 2198.7 |
| kimi | compact_evidence | reference:generated | 6/24/24 | 0 | 3300.0 | 4194.0 |
| kimi | compact_evidence | reference:manual | 16/24/24 | 10 | 2511.5 | 3574.7 |

## 两次采样的稳定性

| 模型 | 条件 | 完整任务 | 始终正确 | 对错变化 | 均可解析任务 | 答案完全相同 |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek | verbose_explain | 24 | 6 | 1 | 23 | 9 |
| deepseek | compact_answer | 24 | 7 | 3 | 24 | 8 |
| deepseek | compact_evidence | 24 | 17 | 6 | 24 | 13 |
| kimi | verbose_explain | 24 | 7 | 4 | 14 | 8 |
| kimi | compact_answer | 24 | 7 | 3 | 22 | 8 |
| kimi | compact_evidence | 24 | 9 | 4 | 24 | 12 |

## 数值误差敏感性（不改原判分）

| 模型 | 条件 | 数值题返回 | 有限数值答案 | 误差≤1e-6 | ≤1e-4 | ≤1e-2 | 绝对误差中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | verbose_explain | 36 | 33 | 3 | 7 | 16 | 0.0757566666666667 |
| deepseek | compact_answer | 36 | 36 | 5 | 11 | 19 | 0.005520752244548968 |
| deepseek | compact_evidence | 36 | 36 | 24 | 29 | 31 | 2.5224454897054827e-07 |
| kimi | verbose_explain | 36 | 23 | 5 | 9 | 14 | 0.0012709526087607004 |
| kimi | compact_answer | 36 | 35 | 5 | 8 | 22 | 0.0018515435506901712 |
| kimi | compact_evidence | 36 | 32 | 11 | 21 | 26 | 2.3002284820772267e-06 |

## 整体配对与任务聚类区间

| 模型 | 比较 | 有效/缺失 | 改善/退步 | 正确率差 | 95%描述区间 | 总token节省 | 95%描述区间 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek | combined | 48/0 | 4/0 | 0.08333333333333333 | [0.0, 0.1875] | 0.5227966336816794 | [0.4838840293182854, 0.5582271382679634] |
| deepseek | evidence_vs_answer | 48/0 | 23/0 | 0.4791666666666667 | [0.3125, 0.6458333333333334] | -0.6945736434108527 | [-0.7816177110723692, -0.6142610405569734] |
| deepseek | evidence_vs_baseline | 48/0 | 27/0 | 0.5625 | [0.3958333333333333, 0.7291666666666666] | 0.1913437528900398 | [0.1511003232972343, 0.23258184791591294] |
| kimi | combined | 48/0 | 3/4 | -0.020833333333333332 | [-0.10416666666666667, 0.041666666666666664] | 0.6756823698419775 | [0.5839811444833205, 0.7388500948751725] |
| kimi | evidence_vs_answer | 48/0 | 10/5 | 0.10416666666666667 | [-0.0625, 0.2916666666666667] | -0.7391171528944556 | [-0.961767081201989, -0.4783608996725107] |
| kimi | evidence_vs_baseline | 48/0 | 9/5 | 0.08333333333333333 | [-0.08333333333333333, 0.2708333333333333] | 0.4359736464061029 | [0.32008077252603406, 0.511913736389101] |

各题型的完整配对、输入/输出token与缺失数见 dimensions.json。区间不是总体能力估计；不能据区间覆盖0宣称等价。
