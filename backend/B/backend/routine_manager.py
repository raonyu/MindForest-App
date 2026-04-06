import pandas as pd
import datetime
import random

# 1. 루틴 데이터베이스 (6가지 유형 / 3단계 난이도)
ROUTINE_MASTER = {
    '활동형': {
        1: ['기지개 켜고 전신 스트레칭 2분', '실내에서 제자리 걷기 5분'],
        2: ['동네 가볍게 산책하기 20분', '정자세 스쿼트 20개 수행하기'],
        3: ['야외 조깅 30분', '가까운 뒷산 등산 1시간']
    },
    '몰입형': {
        1: ['좋아하는 음악 2곡 가사에 집중하며 듣기', '창밖 풍경 5분간 가만히 바라보기'],
        2: ['영화 1편 끝까지 집중해서 감상하기', '관심 분야 다큐멘터리 1편 시청'],
        3: ['종이책 30페이지 읽고 기억나는 문구 적기', '악기 연습 또는 새로운 곡 연주 40분']
    },
    '기록형': {
        1: ['오늘 찍은 사진 중 가장 맘에 드는 1장 고르기', '현재 내 기분을 단어 하나로 메모하기'],
        2: ['오늘 하루 감사했던 일 3가지 구체적으로 적기', '오늘 먹은 식단과 지출 내역 기록하기'],
        3: ['좋아하는 책 문장 1페이지 정성껏 필사하기', '이번 주 나에게 일어난 변화와 감정 회고록 쓰기']
    },
    '휴식형': {
        1: ['미지근한 물 1잔 천천히 음미하며 마시기', '눈 감고 편안하게 심호흡 10번 하기'],
        2: ['알람 맞추고 짧고 깊게 낮잠 20분 자기', '가장 좋아하는 디저트나 간식 하나 기분 좋게 먹기'],
        3: ['가이드 영상 보며 명상 20분 수행하기', '스마트폰 전원 끄고 디지털 디톡스 1시간 하기']
    },
    '자기계발형': {
        1: ['새로운 외국어 단어 5개 암기하기', '오늘의 주요 뉴스 헤드라인 3개 읽기'],
        2: ['관심 분야 온라인 강의 1개 시청하기', '경제 또는 시사 기사 1개 읽고 요약하기'],
        3: ['자격증 문제집 5페이지 집중해서 풀기', '외국어 회화 앱으로 20분간 대화 연습하기']
    },
    '환경조성형': {
        1: ['책상 위 쓰레기 버리고 물티슈로 닦기', '창문 모두 열고 10분간 시원하게 환기하기'],
        2: ['쌓여 있는 설거지 바로 끝내기', '세탁기 돌리고 다 된 빨래 건조대에 널기'],
        3: ['나를 위해 정성 들여 직접 밥 만들어 먹기', '옷장 정리하며 안 입는 옷 과감히 분류하기']
    }
}

def get_recommended_routines(user):
    """
    담당 B의 User 모델 객체를 직접 받아서 처리하도록 수정
    """
    today = datetime.datetime.now(datetime.timezone.utc).date()
    # B의 models.User.created_at 사용
    signup_date = user.created_at.date() 
    days_passed = (today - signup_date).days
    all_categories = list(ROUTINE_MASTER.keys())

    # --- [Step 1: 가입 초기 1주일] ---
    if days_passed <= 7:
        selected_cats = random.sample(all_categories, 3)
        return [random.choice(ROUTINE_MASTER[cat][random.choice([1, 2])]) for cat in selected_cats]

    # --- [Step 2: 데이터 기반 최적화] ---
    else:
        # B의 models.Diary 역참조(user.diaries) 사용
        logs = user.diaries 
        category_stats = {cat: {'count': 0, 'score': 0} for cat in all_categories}
        
        for log in logs:
            # B의 모델에 추가될 routine_category와 score_diff 사용
            cat = log.routine_category
            if cat in category_stats:
                category_stats[cat]['count'] += 1
                category_stats[cat]['score'] += (log.score_diff if log.score_diff else 0)

        sorted_cats = sorted(all_categories, key=lambda x: category_stats[x]['score'], reverse=True)
        active_cats = [cat for cat in sorted_cats if category_stats[cat]['score'] > 0]
        
        final_candidates = active_cats if active_cats else all_categories
        recommendations = []

        best_cat = final_candidates[0]
        recommendations.append(random.choice(ROUTINE_MASTER[best_cat][3]))

        if len(final_candidates) > 1:
            sub_cat = final_candidates[1]
            recommendations.append(random.choice(ROUTINE_MASTER[sub_cat][2]))
        else:
            recommendations.append(random.choice(ROUTINE_MASTER[best_cat][2]))

        # 탐색 로직 (가장 적게 수행한 카테고리)
        worst_cat = min(all_categories, key=lambda x: category_stats[x]['count'])
        if worst_cat in active_cats:
            recommendations.append(random.choice(ROUTINE_MASTER[worst_cat][1]))
        else:
            used = [best_cat]
            if len(final_candidates) > 1: used.append(sub_cat)
            remaining = [c for c in all_categories if c not in used]
            explore_cat = random.choice(remaining) if remaining else best_cat
            recommendations.append(random.choice(ROUTINE_MASTER[explore_cat][1]))

        return recommendations


# 3. 데이터 분석 및 성능 리포트 함수
def analyze_routine_logs(logs):
    if not logs:
        return {"status": "no_data"}
    
    df = pd.DataFrame(logs)
    total_count = len(df)
    completed_count = len(df[df['is_completed'] == True])
    completion_rate = (completed_count / total_count) * 100
    
    cat_scores = df.groupby('category')['score_diff'].mean().to_dict()
    best_cat = max(cat_scores, key=cat_scores.get)
    
    return {
        "completion_rate": round(completion_rate, 1),
        "best_category": best_cat,
        "score_summary": cat_scores
    }