import json
import os
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def _get_client() -> OpenAI:
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), timeout=10.0)


def run_bws_llm(text: str, candidate_emotions: dict[str, int]) -> dict[str, Any] | None:
    """
    상위 경합 감정들을 받아 LLM에게 Best/Worst를 가리게 하는 함수.
    candidate_emotions: 예) {"sadness": 78, "anger": 76}
    """
    emotion_names = list(candidate_emotions.keys())
    if len(emotion_names) < 2:
        return None

    prompt = f"""당신은 심리학 기반의 감정 분석 검증 AI입니다.
아래 일기 텍스트를 읽고, 1차 모델이 추출한 경합 후보 감정들 중에서 문맥상 가장 지배적인 핵심 감정(Best)과 가장 거리가 먼 감정(Worst)을 판별해주세요.

일기 텍스트: "{text}"
후보 감정 및 1차 점수: {json.dumps(candidate_emotions, ensure_ascii=False)}

반드시 후보 감정에 제시된 '영어 단어'({emotion_names})만 그대로 사용하여 아래 JSON 형식으로만 응답하세요.
{{
  "best_emotion": "후보 중 1개 (반드시 영어)",
  "worst_emotion": "후보 중 1개 (반드시 영어)",
  "reasoning": "사용자의 상황에 공감하며 해당 감정을 선택한 이유를 부드러운 해요체로 짧게 1문장 작성"
}}"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            return None

        result = json.loads(content)

        # 후보 리스트에 없는 단어거나 Best/Worst가 동일하면 무효 처리
        best = result.get("best_emotion")
        worst = result.get("worst_emotion")

        if best not in emotion_names:
            result["best_emotion"] = emotion_names[0]
        if worst not in emotion_names or worst == result["best_emotion"]:
            result["worst_emotion"] = emotion_names[-1]

        # 주간 리포트 BwsRecord 저장을 위해 후보 목록을 함께 담아 반환
        result["candidates"] = emotion_names
        return result

    except Exception as e:
        print(f"[경고] BWS LLM 호출 실패 (1차 모델 결과로 폴백합니다): {e}")
        return None