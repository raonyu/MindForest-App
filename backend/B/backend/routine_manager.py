import models
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
import random

ROUTINE_CATEGORY_MAP = {
    "DEPRESSION": ["활동형", "기록형", "휴식형"],
    "BIPOLAR": ["휴식형", "기록형", "몰입형"],
    "ANXIETY": ["휴식형", "몰입형", "환경조성형"],
    "SCHIZOPHRENIA": ["몰입형", "휴식형", "기록형"],
    "PTSD": ["휴식형", "환경조성형", "몰입형"],
    "OCD": ["환경조성형", "휴식형", "몰입형"],
    "ADHD": ["활동형", "몰입형", "환경조성형"],
    "EATING_DISORDER": ["휴식형", "기록형", "자기계발형"],
    "ANGER": ["활동형", "휴식형", "기록형"],
}

ALL_ROUTINE_CATEGORIES = ["활동형", "몰입형", "기록형", "휴식형", "자기계발형", "환경조성형"]

ROUTINE_MASTER = {
    "활동형": {
        1: ["기지개 켜고 전신 스트레칭 2분", "실내에서 제자리 걷기 5분"],
        2: ["동네 가볍게 산책하기 20분", "정자세 스쿼트 20개 수행하기"],
        3: ["야외 조깅 30분", "가까운 뒷산 등산 1시간"],
    },
    "몰입형": {
        1: ["좋아하는 음악 2곡 가사에 집중하며 듣기", "창밖 풍경 5분간 가만히 바라보기"],
        2: ["영화 1편 끝까지 집중해서 감상하기", "관심 분야 다큐멘터리 1편 시청"],
        3: ["종이책 30페이지 읽고 기억나는 문구 적기", "악기 연습 또는 새로운 곡 연주 40분"],
    },
    "기록형": {
        1: ["오늘 찍은 사진 중 가장 맘에 드는 1장 고르기", "현재 내 기분을 단어 하나로 메모하기"],
        2: ["오늘 하루 감사했던 일 3가지 구체적으로 적기", "오늘 먹은 식단과 지출 내역 기록하기"],
        3: ["좋아하는 책 문장 1페이지 정성껏 필사하기", "이번 주 나에게 일어난 변화와 감정 회고록 쓰기"],
    },
    "휴식형": {
        1: ["미지근한 물 1잔 천천히 음미하며 마시기", "눈 감고 편안하게 심호흡 10번 하기"],
        2: ["알람 맞추고 짧고 깊게 낮잠 20분 자기", "가장 좋아하는 디저트나 간식 하나 기분 좋게 먹기"],
        3: ["가이드 영상 보며 명상 20분 수행하기", "스마트폰 전원 끄고 디지털 디톡스 1시간 하기"],
    },
    "자기계발형": {
        1: ["새로운 외국어 단어 5개 암기하기", "오늘의 주요 뉴스 헤드라인 3개 읽기"],
        2: ["관심 분야 온라인 강의 1개 시청하기", "경제 또는 시사 기사 1개 읽고 요약하기"],
        3: ["자격증 문제집 5페이지 집중해서 풀기", "외국어 회화 앱으로 20분간 대화 연습하기"],
    },
    "환경조성형": {
        1: ["책상 위 쓰레기 버리고 물티슈로 닦기", "창문 모두 열고 10분간 시원하게 환기하기"],
        2: ["쌓여 있는 설거지 바로 끝내기", "세탁기 돌리고 다 된 빨래 건조대에 널기"],
        3: ["나를 위해 정성 들여 직접 밥 만들어 먹기", "옷장 정리하며 안 입는 옷 과감히 분류하기"],
    },
}

class RoutineManager:
    def _get_lifestyle_categories(self, category: str):
        clean_category = (category or "").strip().upper()
        return ROUTINE_CATEGORY_MAP.get(clean_category, ALL_ROUTINE_CATEGORIES[:3])

    def initialize_user_routine(self, db: Session, user_id: str, category: str):
        """
        사용자가 온보딩을 마쳤을 때, 질병 유형에 맞는 C 파트 생활양식 루틴 3개를 할당합니다.
        """
        lifestyle_categories = self._get_lifestyle_categories(category)
        
        available_routines = db.query(models.RoutineMaster).filter(
            models.RoutineMaster.category.in_(lifestyle_categories)
        ).all()

        if not available_routines:
            print(f"⚠️ [ROUTINE] '{category}'에 매핑된 C 루틴 마스터 데이터가 없습니다.")
            return

        selected = []
        for lifestyle_category in lifestyle_categories:
            category_routines = [r for r in available_routines if r.category == lifestyle_category]
            if category_routines:
                selected.append(random.choice(category_routines))

        if len(selected) < 3:
            remaining = [r for r in available_routines if r.id not in {selected_r.id for selected_r in selected}]
            selected.extend(random.sample(remaining, min(len(remaining), 3 - len(selected))))
        
        for r in selected:
            exists = db.query(models.UserRoutine).filter(
                models.UserRoutine.user_id == user_id,
                models.UserRoutine.routine_id == r.id,
                models.UserRoutine.date == date.today()
            ).first()
            
            if not exists:
                new_user_routine = models.UserRoutine(
                    user_id=user_id,
                    routine_id=r.id,
                    date=date.today(),
                    is_completed=False
                )
                db.add(new_user_routine)
        
        try:
            db.commit()
            print(f"✅ {user_id}님에게 루틴 {len(selected)}개 할당 완료")
        except Exception as e:
            db.rollback()
            print(f"❌ 루틴 저장 오류: {e}")

    def get_daily_recommendations(self, db: Session, user_id: str):
        return db.query(models.UserRoutine).filter(
            models.UserRoutine.user_id == user_id,
            models.UserRoutine.date == date.today()
        ).all()

    def get_recommended_routines(self, user_data_or_user):
        """
        C 파트의 생활양식 루틴 추천 규칙을 B 메인 서버 안에서 제공합니다.
        """
        if not hasattr(user_data_or_user, "created_at"):
            selected_categories = random.sample(ALL_ROUTINE_CATEGORIES, 3)
            return self._pick_routine_contents_from_categories(selected_categories, max_level=2)

        user = user_data_or_user
        today = datetime.now(timezone.utc).date()
        signup_date = user.created_at.date()
        days_passed = (today - signup_date).days

        if days_passed <= 7:
            selected_categories = random.sample(ALL_ROUTINE_CATEGORIES, 3)
            return self._pick_routine_contents_from_categories(selected_categories, max_level=2)

        category_stats = {cat: {"count": 0, "score": 0.0} for cat in ALL_ROUTINE_CATEGORIES}
        for diary in user.diaries:
            cat = diary.routine_category
            if cat in category_stats:
                category_stats[cat]["count"] += 1
                category_stats[cat]["score"] += diary.score_diff or 0.0

        sorted_categories = sorted(
            ALL_ROUTINE_CATEGORIES,
            key=lambda cat: category_stats[cat]["score"],
            reverse=True,
        )
        active_categories = [cat for cat in sorted_categories if category_stats[cat]["score"] > 0]
        final_categories = active_categories if active_categories else ALL_ROUTINE_CATEGORIES
        explore_category = min(ALL_ROUTINE_CATEGORIES, key=lambda cat: category_stats[cat]["count"])

        selected_categories = [final_categories[0]]
        selected_categories.append(final_categories[1] if len(final_categories) > 1 else final_categories[0])
        selected_categories.append(explore_category)

        return self._pick_routine_contents_from_categories(selected_categories)

    def _pick_routine_contents_from_categories(self, categories, max_level=None):
        result = []
        for category in categories:
            levels = ROUTINE_MASTER.get(category, {})
            level_keys = [level for level in levels if max_level is None or level <= max_level]
            candidates = [routine for level in level_keys for routine in levels[level]]
            if candidates:
                result.append(random.choice(candidates))

        if len(result) < 3:
            fallback = [
                routine
                for levels in ROUTINE_MASTER.values()
                for routines in levels.values()
                for routine in routines
            ]
            result.extend([item for item in fallback if item not in result][:3 - len(result)])

        return result[:3]

    def analyze_routine_logs(self, logs: list):
        """
        루틴 수행 이력을 분석하여 결과를 반환합니다.
        """
        completed = sum(1 for l in logs if l.get("is_completed"))
        total = len(logs)
        return {
            "total_completed": completed,
            "total_assigned": total,
            "status": "success"
        }

routine_manager = RoutineManager()

# 모듈 단위 함수 노출
def get_recommended_routines(user_data_or_user):
    return routine_manager.get_recommended_routines(user_data_or_user)

def analyze_routine_logs(logs):
    return routine_manager.analyze_routine_logs(logs)
