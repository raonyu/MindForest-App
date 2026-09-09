"""B 담당 데이터가 오기 전까지 파이프라인을 돌려보기 위한 Mock 데이터 생성기.

실제 데이터가 도착하면 이 파일은 쓰지 않는다. 형식(JSONL)만 동일하게 맞춰 두었으므로
data/train.jsonl 등을 실제 파일로 교체하면 train.py / evaluate.py는 그대로 동작한다.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from emotion_classifier import EMOTIONS

DATA_DIR = Path(__file__).parent / "data"

# (문장 템플릿, 켜져 있는 감정) — 실제 라벨 분포를 흉내내기 위해 다중 감정도 섞는다.
TEMPLATES: list[tuple[str, list[str]]] = [
    ("오늘 {subject} 덕분에 하루 종일 기분이 좋았다.", ["joy"]),
    ("{subject} 때문에 정말 화가 나서 참기 힘들었다.", ["anger"]),
    ("{subject} 생각하면 아직도 눈물이 난다.", ["sadness"]),
    ("내일 {subject} 어떻게 될지 너무 무섭고 걱정된다.", ["fear"]),
    ("{subject}이(가) 갑자기 그렇게 될 줄은 정말 몰랐다.", ["surprise"]),
    ("{subject} 하는 짓을 보니 정말 역겨웠다.", ["disgust"]),
    ("다음 주 {subject}이(가) 벌써부터 기대된다.", ["anticipation"]),
    ("{subject}은(는) 언제나 내 편이라 믿음이 간다.", ["trust"]),
    ("{subject} 때문에 긴장했지만 끝나고 나니 뿌듯했다.", ["joy", "fear"]),
    ("{subject}이(가) 잘 되기를 기대하면서도 잘못될까 두렵다.", ["anticipation", "fear"]),
    ("{subject} 소식을 듣고 놀랐지만 정말 기뻤다.", ["surprise", "joy"]),
    ("{subject}에게 실망해서 슬프고 화가 났다.", ["sadness", "anger"]),
    ("{subject}을(를) 믿고 맡겼는데 결과가 기대된다.", ["trust", "anticipation"]),
    ("{subject} 이야기를 듣고 슬프면서도 무서웠다.", ["sadness", "fear"]),
    ("오늘은 {subject} 말고는 특별한 일이 없는 하루였다.", []),
]

SUBJECTS = [
    "친구", "가족", "회사 동료", "발표", "시험", "면접", "여행 계획", "새 프로젝트",
    "동생", "팀장님", "이사 준비", "건강검진 결과", "고양이", "졸업식", "아르바이트",
]


def make_records(count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    records = []
    for _ in range(count):
        template, active = rng.choice(TEMPLATES)
        text = template.format(subject=rng.choice(SUBJECTS))
        records.append(
            {
                "text": text,
                "labels": {emotion: int(emotion in active) for emotion in EMOTIONS},
            }
        )
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{path.name}: {len(records)}건")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=int, default=400)
    parser.add_argument("--val", type=int, default=100)
    parser.add_argument("--test", type=int, default=100)
    args = parser.parse_args()

    write_jsonl(DATA_DIR / "train.jsonl", make_records(args.train, seed=1))
    write_jsonl(DATA_DIR / "val.jsonl", make_records(args.val, seed=2))
    write_jsonl(DATA_DIR / "test.jsonl", make_records(args.test, seed=3))
    print(f"\n생성 위치: {DATA_DIR}")
