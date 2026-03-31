import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 및 API 클라이언트 초기화
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# --- [신규] 9대 질환 및 동물 캐릭터 매핑 정보 ---
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
    [신규] 20문항 간이 설문 결과를 분석하여 9가지 질환 중 가장 적합한 카테고리를 결정합니다.
    survey_responses: "1. 예, 2. 아니오..." 형태의 문자열 또는 리스트
    """
    try:
        system_instruction = f"""
        너는 숙련된 심리 진단 전문가야. 사용자의 20가지 간단한 답변을 보고, 
        가장 가능성이 높은 정신건강 카테고리를 하나 골라줘.
        
        선택 가능한 카테고리: {list(DISEASE_ANIMAL_MAP.keys())}
        
        반드시 아래 JSON 형식으로만 대답해:
        {{
          "category": "카테고리명",
          "reason": "해당 카테고리로 분류한 간략한 이유"
        }}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"사용자 답변 내용: {survey_responses}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content)
        category = result.get("category")
        
        # 매핑 테이블에서 동물 이름과 설문지 정보 추가
        animal_info = DISEASE_ANIMAL_MAP.get(category, DISEASE_ANIMAL_MAP["DEPRESSION"])
        result.update(animal_info)
        
        return result
    except Exception as e:
        print(f"온보딩 분석 중 에러 발생: {e}")
        return None

def analyze_diary_emotion(diary_text):
    """
    사용자의 일기를 분석하여 8가지 감정 수치와 요약을 반환합니다.
    """
    try:
        system_instruction = """
        너는 전문 심리 상담사야. 사용자의 일기를 읽고 다음 8가지 감정 점수를 0~100 사이의 정수로 평가해줘.
        감정 종류: joy, trust, fear, surprise, sadness, disgust, anger, anticipation
        
        응답은 반드시 아래와 같은 JSON 형식으로만 대답해:
        {
          "emotions": { "joy": 0, "trust": 0, "fear": 0, "surprise": 0, "sadness": 0, "disgust": 0, "anger": 0, "anticipation": 0 },
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
        print(f"AI 분석 중 에러 발생: {e}")
        return None

def check_anomaly_level(recent_emotions_list):
    """
    [개선] 최근 데이터를 역순으로 확인하여 이상 징후를 감지합니다.
    - 민감도를 위해 기준 점수를 60점으로 하향 조정했습니다.
    - 공포(fear)와 혐오(disgust)를 부정 감정 지표에 추가했습니다.
    """
    if not recent_emotions_list:
        return {"level": "LOW", "message": "데이터가 없습니다."}

    consecutive_bad_days = 0
    THRESHOLD = 60 # 민감도 향상을 위해 70에서 60으로 하향
    
    for data in reversed(recent_emotions_list):
        # DB 모델 구조에 따라 data["emotions"] 혹은 d.sadness 형태일 수 있음
        # 여기서는 리스트 내 딕셔너리 구조라고 가정 (diary.py 전달 방식)
        emotions = data.get("emotions", {})
        
        # 부정 감정 중 가장 높은 점수 추출
        bad_score = max(
            emotions.get("sadness", 0),
            emotions.get("anger", 0),
            emotions.get("fear", 0),
            emotions.get("disgust", 0)
        )
        
        if bad_score >= THRESHOLD:
            consecutive_bad_days += 1
        else:
            break

    if consecutive_bad_days >= 7:
        return {
            "level": "HIGH", 
            "message": "일주일간 마음이 많이 힘드셨네요. 혼자 앓지 말고, 전문 상담 센터의 도움을 받아보시는 건 어떨까요?"
        }
    elif consecutive_bad_days >= 3:
        return {
            "level": "MEDIUM", 
            "message": "최근 며칠간 기분이 가라앉아 보여요. 잠시 숨을 고르고 가벼운 산책을 해보는 건 어떨까요?"
        }
    else:
        return {
            "level": "LOW", 
            "message": "안정적인 감정 패턴을 유지하고 있습니다."
        }

def generate_weekly_report(weekly_emotions_list):
    """
    일주일 치 데이터를 모아서 종합적인 주간 리포트 코멘트를 생성합니다.
    """
    if len(weekly_emotions_list) < 7:
        return "아직 일주일 치 일기가 다 모이지 않았어요. 조금 더 기록해 볼까요?"

    total_sadness = sum(d.get("emotions", {}).get("sadness", 0) for d in weekly_emotions_list)
    total_joy = sum(d.get("emotions", {}).get("joy", 0) for d in weekly_emotions_list)

    if total_sadness > total_joy * 1.5:
        return "이번 주는 마음속에 비가 오는 날이 많았네요. 다음 주는 조금 더 맑게 갤 거예요."
    elif total_joy > total_sadness * 1.5:
        return "이번 주는 햇살이 가득한 한 주였네요! 이 긍정적인 에너지를 계속 이어가 볼까요?"
    else:
        return "이번 주는 여러 감정이 교차하는 다채로운 한 주였네요. 수고 많으셨습니다."