# JSON原生类型提醒：公开证据

2026-10-04真实执行；16道新实例×2次×2模型×2条件，128次请求、126次返回、2次失败，38,089已知token，无重试。当前文件是结果档案，重新联网运行请使用新目录。

|入口|内容|
|---|---|
|[结果解读](../../docs/studies/token-efficiency-v4-findings.md)|四组数据、有效配对、类型与计算错误、逐条反例和局限|
|[执行前方案](../../docs/studies/token-efficiency-v4.md)|假设、选题、干预、指标、采样与上限|
|[run.json](run.json)|原始响应、提示、usage、失败记录和题集快照|
|[provenance.json](provenance.json)|原始字节SHA256、执行commit与源码哈希|
|[analysis.md](analysis.md) / [JSON](analysis.json)|答案质量、配对token与分母|
|[types.md](types.md) / [JSON](types.json)|类型端点、互斥错误分解与记录ID|
|[dimensions.md](dimensions.md) / [JSON](dimensions.json)|题型、稳定性、数值误差、延迟与聚类区间|
|[scores.csv](scores.csv)|逐条数据导出|
|[report.html](report.html)|下载后本地打开的自包含交互报告，无需密钥或网络|
|[类型图](figures/native-types.png) / [SVG](figures/native-types.svg)|错误构成与类型、正确率差|
|[用量图](figures/quality-and-tokens.png) / [SVG](figures/quality-and-tokens.svg)|正确率与有效配对总token变化|
|[题型图](figures/category-quality.png) / [SVG](figures/category-quality.svg)|不同题型的返回正确率|

```bash
python -m peerlab analyze-efficiency examples/token-efficiency-v4/run.json --output runs/v4-recheck
```

运行状态为`partial`，因Kimi明确类型组#66、#88网络失败。Kimi全组控制正确10/32，有效配对控制正确9/30；两者分母不同。类型提醒组返回未出现原生类型错误，但仍有算术错误。数值字符串不转型，允许完整JSON外层代码围栏的既有解析规则未改动。结论仅适用于当前选定任务与采样。
