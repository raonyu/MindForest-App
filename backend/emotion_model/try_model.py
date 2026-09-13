"""직접 문장을 넣어보는 테스트용 스크립트.

    python try_model.py                      # 대화형 (문장 입력 반복)
    python try_model.py "오늘 진짜 힘들었다"   # 한 문장만 바로 확인
"""

from __future__ import annotations

import sys

from emotion_classifier import EMOTIONS, get_classifier


def show(classifier, text: str) -> None:
    probabilities = classifier.predict_proba([text])[0]
    scores = classifier.predict_emotions(text)

    print(f"\n입력: {text}")
    print(f"{'emotion':>12} {'확률':>7} {'thr':>6} {'점수':>5}   판정")
    print("-" * 48)
    for emotion in sorted(EMOTIONS, key=lambda e: scores[e], reverse=True):
        threshold = classifier.thresholds[emotion]
        mark = "●" if probabilities[emotion] >= threshold else "·"
        print(
            f"{emotion:>12} {probabilities[emotion]:>7.3f} {threshold:>6.2f} "
            f"{scores[emotion]:>5d}   {mark}"
        )

    detected = [e for e in EMOTIONS if probabilities[e] >= classifier.thresholds[e]]
    print(f"\n감지된 감정: {', '.join(detected) if detected else '없음'}")


def main() -> None:
    classifier = get_classifier()
    if not classifier.is_trained:
        print("[경고] 학습된 모델이 없습니다. train.py를 먼저 실행하세요.")

    if len(sys.argv) > 1:
        show(classifier, " ".join(sys.argv[1:]))
        return

    print("문장을 입력하세요. (빈 줄 또는 Ctrl+C로 종료)")
    while True:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        show(classifier, text)


if __name__ == "__main__":
    main()
