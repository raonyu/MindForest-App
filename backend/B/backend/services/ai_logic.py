import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 및 API 클라이언트 초기화
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# --- [1] 9대 질환 및 동물 캐릭터 매핑 정보 ---
DISEASE_ANIMAL_MAP = {
    "DEPRESSION": {"name": "조용히 움츠린 거북이", "survey": "PHQ-9"},
    "BIPOLAR": {"name": "알록달록 카멜레온", "survey": "K-MDQ"},
    "ANXIETY": {"name": "안절부절 미어캣", "survey": "GAD-7"},
    "SCHIZOPHRENIA": {"name": "몽환적인 검은 고양이", "survey": "PRIME-Screen"},
    "PTSD": {"name": "상처를 방패 삼은 고슴도치", "survey": "PCL-5"},
    "OCD": {"name": "정리대장 펭귄", "survey": "Y-BOCS"},
    "ADHD": {"name": "산만한 꼬마 다람쥐", "survey": "ASRS"},
    "EATING_DISORDER": {"name": "마음을 채우는 판다", "survey": "EAT-26"},
    "ANGER": {"name": "까칠한 햄스터", "survey": "DAR-5"}
}

def analyze_onboarding_survey(survey_responses):
    """
    온보딩 설문 결과를 분석하여 카테고리를 결정합니다.
    """
    try:
        system_instruction = f"""
        너는 숙련된 심리 진단 전문가야. 사용자의 답변을 보고 가장 적합한 카테고리를 골라줘.
        선택 가능한 카테고리: {list(DISEASE_ANIMAL_MAP.keys())}
        
        반드시 아래 JSON 형식으로만 대답해:
        {{
          "category": "카테고리명",
          "reason": "분류 이유"
        }}
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"사용자 답변: {survey_responses}"}
            ],
            response_format={ "type": "json_object" }
        )
        result = json.loads(response.choices[0].message.content)
        animal_info = DISEASE_ANIMAL_MAP.get(result.get("category"), DISEASE_ANIMAL_MAP["DEPRESSION"])
        result.update(animal_info)
        return result
    except Exception as e:
        print(f"온보딩 분석 에러: {e}")
        return None

def analyze_diary_emotion(diary_text):
    """
    [수정] 감정 8종 분석 + 조원 C의 로직을 위한 '마음 온도(mind_temperature)' 측정 추가.
    이 온도는 나중에 score_diff를 계산하는 기초 데이터가 됩니다.
    """
    try:
        system_instruction = """
        너는 전문 심리 상담사야. 사용자의 일기를 읽고 다음을 분석해줘.
        1. 8가지 감정 수치 (0~100)
        2. 현재 사용자의 '마음 온도' (0~100점: 높을수록 심리적으로 안정되고 긍정적인 상태)
        
        응답 형식(JSON):
        {
          "emotions": { "joy": 0, "trust": 0, "fear": 0, "surprise": 0, "sadness": 0, "disgust": 0, "anger": 0, "anticipation": 0 },
          "mind_temperature": 0,
          "analysis_comment": "분석 결과 요약"
        }
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": diary_text}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"일기 분석 에러: {e}")
        return None

def check_anomaly_level(recent_emotions_list):
    """
    최근 감정 흐름을 분석하여 이상 징후 감지 (기존 로직 유지)
    """
    if not recent_emotions_list:
        return {"level": "LOW", "message": "데이터가 없습니다."}

    consecutive_bad_days = 0
    THRESHOLD = 60 
    
    for data in reversed(recent_emotions_list):
        emotions = data.get("emotions", {})
        bad_score = max(
            emotions.get("sadness", 0), emotions.get("anger", 0),
            emotions.get("fear", 0), emotions.get("disgust", 0)
        )
        if bad_score >= THRESHOLD:
            consecutive_bad_days += 1
        else:
            break

    if consecutive_bad_days >= 7:
        return {"level": "HIGH", "message": "일주일간 마음이 많이 힘드셨네요. 전문가의 도움을 권장합니다."}
    elif consecutive_bad_days >= 3:
        return {"level": "MEDIUM", "message": "최근 며칠간 기분이 가라앉아 보여요. 가벼운 산책은 어떨까요?"}
    return {"level": "LOW", "message": "안정적인 감정 패턴을 유지하고 있습니다."}

# --- [신규] 조원 C의 로직을 지원하는 난이도 조절 보조 함수 ---
def decide_next_routine_difficulty(score_diff: float):
    """
    [C의 routine_manager 연동용] 
    마음 온도 변화량(score_diff)을 보고 다음 루틴의 난이도를 결정합니다.
    """
    # 변화량이 크면(효과가 좋으면) 난이도를 유지하거나 조금 올림
    if score_diff >= 10.0:
        return "CHALLENGE"  # 혹은 "MAINTAIN"
    # 변화량이 적으면(효과가 미미하면) 난이도를 낮추거나 다른 유형 추천
    elif score_diff < 5.0:
        return "EASY"
    else:
        return "NORMAL"