# 24题、两次采样的多维度研究

真实调用：2026-10-02，24题×2次×2模型×3条件，共288次请求且全部返回，62,837总token。无网络失败、无重试。输出中的JSON失败、截断、错误答案仍全部保留。

- [详细结果和解释](../../docs/studies/token-efficiency-v2-findings.md)
- [观点文章](../../docs/opinions/measure-usable-answers.md)
- [执行前方案](../../docs/studies/token-efficiency-v2.md) · [指标阅读指南](../../docs/multidimensional-analysis.md)
- [原始记录](run.json) · [来源及SHA256](provenance.json)
- [基础分析](analysis.md) · [机器可读配对](analysis.json)
- [多维度表格](dimensions.md) · [分层、区间与稳定性JSON](dimensions.json)
- [逐条得分CSV](scores.csv)
- [离线报告](report.html)：下载后双击，无密钥或网络需求，可展开题型和逐题输出；GitHub文件页只展示HTML源文件。

![质量与token](figures/quality-and-tokens.png)

![题型结果](figures/category-quality.png)

图的矢量版：[质量/用量SVG](figures/quality-and-tokens.svg)、[题型SVG](figures/category-quality.svg)。图中条件分别对应verbose_explain、compact_answer、compact_evidence；分母是响应次数，不是独立题数。

```bash
python -m peerlab analyze-efficiency examples/token-efficiency-v2/run.json --output runs/v2-recheck
```

这会核验题集、冻结提示词、调度、判分并重建所有分析，完全离线。`python scripts/plot_efficiency.py ... --output ...`可选重画图，需要单独安装matplotlib；项目核心不依赖它。

原始文件按字节复制，运行版本号为0.3.0加执行commit的新协议，最终成果随0.4.0发布。每个条件48条记录只有24道题、两次采样。题集人为选择且含复用题，不声称总体无损、统计等价或跨模型能力排名。
