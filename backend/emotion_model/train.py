"""KoELECTRA multi-label fine-tuning. 8개 sigmoid + BCE 손실."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from dataset import EmotionDataset, load_jsonl
from emotion_classifier import BASE_MODEL, EMOTIONS, MODEL_DIR

DATA_DIR = Path(__file__).parent / "data"


def evaluate_loss(model, loader, device) -> float:
    model.eval()
    total, batches = 0.0, 0
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            total += model(**batch).loss.item()
            batches += 1
    return total / max(batches, 1)


def train(args) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(EMOTIONS),
        problem_type="multi_label_classification",
    ).to(device)

    train_texts, train_labels = load_jsonl(args.train)
    val_texts, val_labels = load_jsonl(args.val)
    print(f"train: {len(train_texts)}건 / val: {len(val_texts)}건")

    train_loader = DataLoader(
        EmotionDataset(train_texts, train_labels, tokenizer),
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        EmotionDataset(val_texts, val_labels, tokenizer),
        batch_size=args.batch_size,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(total_steps * 0.1), total_steps)

    best_val_loss = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0

        for step, batch in enumerate(train_loader, start=1):
            batch = {key: value.to(device) for key, value in batch.items()}
            loss = model(**batch).loss

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            running_loss += loss.item()
            if step % args.log_every == 0:
                print(f"  epoch {epoch} step {step}/{len(train_loader)} loss {running_loss / step:.4f}")

        val_loss = evaluate_loss(model, val_loader, device)
        print(f"epoch {epoch}: train {running_loss / len(train_loader):.4f} / val {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(MODEL_DIR)
            tokenizer.save_pretrained(MODEL_DIR)
            print(f"  → 저장 (val loss 갱신): {MODEL_DIR}")

    print(f"\n완료. best val loss {best_val_loss:.4f}")
    print("다음: evaluate.py로 감정별 threshold를 정하세요.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default=str(DATA_DIR / "train.jsonl"))
    parser.add_argument("--val", default=str(DATA_DIR / "val.jsonl"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--log-every", type=int, default=20)
    train(parser.parse_args())
