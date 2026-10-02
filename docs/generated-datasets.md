# 用精确算术生成题库

首轮模型写对公式、算错数值，因此后续题库将参考答案交给可复算的程序。

```bash
python -m peerlab generate --family bayes --count 6 --seed 20261002 --output runs/bayes.json
python -m peerlab generate --family macro_f1 --count 6 --seed 20261002 --output runs/f1.json
python -m peerlab verify-dataset runs/bayes.json
```

这些命令不读取密钥、不请求 API。相同种子、族与数量产生相同任务；不覆盖已有文件。

Bayes 使用整数基点表示先验概率、真阳性率与假阳性率，每个基点为1/10000。F1使用正整数混淆矩阵。参考答案由Python标准库 `fractions.Fraction` 计算，保留既约分数和最终浮点近似。评分绝对容差固定为1e-6；提示词要求至少6位小数。

每道题的 `oracle` 保存计算参数与精确分数。加载时重建提示词、参考值与评分规则，任何不一致都在发出 API 请求前报错。没有 oracle 的旧题依然可用，但明确标为人工参考题，不宣称已获得数学验证。

这是本地数据完整性与标签校验，不是给模型新增计算器。oracle、参考答案和解释都不发送给模型。模型自己生成的文本从不作为Python代码执行。

参数化题目不是互相独立的能力领域，增加同模板的数量不能代替扩展任务类型，也不等于无训练污染的新基准。后续报告应保留这些限制。
