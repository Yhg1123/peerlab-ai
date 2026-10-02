"""Optional publication figures. Requires matplotlib; core PeerLab stays dependency-free."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from peerlab.dimensions import diagnostics


def main():
    parser = argparse.ArgumentParser(description="Plot audited v2 evidence with matplotlib")
    parser.add_argument("run_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    run = json.loads(args.run_json.read_text(encoding="utf-8"))
    data = diagnostics(run)
    names = [p["name"] for p in run["providers"]]
    arms = run["config"]["arms"]
    labels = ["Standard\nexplanation", "Answer\nonly", "Evidence\nthen answer"]
    colors = ["#45647a", "#14826d", "#bf742c"]
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10, "axes.spines.top":False,
                         "axes.spines.right":False, "svg.fonttype":"none", "figure.facecolor":"#fafaf7"})
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    for col, name in enumerate(names):
        ax = axes[0, col]
        groups = [next(g for g in data["conditions"] if g["provider"]==name and g["arm"]==arm and g["scope"]=="all") for arm in arms]
        for i, g in enumerate(groups):
            if not g["returned"]:
                continue
            ax.bar(i, g["correct"]/g["returned"], color=colors[i], width=.58)
            ax.plot(i, g["contract_and_correct"]/g["returned"], marker="D", color="#222222", markersize=5)
            ax.text(i, g["correct"]/g["returned"]+.035, f"{g['correct']}/{g['returned']}", ha="center", fontsize=10)
        ax.set(title=name + " | returned-answer quality", ylim=(0, 1.05), xticks=range(3), xticklabels=labels, ylabel="Fraction of returned responses")
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", alpha=.15)
        ax.text(.02,.96,"Bars: answer correct\nDiamonds: correct AND output contract met", transform=ax.transAxes, va="top", fontsize=9)
        ax = axes[1, col]
        pairs = [p for p in data["comparisons"] if p["scope"]=="all" and p["provider"]==name]
        for i, p in enumerate(pairs):
            estimate = p["tokens"]["total_tokens"]["saved_fraction"]
            ci = p["cluster_bootstrap"]["total_token_saving_95pct"]
            if estimate is None:
                continue
            if ci:
                ax.plot(ci, [i,i], color=colors[i], linewidth=3)
                ax.plot(ci, [i,i], "|", color=colors[i], markersize=10)
            ax.plot(estimate, i, "o", color=colors[i], markersize=8)
            ax.annotate(f"{estimate:.1%} · {p['paired']} pairs", (estimate,i), xytext=(0,12),textcoords="offset points",ha="center",fontsize=9)
        ax.axvline(0, color="#8c9595", linewidth=1)
        ax.set(yticks=range(3), yticklabels=["Standard → answer only", "Answer only → evidence", "Standard → evidence"], ylim=(2.5,-.6), xlabel="Paired total-token saving (negative = more tokens)",title=name + " | paired token change")
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="x", alpha=.15)
    design = f"PeerLab: {len(run['cases'])} tasks × {run['config']['repeats']} repeats × {len(names)} models × {len(arms)} conditions"
    if run.get("mode") != "live":
        design = "SYNTHETIC TEST FIXTURE | " + design
    fig.suptitle(design, fontsize=17, y=.99)
    fig.text(.5,.025,"Intervals: 2,000 task-cluster bootstrap draws, percentile 95%. Selected task set; no noninferiority claim.\nQuality denominators exclude failed requests. Savings use matched returned pairs, not full-condition totals. Token counts are not bills.",ha="center",fontsize=9,color="#52636b")
    fig.tight_layout(rect=(0,.075,1,.95),h_pad=3,w_pad=2)
    args.output.mkdir(parents=True,exist_ok=True)
    for suffix in ("png","svg"):
        fig.savefig(args.output/f"quality-and-tokens.{suffix}",dpi=180,bbox_inches="tight")
    plt.close(fig)

    categories = sorted({c["category"] for c in run["cases"]})
    translations = {"概率推理":"Probability", "机器学习":"ML metrics", "代码理解":"Code understanding", "约束规划":"Planning", "结构化输出":"Structured output", "事实约束":"Evidence constraints", "逻辑推理":"Logic", "数据分析":"Data analysis", "指令遵循":"Instruction following"}
    fig, axes = plt.subplots(1,2,figsize=(11,7),layout="constrained")
    for ax,name in zip(axes,names):
        groups = [[next(g for g in data["conditions"] if g["provider"]==name and g["arm"]==arm and g["scope"]=="category:"+category) for arm in arms] for category in categories]
        values = [[g["answer_accuracy_returned"] if g["returned"] else float('nan') for g in row] for row in groups]
        im = ax.imshow(values,vmin=0,vmax=1,cmap="YlGnBu",aspect="auto")
        for y,row in enumerate(groups):
            for x,g in enumerate(row):
                value = values[y][x]
                ax.text(x,y,f"{g['correct']}/{g['returned']}",ha="center",va="center",color="white" if value>.6 else "#172e3b",fontsize=11)
        ax.set(xticks=range(3),xticklabels=labels,yticks=range(len(categories)),yticklabels=[translations.get(c,c) for c in categories],title=name)
    fig.colorbar(im,ax=axes,format=PercentFormatter(1),shrink=.8,label="Answer accuracy among returned responses")
    fig.suptitle("Task categories: correct / returned\nSmall groups and repeated tasks; descriptive comparison only",fontsize=14)
    for suffix in ("png","svg"):
        fig.savefig(args.output/f"category-quality.{suffix}",dpi=180,bbox_inches="tight")
    plt.close(fig)
    print(f"Saved 4 figures to {args.output.resolve()}")


if __name__ == "__main__":
    main()
