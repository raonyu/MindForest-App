import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# 환경변수 로드 및 OpenAI 클라이언트 설정
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# [1] 고정된 온보딩 20문항 데이터 (절대 수정/삭제하지 마세요)
ONBOARDING_QUESTIONS = [
    {"title": "1. 아침에 눈을 떴을 때, 오늘 하루의 일정이 꽉 차 있다면?", "detail": ["벌써 기가 빨려...", "시간 단위로 쪼개야 해!", "일단 부딪혀!"]},
    {"title": "2. 기분이 갑자기 롤러코스터처럼 오르락내리락할 때 나는?", "detail": ["나도 내 마음을 몰라 혼란스럽다.", "겉으로는 참지만 속으론 심장이 뛴다.", "주변에 날카롭게 반응한다."]},
    {"title": "3. 예상치 못한 실수로 일을 망쳤을 때 나의 반응은?", "detail": ["내내 자책하며 땅굴을 판다.", "어디서 틀렸는지 계속 복기한다.", "순간 욱하지만 금방 잊는다."]},
    {"title": "4. 나에게 '진정한 휴식'이란 어떤 의미일까?", "detail": ["아무도 없는 곳에서 가만히 누워 있기", "방 청소를 완벽하게 끝낸 평온함", "유튜브나 재밌는 걸 발견하는 것"]},
    {"title": "5. 슬프거나 우울한 감정이 찾아오면 나는?", "detail": ["나만의 동굴로 깊이 숨어버린다.", "기분 전환을 위해 평소 안 하던 행동을 한다.", "상처받을까 봐 철저히 숨긴다."]},
    {"title": "6. 친한 친구가 갑자기 약속을 취소했다. 내 머릿속은?", "detail": ["내가 뭐 잘못했나? 걱정한다.", "순간 화가 치밀어 오른다.", "혼자만의 시간이 생겨 은근 다행이다."]},
    {"title": "7. 사람들이 많이 모인 시끄럽고 낯선 장소에 가면?", "detail": ["기가 빨려서 집에 갈 생각만 한다.", "사람들 눈치를 보며 불안해한다.", "분위기에 휩쓸려 감정이 널뛴다."]},
    {"title": "8. 누군가 나에게 칭찬을 해줄 때 나의 속마음은?", "detail": ["진심일까? 의심부터 든다.", "내 기준엔 부족해서 기쁘지 않다.", "텐션이 확 올라간다."]},
    {"title": "9. 다른 사람에게 내 속마음을 이야기해야 할 때 나는?", "detail": ["약점이 될까 봐 적당히 포장한다.", "감정이 앞서 말이 쏟아져 나온다.", "머릿속으로 수십 번 시뮬레이션한다."]},
    {"title": "10. 대화 중에 내가 관심 없는 주제가 나오면?", "detail": ["나도 모르게 멍을 때린다.", "억지로 리액션하며 에너지를 소모한다.", "분위기를 망칠까 봐 눈치를 본다."]},
    {"title": "11. 중요한 시험이나 프로젝트를 앞둔 나의 모습은?", "detail": ["실패할까 봐 극도로 초조하다.", "계획표를 완벽하게 세워야 시작한다.", "딴생각이 들고 자꾸 휴대폰을 본다."]},
    {"title": "12. 일이 내 뜻대로, 내 계획대로 풀리지 않으면?", "detail": ["스트레스를 받고 계획에 집착한다.", "참을 수 없는 짜증이 밀려온다.", "순식간에 의욕을 잃고 놔버린다."]},
    {"title": "13. 무언가에 집중하고 있을 때 누가 말을 걸면?", "detail": ["날카롭게 반응한다.", "깜짝 놀라며 상대의 눈치를 본다.", "금방 대화에 빠져 하던 일을 까먹는다."]},
    {"title": "14. 해야 할 일이 산더미일 때 나의 대처법은?", "detail": ["압박감에 회피하고 미룬다.", "리스트를 지워가는 쾌감을 느낀다.", "이것저것 손대다 제대로 끝내지 못한다."]},
    {"title": "15. 밤에 자려고 누웠을 때 내 머릿속은?", "detail": ["과거의 상처나 부끄러운 일이 떠오른다.", "최악의 상황을 상상하며 뒤척인다.", "감정 기복이 심해진다."]},
    {"title": "16. 나를 가장 힘들게 하는 것은 무엇일까?", "detail": ["불확실한 상황", "상처받고 버림받을지 모른다는 두려움", "주체할 수 없는 내 안의 감정"]},
    {"title": "17. 화가 났을 때 나를 진정시키는 방법은?", "detail": ["확실한 분출구가 필요하다.", "혼자만의 방어막 안으로 숨는다.", "새로운 자극으로 환기한다."]},
    {"title": "18. 내가 바라는 나의 모습은 어떤 사람일까?", "detail": ["평온하고 단단한 사람", "사람들과 편하게 어울리는 사람", "걱정 없이 세상을 즐기는 사람"]},
    {"title": "19. 마음이 지쳤을 때 누군가 나에게 해줬으면 하는 말은?", "detail": ["완벽하지 않아도 괜찮아.", "아무것도 안 해도 돼. 푹 쉬어.", "네 마음 다 알아. 옆에 있을게."]},
    {"title": "20. 마음의 숲에서 내가 찾고 싶은 장소는 어디일까?", "detail": ["안전한 오두막", "정돈된 깔끔한 정원", "모험이 가득한 숲"]}
]

CATEGORIES = [
    "DEPRESSION",
    "BIPOLAR",
    "ANXIETY",
    "SCHIZOPHRENIA",
    "PTSD",
    "OCD",
    "ADHD",
    "EATING_DISORDER",
    "ANGER",
]

ONBOARDING_SCORE_MAP = [
    [
        {"DEPRESSION": 2, "ANXIETY": 1},
        {"OCD": 2, "ANXIETY": 1},
        {"ADHD": 2, "BIPOLAR": 1},
    ],
    [
        {"BIPOLAR": 2, "ANXIETY": 1},
        {"ANXIETY": 2, "PTSD": 1},
        {"ANGER": 2, "BIPOLAR": 1},
    ],
    [
        {"DEPRESSION": 2, "PTSD": 1},
        {"OCD": 2, "ANXIETY": 1},
        {"ANGER": 2, "ADHD": 1},
    ],
    [
        {"PTSD": 2, "DEPRESSION": 1},
        {"OCD": 2, "EATING_DISORDER": 1},
        {"ADHD": 2, "BIPOLAR": 1},
    ],
    [
        {"DEPRESSION": 2, "EATING_DISORDER": 1},
        {"BIPOLAR": 2, "ADHD": 1},
        {"PTSD": 2, "ANXIETY": 1},
    ],
    [
        {"ANXIETY": 2, "PTSD": 1},
        {"ANGER": 2, "BIPOLAR": 1},
        {"DEPRESSION": 2, "EATING_DISORDER": 1},
    ],
    [
        {"DEPRESSION": 2, "ANXIETY": 1},
        {"ANXIETY": 2, "SCHIZOPHRENIA": 1},
        {"BIPOLAR": 2, "ADHD": 1},
    ],
    [
        {"SCHIZOPHRENIA": 2, "ANXIETY": 1},
        {"EATING_DISORDER": 2, "OCD": 1},
        {"BIPOLAR": 2, "ADHD": 1},
    ],
    [
        {"PTSD": 2, "SCHIZOPHRENIA": 1},
        {"BIPOLAR": 2, "ADHD": 1},
        {"ANXIETY": 2, "OCD": 1},
    ],
    [
        {"ADHD": 2, "DEPRESSION": 1},
        {"EATING_DISORDER": 2, "DEPRESSION": 1},
        {"SCHIZOPHRENIA": 2, "ANXIETY": 1},
    ],
    [
        {"ANXIETY": 2, "PTSD": 1},
        {"OCD": 2, "ANXIETY": 1},
        {"ADHD": 2, "BIPOLAR": 1},
    ],
    [
        {"OCD": 2, "ANXIETY": 1},
        {"ANGER": 2, "BIPOLAR": 1},
        {"DEPRESSION": 2, "ADHD": 1},
    ],
    [
        {"ANGER": 2, "OCD": 1},
        {"PTSD": 2, "ANXIETY": 1},
        {"ADHD": 2, "BIPOLAR": 1},
    ],
    [
        {"ANXIETY": 2, "DEPRESSION": 1},
        {"OCD": 2, "EATING_DISORDER": 1},
        {"ADHD": 2, "BIPOLAR": 1},
    ],
    [
        {"PTSD": 2, "DEPRESSION": 1},
        {"ANXIETY": 2, "SCHIZOPHRENIA": 1},
        {"BIPOLAR": 2, "ANGER": 1},
    ],
    [
        {"SCHIZOPHRENIA": 2, "ANXIETY": 1},
        {"PTSD": 2, "DEPRESSION": 1},
        {"BIPOLAR": 2, "ANGER": 1},
    ],
    [
        {"ANGER": 2, "BIPOLAR": 1},
        {"SCHIZOPHRENIA": 2, "PTSD": 1},
        {"EATING_DISORDER": 2, "ADHD": 1},
    ],
    [
        {"DEPRESSION": 2, "ANXIETY": 1},
        {"SCHIZOPHRENIA": 2, "PTSD": 1},
        {"ADHD": 2, "BIPOLAR": 1},
    ],
    [
        {"EATING_DISORDER": 2, "OCD": 1},
        {"DEPRESSION": 2, "EATING_DISORDER": 1},
        {"PTSD": 2, "SCHIZOPHRENIA": 1},
    ],
    [
        {"PTSD": 2, "ANXIETY": 1},
        {"OCD": 2, "EATING_DISORDER": 1},
        {"ADHD": 2, "BIPOLAR": 1},
    ],
]

CATEGORY_REASON_LABELS = {
    "DEPRESSION": "지친 마음을 조용히 쉬게 하고 싶은 신호가 많이 보여요.",
    "BIPOLAR": "감정의 움직임이 크고 순간의 에너지가 선명하게 드러나요.",
    "ANXIETY": "불확실한 상황에서 긴장과 걱정이 먼저 올라오는 편이에요.",
    "SCHIZOPHRENIA": "혼자만의 안전한 세계와 섬세한 거리감이 중요해 보여요.",
    "PTSD": "상처받지 않기 위해 스스로를 보호하려는 마음이 강하게 보여요.",
    "OCD": "정돈감과 예측 가능한 흐름에서 안정감을 찾는 편이에요.",
    "ADHD": "새로운 자극과 빠른 전환에 민감하게 반응하는 에너지가 있어요.",
    "EATING_DISORDER": "허전함을 채우고 스스로를 다독이고 싶은 마음이 보여요.",
    "ANGER": "답답함이나 침범당한 느낌에 빠르게 반응하는 경향이 보여요.",
}

ANSWER_TO_INDEX = {
    option: option_idx
    for question in ONBOARDING_QUESTIONS
    for option_idx, option in enumerate(question["detail"])
}


def _extract_onboarding_answers(chat_history, current_message=None):
    valid_answers = set(ANSWER_TO_INDEX.keys())
    answers = [
        str(h.get("content", "")).strip()
        for h in chat_history
        if h.get("role") == "user" and str(h.get("content", "")).strip() in valid_answers
    ]

    current = str(current_message or "").strip()
    if current in valid_answers:
        answers.append(current)

    return answers[:len(ONBOARDING_QUESTIONS)]


def _calculate_max_scores():
    max_scores = {category: 0 for category in CATEGORIES}
    for question_scores in ONBOARDING_SCORE_MAP:
        for category in CATEGORIES:
            max_scores[category] += max(option_scores.get(category, 0) for option_scores in question_scores)
    return max_scores


MAX_POSSIBLE_SCORES = _calculate_max_scores()


def analyze_onboarding_answers(answers):
    scores = {category: 0 for category in CATEGORIES}
    primary_hits = {category: 0 for category in CATEGORIES}

    for question_idx, answer in enumerate(answers[:len(ONBOARDING_QUESTIONS)]):
        options = ONBOARDING_QUESTIONS[question_idx]["detail"]
        if answer not in options:
            continue

        option_idx = options.index(answer)
        option_scores = ONBOARDING_SCORE_MAP[question_idx][option_idx]
        for category, point in option_scores.items():
            scores[category] += point
            if point == 2:
                primary_hits[category] += 1

    normalized_scores = {
        category: scores[category] / MAX_POSSIBLE_SCORES[category]
        if MAX_POSSIBLE_SCORES[category] else 0
        for category in CATEGORIES
    }

    selected_category = max(
        CATEGORIES,
        key=lambda category: (
            normalized_scores[category],
            scores[category],
            primary_hits[category],
        ),
    )

    sorted_categories = sorted(
        CATEGORIES,
        key=lambda category: normalized_scores[category],
        reverse=True,
    )
    second_category = sorted_categories[1] if len(sorted_categories) > 1 else selected_category

    return {
        "is_finished": True,
        "category": selected_category,
        "reason": (
            f"{CATEGORY_REASON_LABELS[selected_category]} "
            f"또한 {CATEGORY_REASON_LABELS[second_category]}"
        ),
        "scores": scores,
        "ratios": {
            category: round(normalized_scores[category] * 100, 1)
            for category in CATEGORIES
        },
    }


def get_chat_response(user_message, chat_history=None, is_onboarding_done=False, user_animal="", signup_date=None):
    """
    마음의 숲 챗봇 엔진
    - Onboarding: 정해진 20문항을 순차적으로 제공
    - Analysis: 20문항 답변 완료 시 GPT가 질환 카테고리 분석
    - Consultation: 온보딩 완료 후 개인화된 상담 제공
    """
    if chat_history is None:
        chat_history = []

    # [1] 온보딩 모드 (20문항 테스트 진행 중)
    if not is_onboarding_done:
        # 실제 선택지로 들어온 답변만 추출해서 시작 메시지를 답변으로 세지 않게 합니다.
        user_answers = _extract_onboarding_answers(chat_history, user_message)
        q_idx = len(user_answers)

        # 아직 20문항을 다 완료하지 않은 경우: 질문 리스트에서 다음 질문을 반환
        if q_idx < len(ONBOARDING_QUESTIONS):
            question = ONBOARDING_QUESTIONS[q_idx]
            return {
                "type": "select",
                "title": f"({q_idx + 1}/20) {question['title']}",
                "detail": question["detail"],
                "is_finished": False
            }
        
        # 20문항 답변이 모두 완료된 경우: 고정 점수표와 기회 대비 비율로 카테고리 분석
        else:
            return analyze_onboarding_answers(user_answers)

    # [2] 상담 모드 (온보딩 완료 후 일반 상담)
    else:
        # 가입 기간 계산
        days_since_signup = 0
        if signup_date:
            # signup_date가 datetime 객체라고 가정
            delta = datetime.now(signup_date.tzinfo) - signup_date
            days_since_signup = delta.days

        system_prompt = f"""
        너는 '마음의 숲'의 다정한 상담사야. 
        사용자는 현재 [{user_animal}] 유형으로 진단받았어.
        
        [정보]
        - 사용자가 우리 숲에 머문 지 {days_since_signup}일째야.
        - 사용자의 유형에 맞춰 따뜻하게 공감하고 격려해줘.
        - 대화 중간에 오늘의 기분이나 마음 온도를 물어봐줘.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": user_message}],
                temperature=0.7
            )
            return {
                "is_finished": False, 
                "reply_message": response.choices[0].message.content.strip()
            }
        except Exception as e:
            print(f"상담 GPT 에러: {e}")
            return {
                "is_finished": False, 
                "reply_message": "잠시 숲이 조용하네요. 다시 말을 걸어주시겠어요?"
            }
