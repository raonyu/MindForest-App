import os
import sys
from typing import Any

# 1. 최상위 backend 폴더(emotion_model이 있는 위치)를 파이썬 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))          # .../backend/B/backend/services
backend_dir = os.path.dirname(current_dir)                        # .../backend/B/backend
root_backend_dir = os.path.dirname(os.path.dirname(backend_dir))  # .../backend

if root_backend_dir not in sys.path:
    sys.path.append(root_backend_dir)

from services.bws_logic import run_bws_llm
from emotion_model.emotion_classifier import EMOTIONS, predict_emotions


def check_needs_bws(
    emotions: dict[str, int],
    threshold: int = 50,
    diff_margin: int = 8,
) -> tuple[bool, dict[str, int]]:
    """
    1차 모델 점수 중 임계값(50점) 이상인 유효 감정이 2개 이상이고,
    1위와 2위 감정의 점수 차이가 diff_margin(8점) 이하일 때 경합 상태로 판단한다.
    """
    high_items = sorted(
        ((k, v) for k, v in emotions.items() if v >= threshold),
        key=lambda item: item[1],
        reverse=True,
    )

    if len(high_items) >= 2:
        if (high_items[0][1] - high_items[1][1]) <= diff_margin:
            return True, dict(high_items)

    return False, {}


def analyze_emotion_pipeline(text: str) -> dict[str, Any] | None:
    """
    1차 KoELECTRA 다중 감정 분류 후, 상위 감정 경합 시 2차 BWS(LLM) 검증을 수행하는 하이브리드 파이프라인.
    """
    # [방어 로직 1] 텍스트가 비어있거나 공백만 있는 경우 모델 추론 생략
    if not text or not text.strip():
        return {
            "emotions": {emotion: 0 for emotion in EMOTIONS},
            "dominant_emotion": "joy",
            "confidence": 1.0,
            "needs_bws": False,
            "bws_used": False,
            "status": "empty_text",
            "analysis_comment": "",
        }

    # 1. KoELECTRA 모델로 8감정 점수(0~100) 1차 추출
    try:
        emotions = predict_emotions(text)
        print(f"[1차 KoELECTRA 모델 분석 완료] 점수: {emotions}")
    except Exception as e:
        print(f"[오류] 1차 AI 모델 호출 실패: {e}")
        return None

    # 기본 대표 감정은 1차 모델 최고점 감정으로 설정
    dominant_emotion = max(emotions, key=emotions.get) if emotions else "joy"

    # 2. BWS 필요 여부 판단 (50점 이상 & 1~2위 차이 8점 이하)
    needs_bws, high_emotions = check_needs_bws(emotions, threshold=50, diff_margin=8)
    bws_used = False
    bws_result: dict[str, Any] = {}
    analysis_comment = ""

    # 3. 경합 감정이 있으면 BWS(2차 검증) 실행
    if needs_bws:
        print(f"[2차 검증] 경합 감정 발견, BWS 검증 시작... 후보: {list(high_emotions.keys())}")
        # [방어 로직 2] 외부 API 호출 실패 시에도 1차 분석 결과는 안전하게 보존
        try:
            validation = run_bws_llm(text, high_emotions)
            if validation and validation.get("best_emotion"):
                bws_used = True
                bws_result = validation
                dominant_emotion = validation["best_emotion"]
                analysis_comment = validation.get("reasoning", "")
        except Exception as e:
            print(f"[경고] 2차 BWS 검증 중 오류 발생 (1차 모델 결과로 대체합니다): {e}")

    # 4. 최종 결과 반환
    result: dict[str, Any] = {
        "emotions": emotions,
        "dominant_emotion": dominant_emotion,
        "confidence": 0.84,
        "needs_bws": needs_bws,
        "bws_used": bws_used,
        "status": "completed",
        "analysis_comment": analysis_comment,
    }

    if bws_used:
        result["bws_validation"] = bws_result

    return result