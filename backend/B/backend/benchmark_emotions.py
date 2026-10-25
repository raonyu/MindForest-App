"""Evaluate labeled JSONL with the real engine, or saved predictions without a model/API.

python benchmark_emotions.py --dataset labels.jsonl --predictions predictions.jsonl --output report.json
--gpt-predictions compares saved GPT-direct scores. --include-gpt explicitly enables paid GPT calls.
"""
import argparse
import json
import math
from pathlib import Path
from statistics import mean
from services.emotion_scores import EMOTIONS


def classification_metrics(labels, predictions):
    if not labels or len(labels) != len(predictions):
        raise ValueError("Labels and predictions must have the same nonzero length.")
    per = {}
    for emotion in EMOTIONS:
        tp = sum(bool(y[emotion]) and p[emotion] >= 50 for y,p in zip(labels,predictions))
        fp = sum(not bool(y[emotion]) and p[emotion] >= 50 for y,p in zip(labels,predictions))
        fn = sum(bool(y[emotion]) and p[emotion] < 50 for y,p in zip(labels,predictions))
        precision = tp/(tp+fp) if tp+fp else 0.0
        recall = tp/(tp+fn) if tp+fn else 0.0
        per[emotion] = {"precision":precision,"recall":recall,"f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,"support":tp+fn,"tp":tp,"fp":fp,"fn":fn}
    tp,fp,fn = (sum(p[k] for p in per.values()) for k in ("tp","fp","fn"))
    return {"samples":len(labels),"macro_f1":mean(p["f1"] for p in per.values()),
            "micro_f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,"per_emotion":per}


def load_rows(path):
    with open(path,encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def scores(row):
    values = row.get("emotions", {})
    if set(values) != set(EMOTIONS) or any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0 <= v <= 100 for v in values.values()):
        raise ValueError("Every prediction must contain all eight finite emotion scores (0..100).")
    return values


def evaluate(args):
    dataset = load_rows(args.dataset)
    if args.limit:
        dataset = dataset[:args.limit]
    labels = [row["labels"] for row in dataset]
    if any(set(y)!=set(EMOTIONS) or any(v not in (0,1) for v in y.values()) for y in labels):
        raise ValueError("Each sample needs eight binary labels, in a held-out evaluation dataset.")
    if args.predictions:
        predictions = load_rows(args.predictions)
        if args.limit:
            predictions=predictions[:args.limit]
    else:
        from services.emotion_pipeline import analyze_emotion_pipeline
        predictions=[analyze_emotion_pipeline(row["text"]) for row in dataset]
    if len(predictions)!=len(dataset):
        raise ValueError("Prediction and dataset row counts do not match.")
    for sample,prediction in zip(dataset,predictions):
        if "id" in sample and "id" in prediction and sample["id"]!=prediction["id"]:
            raise ValueError("Prediction IDs do not match dataset order.")
    result={"engine":classification_metrics(labels,[scores(p) for p in predictions])}
    measured=[p["metrics"] for p in predictions if "metrics" in p]
    times=[float(m["total_ms"]) for m in measured if m.get("total_ms") is not None]
    result["runtime"]={"measured_samples":len(measured),"bws_call_rate":mean(bool(m.get("bws_attempted")) for m in measured) if measured else None,
                       "average_analysis_ms":mean(times) if times else None}
    if args.gpt_predictions:
        baseline=load_rows(args.gpt_predictions)
        if args.limit: baseline=baseline[:args.limit]
        if len(baseline)!=len(dataset):
            raise ValueError("GPT baseline and dataset row counts do not match.")
        for sample,prediction in zip(dataset,baseline):
            if "id" in sample and "id" in prediction and sample["id"]!=prediction["id"]:
                raise ValueError("GPT baseline IDs do not match dataset order.")
    elif args.include_gpt:
        from services.ai_logic import analyze_diary_emotion
        baseline=[analyze_diary_emotion(row["text"]) or {} for row in dataset]
    else:
        baseline=None
    if baseline is not None:
        result["gpt_direct_baseline"]=classification_metrics(labels,[scores(p) for p in baseline])
    result["notes"]=["Decision threshold is score >= 50 for both methods; scores are not clinical intensity or risk probabilities.",
                     "Report accuracy only on held-out labels. Saved predictions do not verify a local model, and missing runtime measurements stay null.",
                     "KoELECTRA scores are unchanged by BWS; this F1 does not evaluate whether the BWS-selected representative emotion is correct."]
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset",required=True)
    parser.add_argument("--predictions")
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--gpt-predictions")
    group.add_argument("--include-gpt",action="store_true",help="Allow external GPT API calls (may incur charges).")
    parser.add_argument("--limit",type=int,default=0)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    if args.limit < 0: parser.error("--limit must be nonnegative")
    try:
        result=evaluate(args)
    except (ValueError,KeyError,TypeError) as exc:
        parser.exit(1,f"Evaluation failed: {exc}\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))
