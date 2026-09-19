import sys
import os
import json
import re
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from openai import OpenAI

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 파이썬 모듈 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from B.backend.routine_manager import routine_manager
except ImportError:
    routine_manager = None

# models.py에서 Diary 모델 가져오기 (경로 매핑 완료)
try:
    from B.backend.models import Diary 
except ImportError:
    pass

# ---------------------------------------------------------
# [지표 7] 루틴과 감정 변화 (베이스라인 대비 순수 기여도 분석)
# ---------------------------------------------------------
def analyze_routine_effect(diaries):
    if not diaries:
        return {"status": "insufficient", "data": []}

    total_temps = []
    routine_stats = defaultdict(lambda: {"temps": [], "count": 0})
    
    for d in diaries:
        # models.py 구조에 맞춘 8감정 기반 마음 온도 계산
        pos = getattr(d, 'joy', 0.0) + getattr(d, 'trust', 0.0) + getattr(d, 'anticipation', 0.0) + getattr(d, 'surprise', 0.0)
        neg = getattr(d, 'sadness', 0.0) + getattr(d, 'anger', 0.0) + getattr(d, 'fear', 0.0) + getattr(d, 'disgust', 0.0)
        real_temp = pos - neg
        
        total_temps.append(real_temp)
        
        # 루틴 기록 수집
        routine_name = getattr(d, 'routine_name', None)
        if getattr(d, 'is_done', False) and routine_name:
            routine_stats[routine_name]["temps"].append(real_temp)
            routine_stats[routine_name]["count"] += 1

    baseline_temp = sum(total_temps) / len(total_temps) if total_temps else 0.0

    effects = []
    for name, stat in routine_stats.items():
        if stat["count"] >= 2: # 최소 2회 이상 수행 시 신뢰도 확보
            routine_avg = sum(stat["temps"]) / len(stat["temps"])
            net_effect = round(routine_avg - baseline_temp, 1) 
            
            effects.append({
                "routine_name": name,
                "avg_effect": f"+{net_effect}" if net_effect > 0 else str(net_effect),
                "count_based": stat["count"]
            })
            
    effects = sorted(effects, key=lambda x: float(x["avg_effect"]), reverse=True)
    return {"status": "ready" if effects else "insufficient", "data": effects}

# ---------------------------------------------------------
# [지표 6] 주요 상황·키워드 (LLM 기반 핵심 명사 추출)
# ---------------------------------------------------------
def extract_keywords_and_context(diaries):
    if not diaries:
        return {"summary_message": "작성된 일기가 없어 키워드를 분석할 수 없어요.", "keywords": []}

    diary_texts = []
    emotion_history = [] 

    for d in diaries:
        raw_content = getattr(d, 'content', "")
        main_text = ""
        try:
            main_text = json.loads(raw_content).get("mainText", "")
        except:
            main_text = raw_content

        if main_text:
            clipped = main_text[:300]
            diary_texts.append(clipped)
            
            emotions_dict = {
                "joy": getattr(d, 'joy', 0.0), "sadness": getattr(d, 'sadness', 0.0), 
                "anger": getattr(d, 'anger', 0.0), "fear": getattr(d, 'fear', 0.0), 
                "trust": getattr(d, 'trust', 0.0), "disgust": getattr(d, 'disgust', 0.0)
            }
            ai_top_emo = max(emotions_dict, key=emotions_dict.get) if sum(emotions_dict.values()) > 0 else "joy"
            emotion_history.append((clipped, ai_top_emo))

    if not diary_texts:
        return {"summary_message": "일기 내용이 짧아 키워드를 분석할 수 없어요.", "keywords": []}

    # GPT에게 핵심 키워드 3개 단순/명확하게 추출 요청
    prompt = f"""
    아래는 사용자가 일주일간 작성한 일기 내용입니다.
    이 일기들에서 가장 핵심이 되는 주요 키워드(명사)를 최대 3개만 추출해주세요.
    (예: 친구, 가족, 취업, 시험, 수면, 운동 등 인물이나 일상적인 단어도 모두 포함 가능)
    
    일기: {diary_texts}
    
    반드시 아래 JSON 형식으로만 응답하세요.
    {{"keywords": ["단어1", "단어2", "단어3"]}}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        top_keywords = json.loads(response.choices[0].message.content).get("keywords", [])
    except:
        top_keywords = []

    context_analysis = []
    for kw in top_keywords:
        matched = [emo for text, emo in emotion_history if kw in text]
        if matched:
            most_common_emo = Counter(matched).most_common(1)[0][0]
            context_analysis.append({
                "keyword": kw,
                "frequent_emotion": most_common_emo,
                "count": len(matched)
            })

    sorted_contexts = sorted(context_analysis, key=lambda x: x["count"], reverse=True)[:3]

    # 1회 등장 엣지케이스 방어용 동적 코멘트
    if not sorted_contexts:
        summary_msg = "주요 키워드를 뽑기에 일기 내용이 조금 부족했어요."
    elif sorted_contexts[0]["count"] == 1:
        summary_msg = "이번 주는 특정한 하나의 주제보다는, 다채롭고 다양한 일상을 보내셨군요!"
    else:
        summary_msg = f"이번 주 유저님의 마음속 가장 큰 자리를 차지한 키워드는 '{sorted_contexts[0]['keyword']}'(이)네요."

    return {
        "summary_message": summary_msg,
        "keywords": sorted_contexts
    }

# ---------------------------------------------------------
# [지표 8] 맞춤 루틴 추천 (Two-Track 추천 알고리즘)
# ---------------------------------------------------------
def get_personalized_recommendations(diaries, user_category="DEPRESSION"):
    effect_result = analyze_routine_effect(diaries)
    
    # Track A: 초기 유저 (Cold Start)
    if effect_result["status"] == "insufficient":
        try:
            recs = routine_manager._pick_routine_contents_from_categories([user_category])
            return [{"routine": r, "reason": "아직 숲에 오신 지 얼마 안 돼서, 현재 마음에 가장 알맞은 루틴을 준비했어요."} for r in recs]
        except:
            return [{"routine": "가벼운 동네 산책하기", "reason": "마음을 환기하는 데 가장 좋은 기본 루틴이에요."}]

    # Track B: 데이터 보유 유저 (Exploitation & Exploration)
    recommendations = []
    best = effect_result["data"]
    
    recommendations.append({
        "routine": best[0]["routine_name"],
        "reason": f"분석 결과, 이 루틴을 했을 때 평소보다 마음 온도가 평균 {best[0]['avg_effect']}도 상승했어요!"
    })

    if len(best) > 1:
        recommendations.append({
            "routine": best[1]["routine_name"],
            "reason": "이 루틴도 유저님의 긍정적인 감정을 끌어올리는 데 큰 도움이 되었네요."
        })
        
    try:
        if routine_manager:
            for rec in routine_manager._pick_routine_contents_from_categories([user_category]):
                if not any(r["routine"] == rec for r in recommendations):
                    recommendations.append({"routine": rec, "reason": "지루하지 않게 숲지기가 새로운 루틴도 하나 추천해 드려요!"})
                    break
    except:
        pass

    return recommendations[:3] 

# =========================================================
# [Weekly Report: Part 3 Indicators API]
# 파트 3 (루틴 기여도, 주간 키워드, 맞춤 추천) 전용 데이터 생성 함수
#
# API 라우터 담당자님(파트 1) 필독:
# 이 함수는 '주간 리포트 전체'가 아닌 '파트 3'에 해당하는 지표 데이터만 생성합니다.
# DB 세션(db_session)과 user_id(문자열)를 넘겨주시면 최근 7일 치 일기를 
# 직접 필터링하여 파트 3용 분석 결과(dict)를 반환합니다.
# 라우터에서 이 결과를 받아 다른 파트의 지표(마음 온도 등)와 병합하여 프론트로 전달해 주세요.
# =========================================================
def generate_weekly_report(db_session, user_id: str):
    try:
        # 1. DB 직접 조회: UTC 기준으로 오늘부터 7일 전(168시간) 이내의 일기 필터링
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_diaries = db_session.query(Diary).filter(
            Diary.user_id == user_id,
            Diary.created_at >= seven_days_ago
        ).all()
        
        # 2. 예외 처리: 최근 7일간 기록된 일기가 없는 경우
        if not recent_diaries:
            return {
                "status": "empty", 
                "message": "최근 7일간 작성된 일기가 없어 분석할 수 없습니다.",
                "data": None
            }
            
        # 3. 파트 3 담당 분석 엔진 가동
        keywords_data = extract_keywords_and_context(recent_diaries)
        routine_data = get_personalized_recommendations(recent_diaries, user_category="DEPRESSION") # 추후 User 테이블에서 카테고리 연동 가능
        
        # 4. 파트 3 지표용 JSON 반환
        return {
            "status": "success",
            "message": "파트 3 지표 생성 완료",
            "data": {
                "analyzed_count": len(recent_diaries),
                "part3_indicators": {
                    "keywords_analysis": keywords_data,
                    "routine_recommendations": routine_data
                }
            }
        }
    except Exception as e:
        print(f"Part 3 Report Generation Error: {e}")
        return {
            "status": "error", 
            "message": f"파트 3 지표 생성 중 내부 오류 발생: {e}",
            "data": None
        }