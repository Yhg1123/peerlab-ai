# 顺序 × 依据长度：分解诊断

Common contract: exact fields, nonblank string evidence, requested order; no length limit for any arm.

Arm contract additionally enforces 80 Unicode code points only for bounded arms; answer types are assessed by the unchanged grader.

within_80 is measured identically in all arms, not a requirement for unbounded arms.

Interaction uses complete four-arm task/repeat blocks; unknown usage suppresses its token estimate and interval.

Selected known tasks; repeated parameter variants are not independent task families. Bootstrap is descriptive, not a population claim.

|模型|条件|返回|共同契约且正确|本条件契约且正确|≤80字符|依据长度中位数/P90|
|---|---|---:|---:|---:|---:|---|
|deepseek|answer_first_bounded|32|3|3|27|63.0 / 84.9|
|deepseek|evidence_first_bounded|32|10|7|25|65.0 / 88.7|
|deepseek|answer_first_unbounded|32|2|2|5|107.5 / 306.10000000000014|
|deepseek|evidence_first_unbounded|32|22|22|2|170.0 / 292.40000000000003|
|kimi|answer_first_bounded|31|6|6|17|65 / 161.0|
|kimi|evidence_first_bounded|32|7|2|12|92.0 / 146.9|
|kimi|answer_first_unbounded|32|7|7|0|276.5 / 842.1999999999999|
|kimi|evidence_first_unbounded|32|7|7|0|222 / 639.0|

## 交互项

定义：(不限长时的先依据−先答案) − (限长时的先依据−先答案)。正确率单位为比例差，总token为每个完整区组的差中之差。区间按题聚类2000次；不做显著性结论。

### deepseek

完整区组32，缺失0，题目簇16。

- accuracy: 0.40625; 95%描述区间 [0.15625, 0.65625]
- common_contract_and_correct: 0.40625; 95%描述区间 [0.15625, 0.65625]
- total_tokens_per_block: 14.28125; 95%描述区间 [-6.446093749999999, 31.377343749999987]

### kimi

完整区组31，缺失1，题目簇16。

- accuracy: 0; 95%描述区间 [-0.12903225806451613, 0.12903225806451613]
- common_contract_and_correct: 0; 95%描述区间 [-0.12903225806451613, 0.12903225806451613]
- total_tokens_per_block: -108.12903225806451; 95%描述区间 [-171.8718497983871, -43.84162176724139]
