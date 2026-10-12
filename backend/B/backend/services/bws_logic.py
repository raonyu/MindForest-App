import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_bws_llm(text, candidate_emotions):
    """
    상위 경합 감정들을 받아 LLM에게 Best/Worst를 가리게 하는 함수.
    candidate_emotions: 예) {"sadness": 78, "anger": 76}
    """
    emotion_names = list(candidate_emotions.keys())
    
    # 수정 포인트 1: "영어 단어 그대로" 뱉으라고 프롬프트 명확화
    prompt = f"""
당신은 감정 분석 검증 AI입니다.
아래 텍스트를 읽고, 후보 감정들 중에서 문맥상 가장 지배적인 감정(Best)과 가장 거리가 먼 감정(Worst)을 골라주세요.

텍스트: "{text}"
후보 감정: {emotion_names}

반드시 후보 감정에 제시된 '영어 단어'를 그대로 사용하여 아래 JSON 형식으로만 응답하세요.
{{
  "best_emotion": "후보 중 1개 (반드시 영어)",
  "worst_emotion": "후보 중 1개 (반드시 영어)",
  "reasoning": "선택한 이유 짧게 1문장"
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        
        # 수정 포인트 2: best뿐만 아니라 worst도 리스트에 없는 이상한 단어면 None 처리
        if result.get("best_emotion") not in emotion_names:
            result["best_emotion"] = None
            
        if result.get("worst_emotion") not in emotion_names:
            result["worst_emotion"] = None
            
        return result
        
    except Exception as e:
        print(f"🚨 BWS LLM 호출 에러: {e}")
        return {"best_emotion": None, "worst_emotion": None, "reasoning": "에러 발생"}