import models
from sqlalchemy.orm import Session
from datetime import date
import random

class RoutineManager:
    def initialize_user_routine(self, db: Session, user_id: str, category: str):
        """
        사용자가 온보딩을 마쳤을 때, 해당 카테고리의 루틴 3개를 할당합니다.
        (레벨 제한을 제거하여 1, 2, 3단계를 모두 가져오게 수정)
        """
        clean_category = category.strip().upper()
        
        # [수정] level == 1 조건을 제거하여 해당 카테고리의 모든 루틴(보통 3개)을 가져옵니다.
        available_routines = db.query(models.RoutineMaster).filter(
            models.RoutineMaster.category == clean_category
        ).all()

        if not available_routines:
            print(f"⚠️ [ROUTINE] '{clean_category}' 카테고리에 마스터 데이터가 없습니다.")
            return

        # 랜덤하게 3개를 선택 (데이터가 3개라면 3개 모두 선택됨)
        selected = random.sample(available_routines, min(len(available_routines), 3))
        
        for r in selected:
            # 이미 오늘 할당된 동일한 루틴이 있는지 체크 (중복 방지)
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

routine_manager = RoutineManager()