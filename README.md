# MindForest-App

## 로컬 통합본

최신 main의 리포트·챗봇과 C 브랜치의 감정 강도 입력·비동기 일기 분석·개인 감정 추세를 합친 버전입니다. 원격 업로드 전 검증용입니다.

```powershell
# 최초 설치
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/B/backend/requirement.txt
cd frontend
npm.cmd ci
cd ..
# 첫 번째 터미널: 로컬 DB 준비 및 API 실행
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-local.ps1
# 두 번째 터미널: 웹 실행
cd frontend
npm.cmd run web
```

로컬 DB는 `.local/mindforest.db`입니다. 기존 팀 PostgreSQL을 변경하지 않습니다. 기존 로컬 DB가 있으면 실행 전에 SQLite 백업을 만듭니다. `start-local.ps1 -PrepareOnly`는 서버를 켜지 않고 DB만 준비합니다.

실제 감정 모델 가중치는 Git에 없습니다. 팀에서 학습된 모델과 토크나이저 폴더를 받은 뒤 `MINDFOREST_MODEL_DIR` 환경변수에 지정하고 `backend/emotion_model/requirements.txt`의 추론 의존성을 설치하세요. 상담·BWS에는 유효한 `OPENAI_API_KEY`가 필요합니다. 키는 기존 환경 또는 로컬 `.env`에만 넣으며 실행 스크립트는 이를 덮어쓰지 않습니다.

모델 없이도 일기·사용자가 선택한 감정은 저장됩니다. 분석 실패 상태를 표시하며 Mock 점수를 실제 결과로 저장하지 않습니다. 실기기 연결은 `EXPO_PUBLIC_API_URL`과 서버의 수신 주소를 같은 LAN에 맞게 설정해야 합니다.

```powershell
# 임시 DB를 쓰는 통합 검사 (실제 외부 AI 호출 없음)
.\.venv\Scripts\python.exe -m unittest discover -s backend/B/backend/tests -v
cd frontend
npm.cmd run typecheck
npm.cmd run lint -- --quiet
npx.cmd expo export --platform web
```

기존 DB에 통합본을 직접 적용할 때는 백업한 뒤 `backend/B/backend/migrate_report_fields.py`를 명시적으로 실행하세요. 새 컬럼만 추가하며 기존 사용자·일기는 삭제하지 않습니다.

## 추가 고도화 및 전달 방법

Python 3(Windows Python launcher 포함)과 Node.js 20+가 설치된 PC에서는 다음 명령으로 패키지 설치·로컬 DB 준비·검사를 수행할 수 있습니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup-local.ps1 -Verify
```

새 외부 서비스 연결은 추가하지 않았습니다. 기본 회원가입·감정 입력·일기 저장·화면 실행에는 모델이나 API 키가 필요하지 않습니다. 실제 AI 점수·상담·BWS는 기존과 같이 **별도 모델 파일 및 유효한 개인 API 키**가 필요합니다. 모델 의존성도 설치하려면 `setup-local.ps1 -WithModelDeps`를 사용하세요. `.env.example`과 `frontend/.env.example`에는 선택 설정 예시만 있고 비밀값은 없습니다.

- 모든 리포트·개인 추세·상담 요약에서 같은 마음 온도식을 사용하고, 놀람은 긍정·부정 계산에서 제외합니다.
- 자가보고 감정/강도와 해당 감정의 AI 상대점수를 나란히 표시합니다. 내부 환산 온도의 차이도 표시하지만, 서로 다른 척도이며 AI가 정답이라는 뜻이 아닙니다.
- 시험·팀플·수면·친구·가족·취업 등 상황 표현을 로컬 주제 사전으로 추출합니다. 과거 일기도 표시 시 추출할 수 있어 별도 데이터 초기화가 필요하지 않습니다. 이는 원인 분석이나 범용 키워드 모델이 아닙니다.
- 루틴 완료만으로 +10점을 부여하지 않습니다. 실제 완료한 날/완료하지 않은 날을 나누어 일별 평균을 비교하고, 양쪽 최소 3일 기록이 있을 때 순위를 표시합니다.
- 완료 직전 24시간 안의 분석 완료 기록과, 완료 후 24시간 안에 **새로 제출된** 같은 날짜의 일기를 연결해 전후 스냅샷을 만듭니다. 이전 비동기 작업이 늦게 끝난 것은 사후 측정으로 사용하지 않습니다. 기록이 없는 경우 변화량을 만들지 않습니다. 여러 루틴을 함께 했다면 공유 관찰임을 표시하며 인과 효과로 해석하지 않습니다.
- 완료 취소 시 관찰 스냅샷을 제거합니다. 일기 삭제 시 연결된 관찰·분석 기록도 제거합니다. 기존 `score_diff=10` 값은 새 리포트 계산에 사용하지 않습니다.

운영 측정 API: `GET /api/analysis/api/metrics/{user_id}?days=30`. 성공·실패·BWS 시도/성공·평균 및 p95 분석 시간을 반환합니다. 빈 텍스트와 폐기된 이전 버전은 호출 비율 분모에서 제외합니다. 일기 원문은 운영 측정 테이블에 저장하지 않습니다. 이 엔드포인트도 기존 single-user 개발 API와 같은 접근 방식이므로 운영 공개 전 사용자 인증 적용이 필요합니다.

### 모델/GPT 비교 평가

기존 `emotion_model/evaluate.py`의 검증용 threshold 탐색은 유지합니다. 추가 비교 도구는 학습에 사용하지 않은 정답 라벨과 예측 결과를 입력받아 Macro/Micro F1, 감정별 Precision/Recall/F1, BWS 비율과 측정된 평균 시간을 계산합니다.

```powershell
cd backend/B/backend
# 모델 없이 저장된 예측으로 검증. 두 예측 파일은 정답 데이터와 행 순서/id가 같아야 합니다.
..\..\..\.venv\Scripts\python.exe benchmark_emotions.py --dataset labels.jsonl --predictions engine.jsonl --gpt-predictions gpt.jsonl --output comparison.json
# 실제 모델 실행 (설정된 BWS가 외부 API를 호출할 수 있음)
..\..\..\.venv\Scripts\python.exe benchmark_emotions.py --dataset labels.jsonl --output measured.json
# GPT 직접 채점까지 새로 호출하려면 명시적으로 --include-gpt 추가 (API 비용 발생 가능)
```

정답 행: `{"id":"1","text":"일기","labels":{"joy":1,"trust":0,"fear":0,"surprise":0,"sadness":0,"disgust":0,"anger":0,"anticipation":0}}`

예측 행: `{"id":"1","emotions":{"joy":80,"trust":20,"fear":10,"surprise":10,"sadness":5,"disgust":5,"anger":5,"anticipation":20}}`. 선택적으로 실제 측정한 `metrics`를 포함할 수 있습니다. 시간 정보가 없으면 null로 두며 속도를 만들어내지 않습니다. 두 방식 모두 50점 이상을 분류 기준으로 비교하며, BWS는 8감정 숫자를 바꾸지 않으므로 이 F1로 BWS 대표 감정 선택의 정확성을 주장하지 않습니다.
