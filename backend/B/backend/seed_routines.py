from database import SessionLocal
import models

def seed_routines():
    db = SessionLocal()

    # AI 카테고리(영문)와 매칭하기 위해 한글명을 영문 키로 변환하여 정의합니다.
    # [질환 키, 난이도, 루틴 내용]
    routines_data = [
        # 1. 우울증 (DEPRESSION)
        ("DEPRESSION", 1, "햇볕 쬐며 10분 산책하기"),
        ("DEPRESSION", 2, "작은 성취 기록하기: '물 마시기', '이불 개기' 등 아주 사소한 일을 완료하고 체크합니다."),
        ("DEPRESSION", 3, "감사 세 줄 일기: 뇌가 긍정적인 정보에 주목을 받도록 훈련합니다."),

        # 2. 불안증 (ANXIETY)
        ("ANXIETY", 1, "4, 7, 8 호흡법: 4초간 숨 들이마시고, 7초 멈추고, 8초 내뱉으며 부교감 신경을 활성화합니다."),
        ("ANXIETY", 2, "5, 4, 3, 2, 1 접지법: 보이는 것 5개, 들리는 것 4개, 느껴지는 것 3개, 냄새 2개, 맛 1개에 집중합니다."),
        ("ANXIETY", 3, "걱정 시간 정하기: 하루 중 딱 15분만 걱정하는 시간으로 정하고 그 외에는 걱정 미루는 연습을 합니다."),

        # 3. ADHD
        ("ADHD", 1, "포모도로 타이머: 25분 집중, 5분 휴식 패턴을 반복하여 수행합니다."),
        ("ADHD", 2, "도착지 시각화: 할 일을 하기 전, 완성된 모습을 머릿속으로 그려봅니다."),
        ("ADHD", 3, "원터치 정리: 자주 쓰는 물건은 무조건 정해진 위치 한 곳에만 둡니다."),

        # 4. 조울증 (BIPOLAR)
        ("BIPOLAR", 1, "수면 위생 철저: 매일 같은 시간에 자고 깨는 것이 기분 조절 핵심입니다."),
        ("BIPOLAR", 2, "기분 도표 기록: 매일의 에너지를 기록하여 삽화가 오기 전 전조증상을 파악합니다."),
        ("BIPOLAR", 3, "신경계를 자극하거나 억제하는 물질을 멀리하여 평형 상태를 유지합니다."),

        # 5. 강박증 (OCD)
        ("OCD", 1, "확인 지연하기: 가스 불 확인 등 강박 행동을 하고 싶을 때 5분만 참고 다른 행동을 합니다."),
        ("OCD", 2, "불완전함 연습: 책상 위 펜 하나를 삐딱하게 두는 등 완벽하지 않은 상태를 유지합니다."),
        ("OCD", 3, "반복적인 강박 사고를 떠올리면서 생각이 드는 강박 행동을 의도적으로 참아봅니다."),

        # 6. PTSD (외상 후 스트레스 장애)
        ("PTSD", 1, "안전 지대 이미지 만들기: 가장 편안했던 장소를 떠올리거나 향기나 물건을 곁에 둡니다."),
        ("PTSD", 2, "근육 이완 요법: 발가락부터 머리까지 힘을 꽉 주었다 풀며, 현재 자신의 몸에 대한 감각을 느낍니다."),
        ("PTSD", 3, "긍정적 자기 암시: '나는 안전하다', '예전의 일은 끝났어.' 등 소리 내어 말합니다."),

        # 7. 섭식 장애 (EATING_DISORDER)
        ("EATING_DISORDER", 1, "마인드풀 이팅: 음식의 색, 향, 식감을 충분히 음미하며 먹습니다."),
        ("EATING_DISORDER", 2, "식사 일지 작성: 본인이 먹은 음식, 양, 시간, 먹을 때의 감정을 작성합니다."),
        ("EATING_DISORDER", 3, "식사 후 30분 ~ 1시간 산책 루틴을 수행합니다."),

        # 8. 조현병 (SCHIZOPHRENIA)
        ("SCHIZOPHRENIA", 1, "약 복용 루틴: 정해진 장소, 시간에 맞춰서 약을 복용합니다."),
        ("SCHIZOPHRENIA", 2, "규칙적인 대화: 하루에 한 번 신뢰할 수 있는 사람과 일상적인 대화를 나눕니다."),
        ("SCHIZOPHRENIA", 3, "현실 확인: 혼란스러울 때 주변 사물을 만지거나, 이름을 부르며 현실을 확인합니다."),

        # 9. 분노조절장애 (ANGER)
        ("ANGER", 1, "타임 아웃: 그 장소를 즉시 벗어나 10분간 혼자 있습니다."),
        ("ANGER", 2, "찬물 세수: 급격히 올라온 열감을 식히고 감각을 환기합니다."),
        ("ANGER", 3, "'나' 전달법: '나는 ~해서 속상해'라고 본인의 감정을 상대방에게 전달합니다.")
    ]

    try:
        for cat, lvl, txt in routines_data:
            # 중복 데이터 삽입 방지 (카테고리와 내용이 같은 게 있는지 확인)
            exists = db.query(models.RoutineMaster).filter(
                models.RoutineMaster.category == cat,
                models.RoutineMaster.content == txt
            ).first()

            if not exists:
                new_routine = models.RoutineMaster(
                    category=cat,
                    level=lvl,
                    content=txt
                )
                db.add(new_routine)
        
        db.commit()
        print("🌱 [마음의 숲] 9대 질환별 27개 루틴 마스터 데이터 삽입 완료!")
    except Exception as e:
        db.rollback()
        print(f"❌ 데이터 삽입 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_routines()