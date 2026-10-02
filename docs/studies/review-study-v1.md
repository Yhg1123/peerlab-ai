# 数值审稿实验 v1：执行前方案

这份方案与程序在第一次本轮 API 调用前提交到 GitHub。它是仓库内的预先记录，不是正式登记平台的注册研究。

## 问题与条件

主要问题：审稿者同时拿到自己在看候选前产生的独立解答，是否改变修订答案的客观正确率？

主要比较为 **peer_independent 对 peer**，按作者模型、题目和重复轮次配对。baseline与self作为次要对照，不在观察结果后挑选表现较好的对照。

## 固定设置

- 题库：`peerlab/data/review-study.json`，由已发布的 `bayes-study.json` 和 `f1-study.json` 按该顺序拼接，各6题，共12题。
- 生成种子：两族均为20261002。任务顺序种子：20261002。
- 每题1次采样。请求模型固定为deepseek-flash和kimi-k2.6，不自动替换。
- 四条件：baseline、self、peer、peer_independent。
- temperature=0.6，thinking=disabled，每次输出最多700 token，超时90秒。
- 最多168次聊天请求；输出token上限117,600，不含输入token，也不是金额上限。无自动重试。
- 三个修订条件随机排序，共用同次baseline；不使用其他条件的修订结果。
- 所有题按预设1e-6绝对容差判分，不依据模型表现改变参考值或容差。

精确题库hash和离线调用计划见同目录的 `review-study-v1-plan.json`。

## 记录与分析

1. 保存全部输出、请求参数、耗时、token和失败记录；不只展示成功纠错的案例。
2. 先报告各条件正确/已返回，以及已返回/计划，避免混淆缺失与错误。
3. 对主要比较报告双方都正确、仅peer正确、仅peer_independent正确、双方都错的四格计数。只用两边均有回答的有效配对；截断作为已返回但未通过。
4. 同时报告相对baseline的纠错与退步次数，以及两个任务族各自的结果。
5. 汇总全部调用的用量与延迟；修订条件的路径成本计入基线、审稿与修订。复用调用只在全程总量中计一次，各条件路径不可相加当作总账单。
6. 不进行事后补跑、换种子或筛选题目。发生失败也公开部分结果；有意重跑需作为另一次实验记录。

## 限制与停止规则

这是两个算术模板上的12题探索，不代表综合智能或训练污染已排除。一次采样不估计模型随机性；即使有净改善也不做显著性或普遍有效的宣称。

先解后审既增加上下文，也改变审稿指令，不能单独识别锚定效应。按记录比较错误传播案例时，只能描述发生了什么。

完成计划后停止。遇到人工中断或程序异常立即保留已有记录；失败请求不重试，依赖失败则跳过对应分支。没有授权本项目自动进行后续长期实验。

## 执行命令

```bash
python -m peerlab run --dataset peerlab/data/review-study.json --limit 12 --protocol independent --seed 20261002 --max-calls 168 --max-tokens 700 --timeout 90 --dry-run
python -m peerlab run --dataset peerlab/data/review-study.json --limit 12 --protocol independent --seed 20261002 --max-calls 168 --max-tokens 700 --timeout 90 --output runs/review-study-v1
```
