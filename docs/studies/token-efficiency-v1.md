# 执行前方案：Token 效率 2×2 实验 v1

本方案和机器可读的[token-efficiency-v1-plan.json](token-efficiency-v1-plan.json)在本轮真实聊天请求前提交到GitHub。实验执行后另写findings，不根据结果修改本方案或提示词。

## 问题与预期

压缩系统提示词和去掉解释能节省多少实际返回token？在同题配对中会不会同时损失正确答案？预期只输出answer会减少输出用量，短提示词会减少输入用量；不预先宣称质量不变。没有显著性检验或不劣性界值，本轮只做描述性探索。

## 固定设计

- 使用[token-efficiency-v1.json](../../peerlab/data/token-efficiency-v1.json)：4道Bayes、4道macro-F1，使用已有有理数生成器，seed=2026100203；另外固定选取原题库的python-aliasing、critical-path、balanced-json、retrieval-abstain四题。8道生成题可机器核验精确参考，4道复用题是人工参考；混合题集比例人为设定，不代表用户任务分布。
- 选取两类数值题是因为前轮已暴露小数计算困难；四道复用题覆盖代码理解、规划、结构化输出与证据不足。选择发生在本轮请求前，但并非盲选未知基准。所有12题都进入结果，不事后筛选容易题。
- DeepSeek deepseek-flash与Kimi kimi-k2.6，thinking=disabled，temperature=0.6，max_tokens=700，timeout=90秒，retries=0。
- [协议](../token-efficiency.md)的四条件，每模型每题每条件独立一次：12×2×4=96次请求；不另设停止规则，不根据正确率补跑。调度seed=2026100203。
- 只发送题目prompt和冻结系统提示词。参考答案、rationale、oracle和其他调用结果不进入请求。调用前已知的模型列表预检不算聊天请求。
- 数值题绝对误差1e-6；critical-path沿用默认1e-6；结构化题严格类型/值判定。只判answer，不从explanation中挑数字。截断或不合法JSON判错；请求失败记缺失，无重试。未专门量化解释质量和字段遵循度。

## 预先定义的报告

主比较是每模型verbose_explain→compact_answer，同题有效配对中的输入/输出/总token节省比例、正确数、改善/退步数。次比较是两个提示词水平分别固定输出类型、两个输出水平分别固定提示词；不把这些相关比较当独立重复。

报告所有条件的正确/返回/计划数、网络失败、JSON失败、截断、缺失usage。配对token节省用两端均有已知用量的同一子集；不把失败请求的未知用量当零。公开原始请求/响应、分析JSON/CSV/HTML、原始文件SHA256、执行代码commit和本方案commit。

观点文章必须区分观察与推测：即使答案正确率相同，也不宣称统计等价、解释无价值或普遍降本。无推理模式不代表模型没有内部计算；这个实验只能测提示词与可见输出约束，不推断内部机制。不比较不同模型的账单成本，不以字符数替代token。

## 运行命令

```bash
python -m peerlab efficiency --dataset peerlab/data/token-efficiency-v1.json --limit 12 --repeats 1 --seed 2026100203 --max-calls 96 --max-tokens 700 --timeout 90 --output runs/token-efficiency-v1
```

预算是96次尝试，输出理论上限67200token，输入额外计入。执行失败/中断不会重用同一输出目录。最终结论保留单轮、小题集、已知任务类型、服务端模型和缓存可变化的限制。
