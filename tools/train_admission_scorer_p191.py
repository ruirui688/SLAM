#!/usr/bin/env python3
"""CPU-only learned admission-scorer smoke for P191.

Pure-Python logistic regression on the P190 cluster-level dataset. This is a
feasibility smoke, not a publication-grade learned component.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

FEATURE_FIELDS = [
    "session_count",
    "frame_count",
    "support_count",
    "dynamic_ratio",
    "label_purity",
    "mean_center_x",
    "mean_center_y",
    "mean_size_x",
    "mean_size_y",
    "is_forklift_like",
    "is_infrastructure_like",
]


def fnum(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def sigmoid(z: float) -> float:
    if z < -60:
        return 0.0
    if z > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def standardize(rows: list[dict[str, Any]], ref_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    stats: dict[str, dict[str, float]] = {}
    for feat in FEATURE_FIELDS:
        vals = [fnum(r[feat]) for r in ref_rows]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(var) or 1.0
        stats[feat] = {"mean": mean, "std": std}
    out=[]
    for row in rows:
        z={**row}
        z["x"]=[(fnum(row[feat])-stats[feat]["mean"])/stats[feat]["std"] for feat in FEATURE_FIELDS]
        z["y"]=int(float(row["target_admit"]))
        out.append(z)
    return out, stats


def train_logreg(train_rows: list[dict[str, Any]], epochs: int, lr: float, l2: float) -> tuple[list[float], float, list[dict[str, float]]]:
    nfeat=len(FEATURE_FIELDS)
    w=[0.0]*nfeat
    b=0.0
    history=[]
    for epoch in range(1, epochs+1):
        gw=[0.0]*nfeat
        gb=0.0
        loss=0.0
        for row in train_rows:
            x=row["x"]; y=row["y"]
            p=sigmoid(sum(wi*xi for wi,xi in zip(w,x))+b)
            p=min(max(p,1e-8),1-1e-8)
            loss += -(y*math.log(p)+(1-y)*math.log(1-p))
            err=p-y
            for i,xi in enumerate(x):
                gw[i]+=err*xi
            gb+=err
        m=len(train_rows)
        for i in range(nfeat):
            gw[i]=gw[i]/m + l2*w[i]
            w[i]-=lr*gw[i]
        b-=lr*(gb/m)
        if epoch in {1,10,100,500,1000,epochs}:
            reg=0.5*l2*sum(v*v for v in w)
            history.append({"epoch":epoch,"loss":round(loss/m+reg,6)})
    return w,b,history


def rule_predict(row: dict[str, Any]) -> int:
    return int(
        fnum(row["session_count"]) >= 2
        and fnum(row["frame_count"]) >= 4
        and fnum(row["support_count"]) >= 6
        and fnum(row["dynamic_ratio"]) <= 0.2
        and fnum(row["label_purity"]) >= 0.7
    )


def summarize(rows: list[dict[str, Any]], pred_key: str) -> dict[str, Any]:
    tp=tn=fp=fn=0
    false_admit_forklift=[]
    false_reject_infra=[]
    for r in rows:
        y=int(r["y"]); p=int(r[pred_key])
        if p==1 and y==1: tp+=1
        elif p==0 and y==0: tn+=1
        elif p==1 and y==0:
            fp+=1
            if int(float(r.get("is_forklift_like",0)))==1:
                false_admit_forklift.append(r["sample_id"])
        else:
            fn+=1
            if int(float(r.get("is_infrastructure_like",0)))==1:
                false_reject_infra.append(r["sample_id"])
    n=tp+tn+fp+fn
    precision=tp/(tp+fp) if (tp+fp) else 0.0
    recall=tp/(tp+fn) if (tp+fn) else 0.0
    f1=2*precision*recall/(precision+recall) if (precision+recall) else 0.0
    return {
        "n":n,"tp":tp,"tn":tn,"fp":fp,"fn":fn,
        "accuracy":round((tp+tn)/n,4) if n else 0.0,
        "precision_admit":round(precision,4),
        "recall_admit":round(recall,4),
        "f1_admit":round(f1,4),
        "false_admit_forklift_like":false_admit_forklift,
        "false_reject_infrastructure_like":false_reject_infra,
    }


def evaluate(rows: list[dict[str, Any]], w: list[float], b: float) -> None:
    for r in rows:
        prob=sigmoid(sum(wi*xi for wi,xi in zip(w,r["x"]))+b)
        r["learned_probability"]=prob
        r["learned_pred"]=1 if prob>=0.5 else 0
        r["rule_pred"]=rule_predict(r)


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset", default="paper/evidence/admission_scorer_dataset_p190.csv")
    ap.add_argument("--output-json", default="paper/evidence/admission_scorer_smoke_p191.json")
    ap.add_argument("--output-md", default="paper/export/admission_scorer_smoke_p191.md")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=0.08)
    ap.add_argument("--l2", type=float, default=0.001)
    args=ap.parse_args()

    dataset=Path(args.dataset)
    raw=read_rows(dataset)
    train_raw=[r for r in raw if r["split"]=="train"]
    rows,stats=standardize(raw, train_raw)
    splits={s:[r for r in rows if r["split"]==s] for s in ["train","val","test"]}
    w,b,history=train_logreg(splits["train"], args.epochs, args.lr, args.l2)
    evaluate(rows,w,b)

    metrics={
        split:{
            "learned":summarize(srows,"learned_pred"),
            "rule_baseline":summarize(srows,"rule_pred"),
        }
        for split,srows in splits.items()
    }
    coeffs=sorted([
        {"feature":feat,"coefficient":round(wi,6)} for feat,wi in zip(FEATURE_FIELDS,w)
    ], key=lambda d: abs(d["coefficient"]), reverse=True)
    predictions=[{
        "sample_id":r["sample_id"],"split":r["split"],"canonical_label":r["canonical_label"],
        "target_admit":r["y"],"learned_probability":round(r["learned_probability"],6),
        "learned_pred":r["learned_pred"],"rule_pred":r["rule_pred"]
    } for r in rows]
    payload={
        "phase":"P191-admission-scorer-smoke",
        "dataset":str(dataset),
        "model":"pure_python_logistic_regression",
        "epochs":args.epochs,"lr":args.lr,"l2":args.l2,
        "features":FEATURE_FIELDS,
        "standardization":stats,
        "training_history":history,
        "bias":round(b,6),
        "coefficients":coeffs,
        "metrics":metrics,
        "interpretation":"Feasibility smoke only: labels are weak labels from the current rule gate, so matching the rule baseline is expected and not evidence of a stronger learned method.",
        "predictions":predictions,
    }
    out_json=Path(args.output_json); out_md=Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True); out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    lines=[
        "# P191 Admission-Scorer Learned Smoke",
        "",
        "**Status:** CPU-only pure-Python logistic-regression smoke completed.",
        "",
        "## Metrics",
        "",
    ]
    for split in ["train","val","test"]:
        learned=metrics[split]["learned"]; rule=metrics[split]["rule_baseline"]
        lines += [
            f"### {split}",
            f"- Learned: accuracy={learned['accuracy']:.4f}, precision={learned['precision_admit']:.4f}, recall={learned['recall_admit']:.4f}, F1={learned['f1_admit']:.4f}, fp={learned['fp']}, fn={learned['fn']}.",
            f"- Rule baseline: accuracy={rule['accuracy']:.4f}, precision={rule['precision_admit']:.4f}, recall={rule['recall_admit']:.4f}, F1={rule['f1_admit']:.4f}, fp={rule['fp']}, fn={rule['fn']}.",
            "",
        ]
    lines += [
        "## Largest Coefficients",
        "",
    ]
    for c in coeffs[:8]:
        lines.append(f"- `{c['feature']}`: {c['coefficient']:+.6f}")
    lines += [
        "",
        "## Interpretation",
        "",
        "This is a feasibility smoke, not a publication-grade learned component. The labels are weak labels generated by the current rule gate, so a learned model that matches the rule baseline mainly proves the dataset contract and training/evaluation plumbing. The next scientifically meaningful step is to add independent boundary labels or pairwise association supervision so the model can improve beyond rule imitation.",
        "",
    ]
    out_md.write_text("\n".join(lines)+"\n")
    print(json.dumps({"output_json":str(out_json),"output_md":str(out_md),"metrics":metrics,"top_coefficients":coeffs[:5]},indent=2))


if __name__ == "__main__":
    main()
