# Token 效率真实实验 v1

12题 × 2模型 × 4条件；2026-10-02实际执行96次请求，95次返回、1次网络错误，无补跑。全部返回共21,451token；未返回请求的未知用量不包含在此和中。

- [结果与限制](../../docs/studies/token-efficiency-v1-findings.md)
- [观点文章](../../docs/opinions/token-savings-quality-floor.md)
- [执行前方案](../../docs/studies/token-efficiency-v1.md)
- [原始请求、输出及失败](run.json)
- [可重算分析](analysis.json) · [Markdown摘要](analysis.md) · [逐条得分CSV](scores.csv)
- [离线HTML报告](report.html)：下载仓库后双击打开，可展开逐题原始输出；GitHub文件页只展示源码。
- [原始文件哈希和代码来源](provenance.json)

```bash
python -m peerlab analyze-efficiency examples/token-efficiency-v1/run.json --output runs/token-recheck
```

不需要密钥或网络。核验数据集、提示词、调度和判分，然后重新生成报告。原始文件按字节保留；provenance中的SHA256用于检验下载是否一致，不代表供应商签名。运行时版本号为0.2.0加执行commit中的新协议，成果随0.3.0发布；请用commit识别准确代码。

主比较总token减少约53.9%/72.3%，但有效配对正确数仅3/11和3/12，没有证明达到业务质量门槛、质量等价或普遍无损。不将这些token百分比当作账单节省比例。
