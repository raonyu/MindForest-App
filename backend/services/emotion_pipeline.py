import sys
import os
import json

# 현재 파일(emotion_pipeline.py)이 있는 services의 상위 폴더(backend)를 파이썬 경로에 강제로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from bws_logic import run_bws_llm
from emotion_model.emotion_classifier import predict_emotions


def check_needs_bws(emotions, threshold=50, diff_margin=8):
    """
    A 모델 기준: 50점 이상이면 유효한 감정 (threshold=50으로 수정)
    """
    high_emotions = {k: v for k, v in emotions.items() if v >= threshold}
    
    if len(high_emotions) >= 2:
        sorted_scores = sorted(high_emotions.values(), reverse=True)
        if (sorted_scores[0] - sorted_scores[1]) <= diff_margin:
            return True, high_emotions
            
    return False, {}

def analyze_emotion_pipeline(text):
    # 1. A의 '진짜' 인공지능 모델 호출 (Mock 함수 삭제됨)
    emotions = predict_emotions(text)
    
    # 2. BWS 필요 여부 판단
    needs_bws, high_emotions = check_needs_bws(emotions, threshold=50, diff_margin=8)
    bws_used = False
    
    # 3. 필요하면 BWS 실행
    if needs_bws:
        print(f"🔍 경합 감정 발견! BWS 검증 시작... 후보: {list(high_emotions.keys())}")
        bws_result = run_bws_llm(text, high_emotions)
        bws_used = True
        
    # 4. C에게 전달할 최종 JSON 규격
    result = {
        "emotions": emotions,
        "confidence": 0.84, # (추후 A 모델이 신뢰도도 리턴하게 되면 변수 교체)
        "needs_bws": needs_bws,
        "bws_used": bws_used,
        "status": "completed"
    }
    
    if bws_used:
        result["bws_validation"] = bws_result
        
    return result

# --- 테스트 실행 ---
if __name__ == "__main__":
    test_text = "오늘 발표 때문에 긴장됐지만 끝나고 기분이 좋았다."
    final_output = analyze_emotion_pipeline(test_text)
    print(json.dumps(final_output, indent=2, ensure_ascii=False))