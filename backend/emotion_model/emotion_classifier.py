"""Plutchik 8감정 multi-label 분류기. B 담당은 predict_emotions(text)만 호출하면 된다."""

from __future__ import annotations

import json
import os
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

EMOTIONS = [
    "joy",
    "trust",
    "fear",
    "surprise",
    "sadness",
    "disgust",
    "anger",
    "anticipation",
]

BASE_MODEL = "monologg/koelectra-base-v3-discriminator"
MODEL_DIR = Path(__file__).parent / "model"
THRESHOLD_FILE = MODEL_DIR / "thresholds.json"
MAX_LENGTH = 256


def load_thresholds() -> dict[str, float]:
    """evaluate.py가 validation F1로 정한 감정별 임계값. 없으면 0.5."""
    if THRESHOLD_FILE.exists():
        with open(THRESHOLD_FILE, encoding="utf-8") as f:
            saved = json.load(f)
        return {emotion: float(saved.get(emotion, 0.5)) for emotion in EMOTIONS}
    return {emotion: 0.5 for emotion in EMOTIONS}


def to_score_100(probability: float, threshold: float) -> int:
    """확률(0~1)을 0~100 점수로 변환.

    임계값이 정확히 50점에 오도록 구간별 선형 변환한다. 따라서 50점 이상이면
    "모델이 이 감정을 존재한다고 판단"과 같은 뜻이 되고, 감정마다 임계값이 달라도
    B가 받는 0~100 점수는 같은 기준으로 비교할 수 있다.
    """
    if probability <= threshold:
        scaled = probability / threshold * 50 if threshold > 0 else 0.0
    else:
        scaled = 50 + (probability - threshold) / (1 - threshold) * 50 if threshold < 1 else 100.0
    return int(round(min(max(scaled, 0.0), 100.0)))


class EmotionClassifier:
    def __init__(self, model_path: str | os.PathLike | None = None, device: str | None = None):
        source = str(model_path) if model_path else self._resolve_source()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(source)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            source,
            num_labels=len(EMOTIONS),
            problem_type="multi_label_classification",
        )
        self.model.to(self.device)
        self.model.eval()
        self.thresholds = load_thresholds()
        self.is_trained = source != BASE_MODEL

    @staticmethod
    def _resolve_source() -> str:
        # 학습 완료 모델이 있으면 그걸 쓰고, 없으면 미학습 베이스 모델로 폴백한다.
        return str(MODEL_DIR) if (MODEL_DIR / "config.json").exists() else BASE_MODEL

    @torch.no_grad()
    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt",
        ).to(self.device)
        probabilities = torch.sigmoid(self.model(**inputs).logits).cpu().tolist()
        return [dict(zip(EMOTIONS, row)) for row in probabilities]

    def predict_emotions(self, text: str) -> dict[str, int]:
        probabilities = self.predict_proba([text])[0]
        return {
            emotion: to_score_100(probabilities[emotion], self.thresholds[emotion])
            for emotion in EMOTIONS
        }


_classifier: EmotionClassifier | None = None


def get_classifier() -> EmotionClassifier:
    global _classifier
    if _classifier is None:
        _classifier = EmotionClassifier()
    return _classifier


def predict_emotions(text: str) -> dict[str, int]:
    """일기 텍스트 → Plutchik 8감정 점수(0~100). B 담당이 호출할 진입점."""
    return get_classifier().predict_emotions(text)


if __name__ == "__main__":
    classifier = get_classifier()
    if not classifier.is_trained:
        print("[경고] 학습된 모델이 없어 미학습 베이스 모델로 실행합니다. 점수는 무의미합니다.\n")

    for sample in [
        "오늘 발표 때문에 긴장됐지만 끝나고 기분이 좋았다.",
        "친구가 약속을 또 어겨서 정말 화가 났다.",
    ]:
        print(sample)
        for emotion, score in predict_emotions(sample).items():
            print(f"  {emotion:>12}: {score:3d}")
        print()
