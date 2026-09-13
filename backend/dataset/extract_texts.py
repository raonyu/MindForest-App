import json
import random

def extract_random_texts(file_list, sample_size=5000):
    all_texts = set() # 중복 제거를 위한 집합(Set) 사용
    
    for file_name in file_list:
        print(f"🔄 [{file_name}] 에서 사람 텍스트(HS) 추출 중...")
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for item in data:
                try:
                    # 챗봇(SS) 제외, 사람 말(HS)만 이어서 텍스트 생성
                    content = item['talk']['content']
                    hs_texts = [str(v) for k, v in content.items() if k.startswith('HS') and v]
                    text = " ".join(hs_texts).strip()
                    
                    # 텍스트가 비어있지 않으면 추가
                    if text:
                        all_texts.add(text)
                except KeyError:
                    continue
                    
        except FileNotFoundError:
            print(f"🚨 {file_name} 파일을 찾을 수 없습니다.")
            continue
            
    # 랜덤 샘플링을 위해 리스트로 변환
    all_texts = list(all_texts)
    print(f"\n✅ 두 파일에서 총 {len(all_texts)}개의 유일한 문장을 확보했어!")
    
    # 목표치(5000개)만큼 랜덤 추출 (확보된 문장이 더 적으면 전부 다 씀)
    if len(all_texts) > sample_size:
        sampled_texts = random.sample(all_texts, sample_size)
    else:
        sampled_texts = all_texts
        
    # 추출된 텍스트들을 GPT에게 먹이기 좋게 임시 JSON 파일로 저장
    with open("sampled_texts.json", 'w', encoding='utf-8') as f:
        json.dump(sampled_texts, f, ensure_ascii=False, indent=2)
        
    print(f"🎉 성공! {len(sampled_texts)}개의 텍스트를 'sampled_texts.json'에 저장완료!")

# 실행 (두 파일을 한 번에 읽어서 처리)
target_files = [
    "감성대화말뭉치(최종데이터)_Training.json",
    "감성대화말뭉치(최종데이터)_Validation.json"
]

extract_random_texts(target_files, sample_size=5000)