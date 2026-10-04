"""Optional publication figures. Requires matplotlib; core PeerLab stays dependency-free."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from peerlab.dimensions import diagnostics


def main():
    parser = argparse.ArgumentParser(description="Plot audited v2/v3/v4 evidence with matplotlib")
    parser.add_argument("run_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator, PercentFormatter

    run = json.loads(args.run_json.read_text(encoding="utf-8"))
    data = diagnostics(run)
    names = [p["name"] for p in run["providers"]]
    arms = run["config"]["arms"]
    labels = ["Standard\nexplanation", "Answer\nonly", "Evidence\nthen answer"]
    colors = ["#45647a", "#14826d", "#bf742c"]
    pair_labels = ["Standard → answer only", "Answer only → evidence", "Standard → evidence"]
    if run["kind"] == "token-efficiency-v3":
        labels = ["Answer\nfirst\n80-char cap", "Evidence\nfirst\n80-char cap", "Answer\nfirst\nno char cap", "Evidence\nfirst\nno char cap"]
        colors = ["#45647a", "#14826d", "#bf742c", "#875a95"]
        pair_labels = ["Order: 80-char cap", "Order: no char cap", "Remove cap: answer first", "Remove cap: evidence first"]
    if run["kind"] == "token-efficiency-v4":
        labels = ["Control", "Explicit JSON type"]
        pair_labels = ["Control → explicit type"]
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
        ax.set(title=name + " | returned-answer quality", ylim=(0, 1.20), xticks=range(len(arms)), xticklabels=labels, ylabel="Fraction of returned responses")
        ax.set_yticks([0, .25, .5, .75, 1])
        ax.tick_params(axis="x", labelsize=9)
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", alpha=.15)
        ax.text(.02,.96,"Bars: answer correct\nDiamonds: correct AND arm-specific contract", transform=ax.transAxes, va="top", fontsize=9)
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
        ax.set(yticks=range(len(pairs)), yticklabels=pair_labels, ylim=(len(pairs)-.5,-.6), xlabel="Paired total-token saving (negative = more tokens)",title=name + " | paired token change")
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
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
    if run["kind"] == "token-efficiency-v4":
        from peerlab.native_types import type_diagnostics
        types = type_diagnostics(run)
        fig, axes = plt.subplots(2,2,figsize=(12,8.5))
        outcomes = [("correct","Correct","#14826d"),
                    ("native_type_wrong_answer","Type OK, answer wrong","#d6ae65"),
                    ("wrong_native_type","Wrong native type","#9b628d"),
                    ("invalid_json","Invalid JSON","#b3534e"),
                    ("truncated","Truncated","#e18450"),
                    ("request_error","Request failed","#78878b"),
                    ("pending","Pending","#acb9bd"),
                    ("not_attempted","Not attempted","#d2dcdf")]
        used = {key for key,_,_ in outcomes if any(g['outcomes'][key] for g in types['conditions'] if g['scope']=='all')}
        for col,name in enumerate(names):
            ax=axes[0,col]
            groups=[next(g for g in types['conditions'] if g['provider']==name and g['arm']==arm and g['scope']=='all') for arm in arms]
            bottom=[0,0]
            for key,label,color in outcomes:
                if key not in used:
                    continue
                values=[g['outcomes'][key] for g in groups]
                ax.bar([0,1],values,bottom=bottom,color=color,label=label,width=.55)
                for i,value in enumerate(values):
                    if value:
                        ax.text(i,bottom[i]+value/2,str(value),ha='center',va='center',fontsize=11)
                bottom=[a+b for a,b in zip(bottom,values)]
            ax.set(title=name+' | all planned calls',xticks=[0,1],xticklabels=labels,ylim=(0,max(g['planned'] for g in groups)*1.05),ylabel='Number of responses / missing calls')
            ax=axes[1,col]
            p=next(p for p in types['comparisons'] if p['provider']==name and p['scope']=='all')
            q=next(p for p in data['comparisons'] if p['provider']==name and p['scope']=='all')
            endpoints=[('Native type',p['type_delta'],p['native_type_delta_95pct']),('Answer correct',q['accuracy_delta'],q['cluster_bootstrap']['accuracy_delta_95pct'])]
            for i,(label,value,ci) in enumerate(endpoints):
                if value is not None:
                    if ci is not None:
                        ax.plot([x*100 for x in ci],[i,i],color=colors[i],linewidth=3)
                        ax.plot([x*100 for x in ci],[i,i],'|',color=colors[i],markersize=10)
                    ax.plot(value*100,i,'o',color=colors[i])
                    ax.annotate(f'{value*100:+.1f} pp',(value*100,i),xytext=(0,12),textcoords='offset points',ha='center')
            ax.axvline(0,color='#8c9595',linewidth=1)
            ax.set(title=f"{name} | {p['paired']} matched pairs",yticks=[0,1],yticklabels=['Native type','Answer correct'],ylim=(1.5,-.5),xlabel='Explicit type minus control (percentage points)')
            ax.grid(axis='x',alpha=.15)
        handles,legend_labels=axes[0,0].get_legend_handles_labels()
        fig.legend(handles,legend_labels,loc='upper center',bbox_to_anchor=(.5,.94),ncol=3,frameon=False,fontsize=9)
        fig.suptitle(('SYNTHETIC TEST FIXTURE | ' if run.get('mode') != 'live' else '') + 'Native JSON types: compliance and correctness are different endpoints',fontsize=15)
        fig.text(.5,.025,'Top panels: mutually exclusive outcomes; denominators include all planned calls.\nBottom panels: matched returned pairs, 95% descriptive task-cluster intervals. No coercion or grade changes.',ha='center',fontsize=9,color='#52636b')
        fig.tight_layout(rect=(0,.08,1,.86),h_pad=3,w_pad=2)
        for suffix in ('png','svg'):
            fig.savefig(args.output/f'native-types.{suffix}',dpi=180,bbox_inches='tight')
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
        ax.set(xticks=range(len(arms)),xticklabels=labels,yticks=range(len(categories)),yticklabels=[translations.get(c,c) for c in categories],title=name)
        ax.tick_params(axis="x", labelsize=9)
    fig.colorbar(im,ax=axes,format=PercentFormatter(1),shrink=.8,label="Answer accuracy among returned responses")
    fig.suptitle("Task categories: correct / returned\nSmall groups and repeated tasks; descriptive comparison only",fontsize=14)
    for suffix in ("png","svg"):
        fig.savefig(args.output/f"category-quality.{suffix}",dpi=180,bbox_inches="tight")
    plt.close(fig)
    if run["kind"] == "token-efficiency-v3":
        from peerlab.factorial import factorial_diagnostics
        factorial = factorial_diagnostics(run)
        fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
        for ax, name in zip(axes, names):
            index = {(r["case_id"], r["repeat"], r["arm"]): r for r in run["records"] if r["provider"] == name}
            blocks = [[index.get((c["id"], rep, arm)) for arm in arms] for c in run["cases"] for rep in range(1, run["config"]["repeats"]+1)]
            blocks = [b for b in blocks if all(r is not None and r["status"] == "ok" for r in b)]
            if blocks:
                means = [sum(b[i]["grade"]["passed"] for b in blocks)/len(blocks) for i in range(4)]
                for start, color, label in [(0,"#14826d","80-character cap"),(2,"#875a95","No explicit character cap")]:
                    values = means[start:start+2]
                    ax.plot([0,1], values, "o-", color=color, linewidth=2, markersize=7, label=label)
                    for x,y in enumerate(values):
                        ax.annotate(f"{y:.1%}",(x,y),xytext=(10,-18 if start else 10),textcoords="offset points",color=color)
            effect = next(p for p in factorial["interactions"] if p["provider"] == name)
            estimate, ci = effect["estimate"]["accuracy"], effect["percentile_95pct"]["accuracy"]
            caption = f"Interaction: {estimate*100:+.1f} pp" if estimate is not None else "Interaction unavailable"
            if ci:
                caption += f" (95%: {ci[0]*100:+.1f} to {ci[1]*100:+.1f} pp)"
            ax.set(title=f"{name} | {len(blocks)} complete blocks", xticks=[0,1],xticklabels=["Answer first","Evidence first"],xlim=(-.25,1.35),ylim=(-.08,1.15),ylabel="Answer accuracy on complete blocks")
            ax.set_yticks([0,.25,.5,.75,1])
            ax.yaxis.set_major_formatter(PercentFormatter(1))
            ax.grid(axis="y",alpha=.15)
            ax.legend(loc="upper left",fontsize=9)
            ax.text(.5,-.18,caption,ha="center",transform=ax.transAxes,fontsize=9)
        fig.suptitle("Does the effect of output order depend on the evidence cap?",fontsize=15)
        fig.text(.5,.02,"Interaction = order effect without cap minus order effect with cap. Descriptive task-cluster intervals.\nReused, selected tasks; request order does not reveal the model's internal reasoning process.",ha="center",fontsize=9,color="#52636b")
        fig.tight_layout(rect=(0,.11,1,.95))
        for suffix in ("png","svg"):
            fig.savefig(args.output/f"factor-interaction.{suffix}",dpi=180,bbox_inches="tight")
        plt.close(fig)
    # Matplotlib inserts trailing spaces inside SVG path attributes; normalize
    # generated text for clean Git diffs without changing figure geometry.
    svg_names = ["quality-and-tokens.svg", "category-quality.svg"]
    if run["kind"] == "token-efficiency-v3":
        svg_names.append("factor-interaction.svg")
    if run["kind"] == "token-efficiency-v4":
        svg_names.append("native-types.svg")
    for name in svg_names:
        path = args.output / name
        normalized = "\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()) + "\n"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(normalized)
    print(f"Saved {len(svg_names)*2} figures to {args.output.resolve()}")


if __name__ == "__main__":
    main()
