# 执行前方案：24题、两次采样的多维度效率研究

本方案在真实请求前提交；结果另写findings，旧研究不改写、不合并成新样本。对应机器可读计划：[token-efficiency-v2-plan.json](token-efficiency-v2-plan.json)。

## 研究问题

前轮单次采样显示输出压缩节省token，但正确率低。本轮增加题量和每题重复，同时探索“先给简短核验依据、再给答案”的响应契约。问题是：压缩是否仍有效、得分是否随题型变化、同题两次是否稳定、解释新契约是否改变质量和用量。

## 设计与预算

- 24题：6道Bayes、6道macro-F1，使用已有有理数生成器seed=2026100301；另加原始题库全部12题，不根据本轮结果挑选。生成题ID前加v2-避免跨研究混淆。12道生成参考可程序复核，12道人工作答参考沿用旧库；旧库不是未见测试集。数据集快照：[token-efficiency-v2.json](../../peerlab/data/token-efficiency-v2.json)。
- 每模型每题每条件独立采样2次。24×2重复×2模型×3条件=**288次聊天请求**，无重试、无按成绩停止或补跑。
- DeepSeek deepseek-flash，Kimi kimi-k2.6；temperature=0.6，thinking=disabled，max_tokens=700，timeout=90秒；两模型与三条件参数相同。输出理论上限201600token，输入、可能已计费的失败请求额外计入。seed只控制串行调度，非供应商随机种子。
- 复用v1的verbose_explain、compact_answer作为主比较；新增compact_evidence。新条件用与compact_answer相同的短前缀，要求一个JSON对象，先evidence（≤80个Unicode字符的简短计算依据/核验结果），再answer，要求两字段一致。程序只检查字段、顺序和长度；不自动判断依据语义真实性，也不要求隐藏思考过程。
- 新条件同时改变输出顺序、内容、长度和一致性提醒。它是整体策略探索，**不能隔离“顺序”的因果效应**；v1四因素条件未在本轮完整复跑，不将本轮称作2×2实验。
- 调度seed=2026100301，先打乱题目/重复区组，再打乱区组内模型/条件；完全独立请求，不传前一个响应，不传参考答案。每个请求前记录pending，异常和中断留存。模型名预检不计为聊天请求。

## 固定指标与解释边界

1. **质量与缺失**：原题原判分、只判answer；数值绝对误差沿用每题tolerance，结构化答案严格比较；截断/JSON失败判错，HTTP失败记缺失。报告正确/返回/计划、正确率（分母返回）、交付正确比例（分母计划），不掩盖请求失败。
2. **用量**：主比较verbose_explain→compact_answer；次比较compact_answer→compact_evidence及verbose_explain→compact_evidence。按同模型/题目/重复有效配对统计输入、输出、总token；用量缺失从对应token计算的两侧同时排除，不填零、不换算账单。整体与每题类别、生成/人工参考分层均报告，分层有重叠不能相加。
3. **输出契约**：三条件分别要求answer+非空explanation、仅answer、evidence先于answer且字符串长度1—80。单个完整JSON允许整段代码围栏，与旧解析器一致；重复键、多个JSON块、非有限字面量拒绝。该指标比answer评分额外检查输出字段；同时报告契约合格且正确的数量。解释语义质量不在自动评价范围。
4. **稳定性**：按题聚合两次返回；报告两次都正确、一次对一次错、两次都可解析时类型敏感的答案序列化完全相同的题数。缺一次的题不能当不稳定或稳定。相同错误也是稳定，不能将一致性当正确性。
5. **数值误差敏感性**：对所有返回的数值题额外列绝对误差≤1e-6、≤1e-4、≤1e-2的数量，非法/截断输出仍不能通过。只作诊断，不改正式分数；不同题尺度不同，阈值不能代表统一业务容忍度。
6. **延迟**：返回响应的客户端整次调用耗时中位数、P90，P90用排序线性插值；记录已知/缺失数。不包含失败请求超时耗时，不解释为纯模型速度，缓存/负载/网络未控制。
7. **不确定性**：整体三项比较各模型按题ID聚类bootstrap，2000次、seed=2026100301、百分位95%区间，抽中一题保留该题全部有效重复配对；重复调用不是独立题目。输出正确率差和总token节省的描述区间；比较中若有未知total_tokens则不输出token区间。只描述这个人为选题集合，不代表总体，不做多重检验修正，不宣称显著性或不劣性；零差或退化区间不证明等价。

格式计数按解析契约，不能把格式合格等同语义正确。基准测试题比较少、包含复用题，模型服务随时可变。本轮不把v1和v2数字拼成增长趋势或跨模型效率排行榜。

## 复现

```bash
python -m peerlab efficiency --protocol token-efficiency-v2 --dataset peerlab/data/token-efficiency-v2.json --limit 24 --repeats 2 --seed 2026100301 --max-calls 288 --max-tokens 700 --timeout 90 --dry-run
# 去掉 --dry-run 并指定新目录才会真实调用
python -m peerlab efficiency --protocol token-efficiency-v2 --dataset peerlab/data/token-efficiency-v2.json --limit 24 --repeats 2 --seed 2026100301 --max-calls 288 --max-tokens 700 --timeout 90 --output runs/token-efficiency-v2
python -m peerlab analyze-efficiency runs/token-efficiency-v2/run.json --output runs/token-v2-recheck
```

发布原始JSON、SHA256与执行commit、基础配对分析、多维度JSON/Markdown、逐条CSV和离线HTML。手工讨论的例子注明record ID，描述性观点与待验证假设分开，不用挑选案例代替整体结果。
