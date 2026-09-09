"""1~2단계 확인용: KoELECTRA 로드 및 한국어 문장 추론이 정상 동작하는지 점검."""

import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "monologg/koelectra-base-v3-discriminator"

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

SAMPLE_TEXTS = [
    "오늘 시험을 망쳐서 너무 속상하고 앞으로가 걱정된다.",
    "친구랑 오랜만에 만나서 정말 즐거운 하루였다.",
    "별일 없는 하루였다. 그냥 평범했다.",
]


def check_encoder(tokenizer):
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()

    inputs = tokenizer(SAMPLE_TEXTS, padding=True, truncation=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)

    print("[encoder] input_ids:", tuple(inputs["input_ids"].shape))
    print("[encoder] last_hidden_state:", tuple(outputs.last_hidden_state.shape))
    print("[encoder] 토큰 예시:", tokenizer.tokenize(SAMPLE_TEXTS[0])[:12])


def check_multilabel_head(tokenizer):
    """4단계에서 쓸 multi-label 구조가 붙는지 미리 확인 (분류 헤드는 아직 학습 전)."""
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(EMOTIONS),
        problem_type="multi_label_classification",
    )
    model.eval()

    inputs = tokenizer(SAMPLE_TEXTS[0], truncation=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits

    scores = torch.sigmoid(logits)[0]
    print("[head] logits:", tuple(logits.shape))
    print("[head] 미학습 상태 출력값:")
    for name, score in zip(EMOTIONS, scores.tolist()):
        print(f"  {name:>12}: {score * 100:5.1f}")


if __name__ == "__main__":
    print(f"모델: {MODEL_NAME}")
    print(f"device: {'cuda' if torch.cuda.is_available() else 'cpu'}\n")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    check_encoder(tokenizer)
    print()
    check_multilabel_head(tokenizer)
