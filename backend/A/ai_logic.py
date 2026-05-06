import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 및 API 클라이언트 초기화
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def analyze_diary_emotion(diary_text):
    """
    [핵심 AI 엔진] 
    사용자의 일기 텍스트를 분석하여 8가지 감정 수치만 JSON 형식으로 반환합니다.
    """
    try:
        system_instruction = """
        너는 텍스트 감정 분석기야. 
        사용자의 일기를 읽고 다음 8가지 감정 점수를 0~100 사이의 정수로 평가해줘.
        감정 종류: joy, trust, fear, surprise, sadness, disgust, anger, anticipation
        
        [출력 규칙 - 매우 중요!]
        부연 설명이나 위로의 말은 절대 작성하지 마.
        반드시 아래와 같은 JSON 형식으로만 대답해:
        {
          "emotions": { "joy": 0, "trust": 0, "fear": 0, "surprise": 0, "sadness": 0, "disgust": 0, "anger": 0, "anticipation": 0 }
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

# ==========================================
# 터미널에서 바로 테스트해 볼 수 있는 실행 코드
# ==========================================
if __name__ == "__main__":
    print("=== 🌲 감정 일기 AI 분석 테스트 ===")
    sample_diary = "오늘 발표를 앞두고 심장이 터질 것 같이 불안했다. 하지만 막상 시작하니 준비한 대로 잘 해냈고, 팀원들이 고생했다고 말해줘서 뿌듯하고 기분이 좋았다."
    print(f"📝 유저가 작성한 일기:\n{sample_diary}\n")
    
    result = analyze_diary_emotion(sample_diary)
    
    if result:
        print("📊 [AI 분석 결과 (이 데이터가 DB에 저장됩니다)]")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ 분석에 실패했습니다.")