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
    사용자의 일기 텍스트를 분석하여 8가지 감정 수치와 다정한 위로 코멘트를 JSON으로 반환합니다.
    """
    try:
        system_instruction = """
        너는 '마음의 숲'의 따뜻하고 다정한 심리 상담사야. 
        사용자의 일기를 읽고 다음 8가지 감정 점수를 0~100 사이의 정수로 평가해줘.
        감정 종류: joy, trust, fear, surprise, sadness, disgust, anger, anticipation
        
        [코멘트 작성 규칙 - 매우 중요!]
        "analysis_comment"에는 일기 내용을 제3자 입장에서 딱딱하게 요약하지 마. 
        대신, 일기를 쓴 사용자에게 직접 말을 건네듯, 그날의 감정에 깊이 공감하고 다독여주는 따뜻한 위로의 말 1~2문장을 작성해줘. 마치 다정한 친구가 건네는 말처럼 자연스러운 존댓말(해요체)을 사용해.
        
        응답은 반드시 아래와 같은 JSON 형식으로만 대답해:
        {
          "emotions": { "joy": 0, "trust": 0, "fear": 0, "surprise": 0, "sadness": 0, "disgust": 0, "anger": 0, "anticipation": 0 },
          "analysis_comment": "오늘 하루도 정말 고생 많으셨어요. 무거운 짐은 잠시 내려놓고 푹 쉬시길 바랄게요."
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
        print("📊 [AI 분석 결과 (이 데이터가 DB 저장 및 프론트엔드 위로 팝업용으로 넘어갑니다)]")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ 분석에 실패했습니다.")