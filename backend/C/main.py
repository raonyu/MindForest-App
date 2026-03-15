from fastapi import FastAPI
from typing import List
import models  # 담당 B가 만든 DB 모델 연동

app = FastAPI()

# 9유형 진단 가중치 데이터 (아까 우리가 정한 20문항 로직)
# 예시로 몇 개만 넣었으니, 팀에서 정한 전체 로직을 이 형식대로 채우면 돼!
WEIGHTS = {
    1: {1: {"A": 1, "C": 1}, 2: {"H": 2, "B": 1}},
    2: {1: {"B": 2, "E": 1}, 2: {"D": 1, "I": 2}},
    3: {1: {"G": 2}, 2: {"F": 1, "A": 1}},
    # ... 20번 문항까지 같은 방식으로 추가
}

@app.post("/test/diagnose")
def diagnose_user(answers: List[int]):
    """
    사용자가 선택한 답변 리스트(예: [1, 2, 1, ...])를 받아
    가중치를 합산하여 최종 심리 유형을 반환합니다.
    """
    # 점수 초기화 (A~I 유형)
    scores = {k: 0 for k in "ABCDEFGHI"}
    
    # 답변 리스트를 돌면서 가중치 합산
    for i, ans in enumerate(answers):
        q_num = i + 1  # 문항 번호 (1부터 시작)
        if q_num in WEIGHTS and ans in WEIGHTS[q_num]:
            for type_key, weight in WEIGHTS[q_num][ans].items():
                scores[type_key] += weight
    
    # 가장 높은 점수를 받은 유형 결정
    final_type = max(scores, key=scores.get)
    
    # 유형별 캐릭터 매핑 (예시)
    characters = {
        "A": "움츠린 거북이",
        "H": "까칠한 햄스터",
        "I": "산만한 다람쥐"
    }
    
    return {
        "final_type": final_type,
        "character_name": characters.get(final_type, "미확인 유형"),
        "all_scores": scores,
        "message": "성격 유형 진단이 완료되었습니다."
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "담당 C 서버 정상 작동 중"}