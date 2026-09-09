"""B 담당이 전달하는 multi-label JSONL을 읽어들이는 부분."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from torch.utils.data import Dataset

from emotion_classifier import EMOTIONS, MAX_LENGTH


def load_jsonl(path: str | Path) -> tuple[list[str], list[list[float]]]:
    """{"text": ..., "labels": {"joy": 1, ...}} 형식의 JSONL을 읽는다."""
    texts: list[str] = []
    labels: list[list[float]] = []

    with open(path, encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = record.get("text")
            record_labels = record.get("labels")
            if not text or record_labels is None:
                raise ValueError(f"{path}:{line_number} — text 또는 labels 누락")

            missing = [emotion for emotion in EMOTIONS if emotion not in record_labels]
            if missing:
                raise ValueError(f"{path}:{line_number} — 감정 키 누락: {missing}")

            texts.append(text)
            labels.append([float(record_labels[emotion]) for emotion in EMOTIONS])

    return texts, labels


class EmotionDataset(Dataset):
    def __init__(self, texts: list[str], labels: list[list[float]], tokenizer):
        self.encodings = tokenizer(
            texts,
            padding="max_length",
            truncation=True,
            max_length=MAX_LENGTH,
        )
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        item = {key: torch.tensor(value[index]) for key, value in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[index], dtype=torch.float)
        return item
