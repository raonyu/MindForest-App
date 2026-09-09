"""Validation으로 감정별 threshold를 정하고, Test에서 Macro/Micro F1과 감정별 P/R을 출력."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score, precision_recall_fscore_support

from dataset import load_jsonl
from emotion_classifier import EMOTIONS, THRESHOLD_FILE, EmotionClassifier

DATA_DIR = Path(__file__).parent / "data"
THRESHOLD_GRID = np.arange(0.05, 0.96, 0.01)


def predict_all(classifier: EmotionClassifier, texts: list[str], batch_size: int) -> np.ndarray:
    rows = []
    for start in range(0, len(texts), batch_size):
        for probabilities in classifier.predict_proba(texts[start : start + batch_size]):
            rows.append([probabilities[emotion] for emotion in EMOTIONS])
    return np.array(rows)


def tune_thresholds(probabilities: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    """감정마다 F1이 최대가 되는 임계값을 따로 찾는다 (감정별 빈도가 크게 달라서)."""
    thresholds = {}
    for index, emotion in enumerate(EMOTIONS):
        scores = [
            f1_score(labels[:, index], (probabilities[:, index] >= t).astype(int), zero_division=0)
            for t in THRESHOLD_GRID
        ]
        best = int(np.argmax(scores))
        thresholds[emotion] = round(float(THRESHOLD_GRID[best]), 2)
        print(f"  {emotion:>12}: threshold {thresholds[emotion]:.2f} (val F1 {scores[best]:.4f})")
    return thresholds


def report(probabilities: np.ndarray, labels: np.ndarray, thresholds: dict[str, float]) -> dict:
    threshold_row = np.array([thresholds[emotion] for emotion in EMOTIONS])
    predictions = (probabilities >= threshold_row).astype(int)

    macro_f1 = f1_score(labels, predictions, average="macro", zero_division=0)
    micro_f1 = f1_score(labels, predictions, average="micro", zero_division=0)
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, predictions, average=None, zero_division=0, labels=range(len(EMOTIONS))
    )

    print(f"\nMacro F1: {macro_f1:.4f}")
    print(f"Micro F1: {micro_f1:.4f}\n")
    print(f"{'emotion':>12} {'thr':>5} {'P':>7} {'R':>7} {'F1':>7} {'support':>8}")
    for index, emotion in enumerate(EMOTIONS):
        print(
            f"{emotion:>12} {thresholds[emotion]:>5.2f} {precision[index]:>7.4f} "
            f"{recall[index]:>7.4f} {f1[index]:>7.4f} {int(support[index]):>8}"
        )

    return {
        "macro_f1": float(macro_f1),
        "micro_f1": float(micro_f1),
        "per_emotion": {
            emotion: {
                "threshold": thresholds[emotion],
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, emotion in enumerate(EMOTIONS)
        },
    }


def main(args) -> None:
    classifier = EmotionClassifier()
    if not classifier.is_trained:
        print("[경고] 학습된 모델이 없습니다. train.py를 먼저 실행하세요.\n")

    val_texts, val_labels = load_jsonl(args.val)
    print(f"[threshold 탐색] validation {len(val_texts)}건")
    val_probabilities = predict_all(classifier, val_texts, args.batch_size)
    thresholds = tune_thresholds(val_probabilities, np.array(val_labels))

    THRESHOLD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(THRESHOLD_FILE, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, ensure_ascii=False, indent=2)
    print(f"\nthreshold 저장: {THRESHOLD_FILE}")

    test_texts, test_labels = load_jsonl(args.test)
    print(f"\n[최종 평가] test {len(test_texts)}건")
    test_probabilities = predict_all(classifier, test_texts, args.batch_size)
    results = report(test_probabilities, np.array(test_labels), thresholds)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {args.output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--val", default=str(DATA_DIR / "val.jsonl"))
    parser.add_argument("--test", default=str(DATA_DIR / "test.jsonl"))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output", default=str(Path(__file__).parent / "model" / "test_results.json"))
    main(parser.parse_args())
