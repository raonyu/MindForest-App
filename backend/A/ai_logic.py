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
    최근 데이터(리스트)를 역순으로 확인하여 '연속된 우울/분노' 일수를 계산하고,
    단계별 알림 메시지를 반환합니다.
    """
    if not recent_emotions_list:
        return {"level": "LOW", "message": "데이터가 없습니다."}

    consecutive_bad_days = 0
    
    # 가장 최근(오늘) 데이터부터 과거로 거슬러 올라가며 연속성 확인
    for data in reversed(recent_emotions_list):
        emotions = data.get("emotions", {})
        sadness = emotions.get("sadness", 0)
        anger = emotions.get("anger", 0)
        
        # 우울하거나 화나는 수치가 70 이상이면 카운트 증가
        if sadness >= 70 or anger >= 70:
            consecutive_bad_days += 1
        else:
            # 연속이 끊기면 바로 계산 종료
            break

    # 기획하신 '단계별 알림' 로직 적용
    if consecutive_bad_days >= 7:
        return {
            "level": "HIGH", 
            "message": "일주일간 마음이 많이 힘드셨네요. 혼자 앓지 말고, 전문 상담 센터(링크)를 확인해 보시겠어요?"
        }
    elif consecutive_bad_days >= 3:
        return {
            "level": "MEDIUM", 
            "message": "오늘 기분은 좀 어떠신가요? 마음을 환기할 수 있는 가벼운 산책을 추천해요."
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

    # 단순하지만 그럴싸한(MVP용) 리포트 생성 로직
    if total_sadness > total_joy * 1.5:
        return "이번 주는 마음속에 비가 오는 날이 많았네요. 다음 주는 조금 더 맑게 갤 거예요."
    elif total_joy > total_sadness * 1.5:
        return "이번 주는 햇살이 가득한 한 주였네요! 이 긍정적인 에너지를 계속 이어가 볼까요?"
    else:
        return "이번 주는 여러 감정이 교차하는 다채로운 한 주였네요. 수고 많으셨습니다."

# --- 테스트 구역 ---
if __name__ == "__main__":
    print("=== 1. 알림 단계화 테스트 (3일 연속 우울) ===")
    mock_3_days = [
        {"emotions": {"sadness": 75, "anger": 10}}, # 엊그제
        {"emotions": {"sadness": 80, "anger": 20}}, # 어제
        {"emotions": {"sadness": 85, "anger": 10}}  # 오늘
    ]
    alert_result = check_anomaly_level(mock_3_days)
    print(f"경고 레벨: {alert_result['level']}")
    print(f"알림 메시지: {alert_result['message']}\n")

    print("=== 2. 주간 리포트 테스트 (7일치 데이터) ===")
    mock_7_days = [
        {"emotions": {"sadness": 80, "joy": 10}}, # 월
        {"emotions": {"sadness": 90, "joy": 0}},  # 화
        {"emotions": {"sadness": 70, "joy": 20}}, # 수
        {"emotions": {"sadness": 75, "joy": 10}}, # 목
        {"emotions": {"sadness": 85, "joy": 5}},  # 금
        {"emotions": {"sadness": 80, "joy": 10}}, # 토
        {"emotions": {"sadness": 90, "joy": 0}},  # 일
    ]
    # 7일 연속 우울 알림 확인
    weekly_alert = check_anomaly_level(mock_7_days)
    print(f"7일 경고 레벨: {weekly_alert['level']}")
    print(f"7일 알림 메시지: {weekly_alert['message']}")
    
    # 주간 리포트 코멘트 확인
    report_msg = generate_weekly_report(mock_7_days)
    print(f"주간 리포트 코멘트: {report_msg}")