# emotion_model — 한국어 Plutchik 8감정 분류 모델 (A 담당)

일기 텍스트를 넣으면 Plutchik 8개 감정 점수(0~100)를 반환한다. 기존 GPT 직접 채점
방식(`ai_logic.py`)을 대체하는 것이 목표이며, 비교용으로 기존 코드는 그대로 둔다.

## B 담당이 쓰는 방법

```python
from emotion_classifier import predict_emotions

predict_emotions("오늘 발표 때문에 긴장됐지만 끝나고 기분이 좋았다.")
# {'joy': 72, 'trust': 45, 'fear': 20, 'surprise': 15,
#  'sadness': 78, 'disgust': 12, 'anger': 76, 'anticipation': 35}
```

- 첫 호출에서 모델을 메모리에 올리고 이후 재사용한다(모듈 내 싱글턴).
- `model/`에 학습된 모델이 있으면 그것을, 없으면 미학습 베이스 모델로 폴백한다.
  폴백 상태의 점수는 의미가 없으므로 `EmotionClassifier().is_trained`로 확인 가능.

## 0~1 → 0~100 변환 규칙

모델의 raw 출력은 감정별 sigmoid 확률(0~1)이다. 이를 0~100으로 바꿀 때 **단순히
100을 곱하지 않는다.** 감정마다 threshold가 다르기 때문에, 그렇게 하면 "60점"이
감정마다 다른 의미가 되어 버린다.

대신 **해당 감정의 threshold가 정확히 50점에 오도록** 구간별 선형 변환한다:

```
확률 <= threshold : score = (확률 / threshold) * 50
확률 >  threshold : score = 50 + (확률 - threshold) / (1 - threshold) * 50
```

따라서 **50점 이상 = 모델이 그 감정이 존재한다고 판단**이라는 뜻이며, 감정별
threshold가 달라도 B가 받는 점수는 같은 기준으로 비교·표시할 수 있다.
구현은 `emotion_classifier.to_score_100()`.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `emotion_classifier.py` | 모델 로딩 + `predict_emotions()` + 점수 변환. **B가 import하는 파일** |
| `dataset.py` | B가 준 JSONL 로딩 |
| `train.py` | KoELECTRA fine-tuning (8 sigmoid + BCE) |
| `evaluate.py` | 감정별 threshold 탐색 + Macro/Micro F1, 감정별 P/R 리포트 |
| `make_mock_data.py` | 실데이터 도착 전 파이프라인 검증용 더미 데이터 |
| `check_model.py` | 1단계 점검용 (베이스 모델 로딩/추론 확인) |
| `model/` | 학습된 모델, `thresholds.json`, `test_results.json` |

## A가 필요한 데이터 형식 (B → A)

JSONL, 한 줄에 한 건. `train.jsonl` / `val.jsonl` / `test.jsonl`을 `data/`에 넣으면 된다.

```json
{"text": "오늘 발표 때문에 긴장됐지만 끝나고 기분이 좋았다.", "labels": {"joy": 1, "trust": 0, "fear": 1, "surprise": 0, "sadness": 0, "disgust": 0, "anger": 0, "anticipation": 1}}
```

- 8개 감정 키가 **모두** 있어야 한다(0 또는 1). 하나라도 빠지면 로딩 시 에러.
- 여러 감정이 동시에 1일 수 있다(multi-label).

## 실행 순서

```bash
pip install -r requirements.txt

python make_mock_data.py      # 실데이터 없을 때만
python train.py --epochs 3
python evaluate.py            # thresholds.json + test_results.json 생성
python emotion_classifier.py  # 동작 확인
```

## 개발 환경 (GPU)

RTX 2070 + 드라이버 457.20 조합에서 **드라이버 업데이트 없이** GPU 학습이 된다.
CUDA 11.8의 Windows 최소 드라이버 요구사항이 452.39라 현재 드라이버로 충족되기 때문.
따라서 최신 torch(cu126 이상)가 아니라 **cu118 빌드를 고정해서 쓴다**.

```bash
pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu118
```

## 알려진 제약

- **학습 데이터 미확정**: 국립국어원 AI말평 감정 분석 데이터가 Plutchik 8감정
  multi-label로 정확히 일치하지만, 이용 약관이 "말평 참여 목적"으로 제한된다.
  서비스 투입 전 라이선스 확인 필요.
- **현재 `model/`은 Mock 데이터로 학습된 것**이라 점수에 의미가 없다. B의 실데이터가
  들어오면 `data/`의 JSONL을 교체하고 `train.py` → `evaluate.py`를 다시 돌려야 한다.
