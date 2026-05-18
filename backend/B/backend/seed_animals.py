from database import SessionLocal
import models

def seed_animals():
    db = SessionLocal()
    
    # 사용자님이 주신 정확한 데이터 리스트
    animal_list = [
        {"category": "DEPRESSION", "name": "조용히 움츠린 거북이", "emoji": "🐢", "description": "조금은 느려도 괜찮아요. 한 걸음씩 숲을 산책해봐요."},
        {"category": "ANXIETY", "name": "안절부절 미어캣", "emoji": "🦦", "description": "주변을 살피느라 지쳤나요? 이제 굴 안에서 편히 쉬어요."},
        {"category": "ADHD", "name": "산만한 꼬마 다람쥐", "emoji": "🐿️", "description": "하고 싶은 게 정말 많군요! 도토리를 하나씩 모아볼까요?"},
        {"category": "BIPOLAR", "name": "알록달록 카멜레온", "emoji": "🦎", "description": "매일 색이 변해도 당신은 여전히 아름다운 카멜레온이에요."},
        {"category": "OCD", "name": "정리대장 펭귄", "emoji": "🐧", "description": "정리된 얼음 위가 편안하죠? 가끔은 미끄러져도 괜찮아요."},
        {"category": "PTSD", "name": "상처를 방패 삼은 고슴도치", "emoji": "🦔", "description": "가시 뒤에 숨겨진 따뜻한 마음을 숲이 지켜줄게요."},
        {"category": "EATING_DISORDER", "name": "마음을 채우는 판다", "emoji": "🐼", "description": "무엇을 먹든, 얼마나 먹든 당신은 충분히 소중해요."},
        {"category": "SCHIZOPHRENIA", "name": "몽환적인 검은 고양이", "emoji": "🐈‍⬛", "description": "밤의 숲을 조용히 누비는 당신만의 세계를 응원해요."},
        {"category": "ANGER", "name": "까칠한 햄스터", "emoji": "🐹", "description": "볼이 빵빵해질 정도로 화가 났을 땐 쳇바퀴를 잠시 멈춰봐요."}
    ]

    for a in animal_list:
        # 이미 있으면 업데이트, 없으면 생성
        existing = db.query(models.Animal).filter(models.Animal.category == a["category"]).first()
        if existing:
            existing.name = a["name"]
            existing.emoji = a["emoji"]
            existing.description = a["description"]
        else:
            db.add(models.Animal(**a))
    
    db.commit()
    db.close()
    print("✅ 동물 데이터 9종이 DB에 완벽하게 저장되었습니다.")

if __name__ == "__main__":
    seed_animals()