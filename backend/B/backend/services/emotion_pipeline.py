import sys
import os
import json

from services.bws_logic import run_bws_llm
from services.ai_logic import analyze_diary_emotion 

def check_needs_bws(emotions, threshold=50, diff_margin=8):
    high_emotions = {k: v for k, v in emotions.items() if v >= threshold}
    
    if len(high_emotions) >= 2:
        sorted_scores = sorted(high_emotions.values(), reverse=True)
        if (sorted_scores[0] - sorted_scores[1]) <= diff_margin:
            return True, high_emotions
            
    return False, {}

def analyze_emotion_pipeline(text):
    # 1. GPT 감정 분석 함수를 호출. (가짜 모델 대체재)
    base_analysis = analyze_diary_emotion(text)
    
    if not base_analysis:
        return None
        
    emotions = base_analysis.get("emotions", {})
    
    # 2. BWS 필요 여부 판단
    needs_bws, high_emotions = check_needs_bws(emotions, threshold=50, diff_margin=8)
    bws_used = False
    bws_result = {}
    
    # 3. 필요하면 BWS 실행
    if needs_bws:
        print(f"🔍 경합 감정 발견! BWS 검증 시작... 후보: {list(high_emotions.keys())}")
        bws_result = run_bws_llm(text, high_emotions)
        bws_used = True
        
    # 4. 최종 JSON 규격 맞춰서 내보내기 
    result = {
        "emotions": emotions,
        "confidence": 0.84,
        "needs_bws": needs_bws,
        "bws_used": bws_used,
        "status": "completed",
        "analysis_comment": base_analysis.get("analysis_comment", "")
    }
    
    if bws_used:
        result["bws_validation"] = bws_result
        
    return result