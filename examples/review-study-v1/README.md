# 数值审稿实验 v1

真实API记录，状态为 **partial**：150次请求尝试、145次返回、5次网络失败、18个依赖步骤跳过。保留全部失败，不补跑。

- [主要发现与反例](../../docs/studies/review-study-v1-findings.md)
- [配对分析](analysis.md)：普通互审与先解后审，同题同轮比较。
- [四组摘要](summary.md)：正确答案与覆盖率。
- [交互报告](report.html)：下载后用浏览器打开；GitHub文件页显示HTML源码。
- [原始记录](run.json)：完整任务、提示词、输出、依赖和用量。
- [执行来源](provenance.json)：执行前方案、代码版本、数据hash与命令。
- [机器可读分析](analysis.json)、[最终答案CSV](scores.csv)。

仓库根目录离线复核：

```bash
python -m peerlab analyze examples/review-study-v1/run.json --output runs/review-study-recheck
python -m peerlab report examples/review-study-v1/run.json --output runs/review-study-recheck
```

不需要密钥，不调用API。原始文件的字节SHA-256以provenance记录为准；`.gitattributes` 为这份原始记录关闭自动换行转换，CI会核对文件hash和执行前方案。
