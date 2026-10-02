# 字段顺序 × 依据限长：真实API数据

16题 × 2重复 × 2模型 × 4条件，256次请求尝试，255次返回、1次Kimi网络失败，无重试。已知返回用量72,608 token。失败记录保留，不能把255次响应说成255道独立题。

先读[详细结果与反例](../../docs/studies/token-efficiency-v3-findings.md)、[指标阅读指南](../../docs/factorial-analysis.md)和[执行前方案](../../docs/studies/token-efficiency-v3.md)。观点文章：[顺序不是装饰，长度也不是质量](../../docs/opinions/order-length-and-usable-output.md)。

|文件|用途|
|---|---|
|[run.json](run.json)|完整配置、题目快照、256条请求记录及原始响应/错误|
|[provenance.json](provenance.json)|原始字节SHA256、执行代码commit与源码hash|
|[analysis.md](analysis.md) / [analysis.json](analysis.json)|正确率、用量、有效配对与记录ID|
|[dimensions.md](dimensions.md) / [dimensions.json](dimensions.json)|题型、重复稳定性、精度敏感性、延迟与区间|
|[factorial.md](factorial.md) / [factorial.json](factorial.json)|共同/本条件契约、依据长度、四条件交互项|
|[scores.csv](scores.csv)|逐条评分与token用量|
|[report.html](report.html)|无需网络的可展开逐题报告，下载后双击|
|[figures](figures)|三幅研究图，各提供PNG与SVG；可用脚本重画|

```bash
python -m peerlab analyze-efficiency examples/token-efficiency-v3/run.json --output runs/v3-recheck
# 可选：绘图需要matplotlib，核心分析仍无第三方依赖
python scripts/plot_efficiency.py examples/token-efficiency-v3/run.json --output runs/v3-figures
```

原始run.json按字节保留，不改换行。`python -m unittest discover -s tests -v`核对hash、冻结计划和保存的三套分析。报告中的结果来自实际响应；单元测试的合成fixture仅用于测试，未混入本目录。

这些是已知困难集上的探索性结果，不是模型排行榜。无明确字符上限时，DeepSeek先答案→先依据为2/32→22/32；Kimi7/32→7/32，但有5次改善和5次退步。详细解读保留不支持“万能模板”的反例，也解释了缺失导致的不同配对分母。
