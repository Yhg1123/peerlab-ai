# 执行前方案：明确JSON类型能否提高可用答案率

v3里Kimi多次把数字或数组写成字符串。本轮测试同一句明确的JSON原生类型要求，在新参数和新题目上能否减少这种错误，以及它的token成本。代码、题集和机器计划在真实调用前提交到GitHub；不按成绩换题、补跑或修改评分。

## 干预与问题

控制组`native_control`逐字复用v3的`evidence_first_unbounded`系统提示。实验组`native_explicit`仅在其后添加：

> answer必须使用题目要求的JSON原生类型：数值题使用number，数组题使用array；不得把数字或数组写成带引号的字符串。

两组都先evidence后answer、依据非空且简短，无明确字符上限、要求答案与依据一致。题目本身已有数值/数组类型要求，因此测的是**强化类型提醒**的增量作用，不是“有要求”与“无要求”。不使用供应商强制JSON Schema，不修改输出后处理，不增加二次修复请求。更明确的提醒也多占输入token，按实际usage计入。

## 新题、采样与预算

- 16题：6 Bayes、6 macro-F1、4数组任务（稳定去重、排序、转置、引用与复制）。12道数值参考由Fraction精确计算，4道数组参考人工写出并独立复核。类型分层为12个number任务、4个array任务。
- [生成脚本](../../scripts/build_native_dataset.py)对两个数值家族各以seed=2026100401抽取30个候选，按候选顺序排除前五轮出现过的完整prompt，各取前6个；不足则失败而不自动换seed。固定4道新数组题。完整prompt与此前所有已发布题目无重复，在API运行前验证。
- 新参数不是新领域；Bayes、macro-F1和数组题仍属于已知家族，不能称为未污染的外部测试集。题型选择来自v3观察，这也是局限。模型可能曾见过相似问题，无法排除预训练覆盖。
- 16×2重复×2模型×2条件=**128次聊天请求**；每模型每条件32次。DeepSeek deepseek-flash与Kimi kimi-k2.6，temperature=0.6、thinking=disabled、max_tokens=700、timeout=90秒。无重试、无成绩提前停止、无替补。
- 输出理论上限89,600 token；输入和可能计费的失败请求额外计入，不承诺货币费用上限。种子2026100402只控制区组与区组内串行随机顺序，不控制供应商采样。独立请求，不传参考或前次输出。

## 固定指标

1. **正式质量**：完全沿用现有grader，仅判answer。数值绝对误差≤1e-6；数组严格比较类型、顺序、结构和值。字符串不转数字/数组，不从解释提取答案。截断/非法JSON记错，网络失败记缺失。
2. **类型端点**：完整可解析响应中，number题只接受有限int/float且排除bool，array题只检查最外层是list。数组元素错型或内容错仍可能“外层类型正确”，但不能通过正式质量。非法JSON、截断都不是类型合格。明确类型要求中的array不意味着字符串数组的每个元素都禁止使用引号。
3. **互斥分解**：请求失败、pending、未尝试、截断、非法JSON、原生类型错误、类型正确但答案错误、正确。每模型/条件/范围内总数等于计划数；wrong-type字符串另列record ID供复核，不二次解码、不重判。
4. **配对**：两模型分别比较控制→明确类型，按同题/重复、双方返回的配对计算正确率差、类型合格率差、改善/退步、输入/输出/总token及每个正确答案的token。用量各指标要求两边都已知，未知不填0；不把全组总量在缺失不同时直接相除。未预先设业务质量门槛，不宣称业务可用或不劣。
5. **分层与稳定性**：沿用v2的题型、程序/人工参考、重复稳定性、容差敏感性、返回调用延迟中位数/P90；类型端点另外按number/array分层。分组重叠不能相加。延迟不包含失败超时，也不是纯推理速度。
6. **契约**：两组同样要求仅evidence、answer两字段，evidence非空字符串且在前；无长度限制。此结构契约与answer类型指标分开，避免混淆。依据语义真实性不自动评分。
7. **描述区间**：整体正确率差、类型合格率差和配对总token节省沿用按题ID聚类bootstrap，2000次，seed=2026100301，百分位95%；保留同题全部有效重复。若总token有未知则不输出token区间；不足两个题簇不输出区间。参数题之间也可能相关，无多重校正，不作总体推断、显著性或等价性声明。

主结果按分配条件分析，不能事后只保留符合类型的响应再称质量提升。类型改善但算术仍错误是预期要保留的负面结果。解释中的正确值不能替代错误answer。没有执行自动修复实验，因此不声称节省了修复调用的实际成本。

## 复现和交付

```bash
python scripts/build_native_dataset.py --output runs/native-cases.json
python -m peerlab efficiency --protocol token-efficiency-v4 --dataset peerlab/data/token-efficiency-v4.json --limit 16 --repeats 2 --seed 2026100402 --max-calls 128 --max-tokens 700 --timeout 90 --dry-run
# 实际调用需要去掉dry-run，指定新目录
python -m peerlab efficiency --protocol token-efficiency-v4 --dataset peerlab/data/token-efficiency-v4.json --limit 16 --repeats 2 --seed 2026100402 --max-calls 128 --max-tokens 700 --timeout 90 --output runs/token-efficiency-v4
python -m peerlab analyze-efficiency runs/token-efficiency-v4/run.json --output runs/v4-recheck
```

公开原始run.json及SHA256、执行commit、[机器计划](token-efficiency-v4-plan.json)、基础配对与多维度分析、types.json/types.md、离线HTML、科学图表、逐条CSV和结果解读。README首页列出四组数据与正反结论。旧研究按原协议保留，不合并为同一个样本。
