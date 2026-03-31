import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 환경변수 로드 및 OpenAI 클라이언트 세팅
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_chat_response(user_message, chat_history=None, is_onboarding_done=False, user_animal=""):
    """
    마음의 숲 챗봇 메인 엔진
    - user_message: 사용자가 방금 입력한 메시지
    - chat_history: 과거 대화 내역 (리스트 형태)
    - is_onboarding_done: DB에서 가져온 테스트 완료 여부 (True/False)
    - user_animal: 완료된 사용자일 경우 동물 유형
    """
    
    if chat_history is None:
        chat_history = []

    # ----------------------------------------------------
    # 1. 상태에 따라 GPT에게 줄 '시스템 지시문(Prompt)' 설정
    # ----------------------------------------------------
    if not is_onboarding_done:
        # [사전 테스트 모드] - 20문항 대본 및 9대 질병군 매핑
        system_prompt = """
        너는 '마음의 숲' 앱의 다정한 심리 가이드, '귀를 쫑긋 세운 토끼'야.
        지금부터 [마음의 숲 사전 테스트 20문항]을 바탕으로 사용자의 내면 동물을 찾아주는 심리 테스트를 진행해.

        [진행 규칙 - 매우 중요!]
        1. 무조건 한 번에 '딱 한 개의 질문'만 해. (여러 개를 동시에 묻지 마)
        2. 질문을 던질 때는 3개의 선택지(①, ②, ③)를 함께 보여줘.
        3. 사용자가 대답하면, 따뜻하게 공감해 준 뒤 곧바로 다음 번호의 질문을 해.
        4. 사용자가 딴소리를 하면: "우리 하던 테스트가 있었죠? 이어서 진행할게요!"라며 중단되었던 질문을 던져.

        [마음의 숲 사전 테스트 20문항]
        (질문 내용은 사용자님이 작성하신 20문항을 그대로 유지합니다...)
        1. 아침에 눈을 떴을 때, 오늘 하루의 일정이 꽉 차 있다면? ...
        (중략: 2번~20번 질문 포함)

        [결과 판정 기준 : 9가지 동물 유형 및 카테고리 코드]
        분석을 마친 뒤 아래 9가지 중 하나를 반드시 골라야 해:
        - DEPRESSION: 조용히 움츠린 거북이
        - BIPOLAR: 알록달록 카멜레온
        - ANXIETY: 안절부절 미어캣
        - SCHIZOPHRENIA: 몽환적인 검은 고양이
        - PTSD: 상처를 방패 삼은 고슴도치
        - OCD: 정리대장 펭귄
        - ADHD: 산만한 꼬마 다람쥐
        - EATING_DISORDER: 마음을 채우는 판다
        - ANGER: 까칠한 햄스터

        [종료 규칙 - 매우 중요!]
        20번 질문까지 끝나면, 부연 설명 없이 오직 아래 JSON 형식만 반환해:
        {"is_finished": true, "category": "카테고리코드", "result_name": "동물이름"}
        예: {"is_finished": true, "category": "ADHD", "result_name": "산만한 꼬마 다람쥐"}
        """
    else:
        # [일상 상담 모드] - 동물 프로필 적용
        system_prompt = f"""
        너는 '마음의 숲'의 따뜻한 공감 상담사야. 
        사용자는 [{user_animal}] 유형 판정을 받은 사람이야.
        성향에 맞춰 일상 고민을 들어주고 다정하게 위로해 줘.
        """

    # ----------------------------------------------------
    # 2. 메시지 조립 및 API 호출
    # ----------------------------------------------------
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            response_format={ "type": "text" } # JSON과 텍스트 혼용을 위해 text로 유지
        )
        reply_content = response.choices[0].message.content.strip()
        
        # 테스트 종료 시 JSON 파싱 로직
        if '"is_finished": true' in reply_content:
            start_idx = reply_content.find('{')
            end_idx = reply_content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                return json.loads(reply_content[start_idx:end_idx])
            
        return {"is_finished": False, "reply_message": reply_content}

    except Exception as e:
        print(f"GPT API 에러: {e}")
        return None