# PeerLab ↗

**两个 AI，能否一起答得更好？**

一个可以在本地复现的 **DeepSeek × Kimi 交叉审稿实验**。让两个模型独立作答，再分别接受自己的审稿和另一个模型的审稿，用客观规则比较答案是否改对、是否被带偏。

Python 3.10+ · 运行时零第三方依赖 · MIT · 中文题库 · 离线交互报告

## 这个项目研究什么

“多叫一个模型”可能改善答案，也可能只是增加费用，或者把原本正确的答案改错。PeerLab 保留三组对照：

| 条件 | 过程 | 每模型、每题新增调用 |
|---|---|---:|
| Baseline / 独立 | 模型直接回答 | 1 |
| Self / 自检 | 模型审查自己的 baseline，再修订 | 2 |
| Peer / 互审 | 另一个模型审查同一个 baseline，原模型再修订 | 2 |

两模型每题合计 **10 次调用**。Self 与 Peer 共用原始 baseline，并使用相同的审稿、修订提示模板。模型不会看到标准答案或判分结果。完整提示词、返回模型名、输出、耗时、token、截断和错误状态都留在本地。

## 先看真实成果

仓库附带一次 3 题真实 API 试运行，见 [`examples/pilot/summary.md`](examples/pilot/summary.md)。下载仓库后双击 [`examples/pilot/report.html`](examples/pilot/report.html) 即可查看交互图表、逐题结果和匿名人工评审，不需要 API key 或联网。

本轮 DeepSeek 三条件均为2/3，Kimi均为3/3，没有观察到互审改善。一个值得研究的案例是：Kimi独立算对了概率题，却在审稿时认可DeepSeek的错误数值。见[首轮观察](docs/pilot-findings.md)。这是探索性试验，不是模型排行榜。

## 5 分钟开始

下载或克隆仓库，在项目根目录运行。无需安装依赖。

```powershell
# Windows PowerShell
git clone https://github.com/Yhg1123/peerlab-ai.git
cd peerlab-ai
Copy-Item .env.example .env
# 用编辑器把两个 API key 填进 .env
python -m peerlab doctor
python -m peerlab run
```

```bash
# macOS / Linux
git clone https://github.com/Yhg1123/peerlab-ai.git
cd peerlab-ai
cp .env.example .env
# 编辑 .env
python3 -m peerlab doctor
python3 -m peerlab run
```

配置：

```dotenv
DEEPSEEK_API_KEY=your_deepseek_key_here
KIMI_API_KEY=your_kimi_key_here
DEEPSEEK_MODEL=deepseek-flash
KIMI_MODEL=kimi-k2.6
```

环境变量优先于当前目录的 `.env`。`doctor` 查询官方模型列表并核对配置，不发起聊天请求。运行前也会核对模型名；**不自动切换模型**，避免悄悄改变实验条件。

默认关闭思考模式、`temperature=0.6`。请使用支持这些参数的模型；例如不支持关闭推理的模型不能直接替换使用。模型服务可能更新，重跑前检查官方文档和 `doctor` 输出。

每次运行创建独立目录 `runs/<时间戳>/`：

| 文件 | 用途 |
|---|---|
| `run.json` | 数据集快照、配置、逐步提示词与输出、客观判分、用量 |
| `report.html` | 自包含离线报告，响应式布局，匿名 A/B 人工评分 |
| `summary.md` | 可读实验摘要，适合保存到 GitHub |
| `scores.csv` | 逐题最终答案得分，可用于二次分析 |

双击 `report.html` 打开。浏览器不会调用 API，也不会接触密钥。人工评分保存在当前浏览器中，可导出 JSON；受限浏览器可能只保留到页面关闭，请及时导出。报告源数据含身份映射，匿名功能用于减少先入为主，**不是防作弊盲评系统**。

## 控制实验规模

默认只取题库前 3 题，单次采样，最多 30 次聊天请求，每次最多 700 输出 token。请求上限与输出上限不是人民币费用上限：输入也计费，失败或超时请求可能已由供应商计费。项目不保存易过期的价格表，实际费用以供应商后台为准。

```bash
# 完整 12 题，每题一次，共 120 次调用
python -m peerlab run --limit 12 --max-calls 120

# 完整 12 题，每题三次，共 360 次调用
python -m peerlab run --limit 12 --repeats 3 --max-calls 360 --seed 42

# 限制输出、超时，指定新的结果目录
python -m peerlab run --max-tokens 700 --timeout 90 --output runs/my-study

# 离线重新生成报告，不会请求 API
python -m peerlab report examples/pilot/run.json --output runs/rebuilt

# 列出题目 / 运行离线测试
python -m peerlab cases
python -m unittest discover -s tests -v
```

不自动重试，不覆盖已有运行目录。中断时已保存的 `run.json` 保留，可离线生成报告；当前请求可能已计费。失败的依赖会导致对应修订跳过。计划调用数超过预算时，在任何网络请求之前退出。

可选安装：`python -m pip install -e .`，随后也可以使用 `peerlab run`。

## 题库与判分

12 道自建题涵盖概率推理、代码理解、结构化输出、指令遵循、约束规划、机器学习指标与证据不足时的拒答。**程序不执行模型生成代码**。

模型返回 `{"answer": ..., "explanation": "..."}`。仅最终 `answer` 接受自动评分：数值使用绝对容差，数组和对象严格比较结构、类型与内容；允许完整 JSON 代码块，不从散文中搜索答案。非法 JSON、重复键、截断均记未通过。网络错误与缺失单独计覆盖率，不混成错误答案。

题库格式见 [`peerlab/data/cases.json`](peerlab/data/cases.json)。支持 `--dataset your-cases.json`；字段为 `id`、`category`、`title`、`prompt`、`check`、`expected`、`rationale`，数值题可加 `tolerance`。题目和输出都会发给两个供应商，请只放适合发送的内容。

## 实验能说明什么，不能说明什么

- 可以追踪互审修正了哪些错题、改坏了哪些正确答案，并与自检条件比较。
- Self 与 Peer 的额外调用数相同，但 token、耗时和金额没有被严格匹配。
- `seed` 控制本地顺序和展示；云端模型采样不保证确定性。调用顺序在基线和依赖约束下随机化，不是完全交叉平衡设计。
- 每个修订条件与同一次 baseline 配对。分析提升/退步只使用两边都有回答的有效配对，不能跨不同覆盖率直接比较准确率。
- 题库小、人工选择、可能被模型见过；没有隐藏测试集。重复同一题不是增加独立题目数量。
- 解释可能在最终数值正确时仍出错，所以另设人工评审。不会让参赛模型给自己判分。
- 本项目不自动给出统计显著性结论。正式研究应预先固定题库、采样次数与分析方法，并扩充题目与独立人工评审者。

## 目录

```text
peerlab/
  client.py             官方 API 适配、超时与安全错误信息
  experiment.py         三组协议、预算、持久化与配对统计
  grading.py            不执行代码的严格判分
  report.py             HTML / Markdown / CSV 导出
  data/cases.json       12 题与独立参考答案
  templates/report.html 离线报告与匿名人工评分
examples/pilot/         真实试运行记录
tests/                  不使用真实 API 的自动化测试
scripts/package_release.py  带密钥检查的源码打包
```

## 保存到 GitHub

`.env`、本地 `runs/` 和发布包 `dist/` 已加入 `.gitignore`。不要用 `git add -f .env`。提供的源码打包脚本只收集明确允许的项目目录，并拒绝疑似 API key：

```bash
python scripts/package_release.py
```

产出 `dist/peerlab-ai-source.zip`，可以解压后上传仓库。也可以在自己的空 GitHub 仓库中按页面提示设置 remote，再 `git add .`、提交和推送。此项目没有自动创建远程仓库或上传任何密钥。

若 key 曾出现在聊天、截图或公开记录中，应在各自控制台撤销并重新生成，再更新本地 `.env`。

## 官方接口资料

- [DeepSeek API 快速开始](https://api-docs.deepseek.com/) / [Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)
- [Kimi Chat Completions](https://platform.kimi.com/docs/api/chat)

本项目是独立开源实验，与两家供应商没有官方隶属关系。贡献说明见 [CONTRIBUTING.md](CONTRIBUTING.md)，代码按 [MIT](LICENSE) 许可开放。
