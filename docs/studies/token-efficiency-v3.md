# 执行前方案：分离字段顺序与依据限长

v2中“先依据后答案”同时改变多个要求。本轮用2×2设计，在同一长度要求内比较请求的字段顺序，在同一字段顺序内比较80字符上限。方案和程序先提交到GitHub，再执行真实请求。结果另写，不根据本轮成绩换题或补跑。

## 题目与预算

使用v2的全部12道程序参考题（6 Bayes、6 macro-F1），加python-aliasing、critical-path、balanced-json、expected-draws四道人工作答参考题，共16题、5类题型。选择基于已公开v2的数值难点、类型错误和规划现象；这是已知困难集上的机制探索，不是未见测试集，也不与v2总分横向拼接。沿用题目ID方便追踪，不把重复参数题当成新任务家族。

16题 × 每题2次 × 2模型 × 4条件 = **256次聊天请求**。DeepSeek deepseek-flash、Kimi kimi-k2.6；temperature=0.6、thinking=disabled、max_tokens=700、timeout=90秒，无重试、无按成绩停止、无补样。输出上限179200 token，输入和可能计费的失败请求另计，不承诺货币预算。调度seed=2026100302，按题/重复分区组，区组内随机模型与条件；串行执行、独立上下文，不传参考或前次响应。

## 四条件

|条件|字段顺序|依据长度要求|
|---|---|---|
|answer_first_bounded|answer、evidence|≤80 Unicode字符，包括空格标点|
|evidence_first_bounded|evidence、answer|≤80 Unicode字符，包括空格标点|
|answer_first_unbounded|answer、evidence|无明确字符上限，仍要求简短|
|evidence_first_unbounded|evidence、answer|无明确字符上限，仍要求简短|

四组都使用同一短系统前缀、仅两个JSON字段、非空字符串依据及答案与依据一致要求。只替换字段顺序短语、增删限长句。原题对答案类型的要求不变。机器可读完整提示见[token-efficiency-v3-plan.json](token-efficiency-v3-plan.json)。没有新增“仅答案”组；本轮不回答是否应完全移除解释。无明确上限仍受700输出token和“简短”要求约束。

## 预定分析

1. 保留原评分器：只判answer，原容差和严格类型不变；非法JSON、截断判错；请求失败为缺失，不填零。报告正确/返回/计划。
2. 四个简单效应：限长内先答案→先依据，不限长内先答案→先依据，先答案内限长→不限长，先依据内限长→不限长。按模型/题目/重复匹配，仅两组都返回才计配对；输入、输出、总token各自只用双方用量已知的配对，节省率=1−右侧总量/左侧总量。
3. 沿用v2的分层（类别、程序/人工参考）、重复稳定性、数值误差敏感性、返回请求延迟中位数/P90。每模型每条件只有32次，重复调用不等于32道独立题。
4. 拆分字段集合、依据非空、请求顺序、依据≤80字符的计数。**共同契约**对四组检查同类字段/非空依据/各自要求的顺序，均不限制长度；**本条件契约**对限长组额外检查80字符。两者都报告与答案正确的交集。不能把删除要求提高的合格率当成能力改善；答案类型由原判分器评估，依据是否真实不做自动语义判断。字符按Python len，即Unicode code point，不是字节或token。长短诊断统计所有可解析字符串依据，显示长度覆盖数、中位数、P90。
5. 简单效应沿用v2按题ID聚类bootstrap：2000次、seed=2026100301、百分位95%描述区间，保留同题全部有效重复；用量有缺失则隐藏token区间。没有多重比较修正、显著性或不劣性检验；相关参数题导致题簇也未必独立，不能把区间解读为总体能力范围。
6. 新增交互项：**(不限长时先依据−先答案) − (限长时先依据−先答案)**。只用同模型/题/重复四组都返回的完整区组；分别对正确率、共同契约且正确比例、每区组总token作差中之差再求均值。token不是节省百分比；任一完整区组缺用量则隐藏其token估计和区间。按题聚类2000次、同一seed计算描述区间；不足两个题簇不输出区间。报告完整区组/缺失数，不把四次请求当作四个独立样本。

请求顺序处理是提示干预，实际字段可能不遵守；主分析按分配条件，不按实际响应重分组。结果不能揭示内部推理机制。服务端版本、缓存、负载未控制，不把客户端延迟称作纯推理速度。保留负面结果和反例；文章观点清楚区分测量事实与解释假设。

## 复现

```bash
python -m peerlab efficiency --protocol token-efficiency-v3 --dataset peerlab/data/token-efficiency-v3.json --limit 16 --repeats 2 --seed 2026100302 --max-calls 256 --max-tokens 700 --timeout 90 --dry-run
# 去掉dry-run并指定全新目录才调用API
python -m peerlab efficiency --protocol token-efficiency-v3 --dataset peerlab/data/token-efficiency-v3.json --limit 16 --repeats 2 --seed 2026100302 --max-calls 256 --max-tokens 700 --timeout 90 --output runs/token-efficiency-v3
python -m peerlab analyze-efficiency runs/token-efficiency-v3/run.json --output runs/v3-recheck
```

发布run.json原始字节及SHA256、执行commit、机器计划、基础/多维度/交互JSON与Markdown、CSV、离线HTML和PNG/SVG图。离线重算不需要密钥；旧研究原始数据与分析口径保持不变。
