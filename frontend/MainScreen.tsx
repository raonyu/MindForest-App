import { useIsFocused, useNavigation } from '@react-navigation/native';
import { useMainContext } from './MainContext';
import React, { useEffect, useState } from 'react';
import { StyleSheet, Alert, View, Text, TouchableOpacity, ScrollView } from 'react-native';
import ReportModal, { ReportResult } from './ReportModal';
import { useBottomBar } from './BottomBarContext';
import { API_BASE_URL } from './config';
import { AnimatedCircularProgress } from 'react-native-circular-progress';

//임시 리포트 데이터
const MOCK_REPORT = { "indicator_1": { "report_explain": "🐢", "report_value": "🐢" }, "indicator_2": { "report_explain": "현재 마음 온도는 72.5도 지난주보다 15도 높아졌어요", "report_value": { "temp": "72.5", "msg": "15" } }, "indicator_3": { "report_explain": "이번 주 감정의 파동이 적절하게 유지되고 있습니다.", "report_value": [{ "created_at": "2026-04-01", "temp_val": 65.2 }, { "created_at": "2026-04-02", "temp_val": 70.1 }, { "created_at": "2026-04-03", "temp_val": 68.5 }] }, "indicator_4": { "report_explain": "루틴을 꾸준히 수행한 결과 회복 탄력성이 72.5%로 높게 나타납니다.", "report_value": "72.5%" }, "indicator_5": { "report_explain": "산책 루틴이 당신의 기분을 가장 빠르게 회복시켜 주었습니다.", "report_value": [{ "routine": "산책", "effect": 85 }, { "routine": "명상", "effect": 60 }] }, "indicator_6": { "report_explain": "14일 중 12일 기록 성공", "report_value": "12" }, "indicator_7": { "report_explain": "루틴 수행 여부에 따라 에너지가 15도 변화하는 패턴이 확인됩니다.", "report_value": "15" }, "indicator_8": { "report_explain": "🛡️ 이번 주 5번의 급격한 감정 하락 방어", "report_value": "5" }, "indicator_9": { "report_explain": "🔴 [8, 15, 22]개의 레드존 포인트가 감지되었습니다.", "report_value": [8, 15, 22] }, "indicator_10": { "report_explain": "사용자님의 감정점수는 AI 예측과 3.5도 차이가 나요.", "report_value": { "user": 72.5, "ai": 69.0, "gap": 3.5 } }, "indicator_11": { "report_explain": "이번 주 당신을 괴롭힌 키워드는 '업무', '불면', '관계'입니다.", "report_value": ["업무", "불면", "관계"] }, "indicator_12": { "report_explain": "현재 패턴 유지 시 위기 도달 확률은 27.5%입니다.", "report_value": "27.5" } };

//루틴 데이터 구조
interface routineData {
  user_routine_id: number;
  content: string;
  is_completed: boolean;
}

//현제 데이터 구조
interface currentData {
  user_id: string;
  is_onboarding_done?: boolean;
  assigned_category: string | null;
  animal_category: string | null;
  animal_emoji: string | null;
  animal_description: string | null;
  diagnosis_result?: {
    total_score: number;
    result_message: string;
  };
  today_routines?: routineData[];
  weekly_analysis?: any;
}

//백엔드에서 데이터 불러오기
const fetchCurrentData = async (userID: string): Promise<currentData | null> => {
  try {
    const responce = await fetch(`${API_BASE_URL}/api/user/profile/${userID}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!responce.ok) {
      const errorData = await responce.json();
      Alert.alert("데이터 불러오기 실패", errorData.detail);
      return null;
    }
    return await responce.json();
  } catch (error) {
    console.error('데이터 불러오기 실패:', error);
    return null;
  }
}

interface emotionData {
  level: string;
  message: string | null;
}

const fetchEmotionData = async (userID: string): Promise<emotionData | null> => {
  try {
    const responce = await fetch(`${API_BASE_URL}/api/analysis/api/emotion-alert/${userID}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!responce.ok) {
      const errorData = await responce.json();
      Alert.alert("데이터 불러오기 실패", errorData.detail);
      return null;
    }
    return await responce.json();
  } catch (error) {
    console.error('데이터 불러오기 실패:', error);
    return null;
  }
}

const fetchReportData = async (userID: string): Promise<any | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/analysis/report/${userID}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('리포트 데이터 불러오기 실패:', error);
    return null;
  }
}

const normalizeWeeklyAnalysis = (weeklyAnalysis: currentData['weekly_analysis']): ReportResult | null => {
  if (!weeklyAnalysis) return null;
  if ((weeklyAnalysis as { status?: string }).status === 'no_data') return null;
  return weeklyAnalysis as ReportResult;
};

interface RoutinesProps {
  routines: routineData[] | undefined;
}

// 루틴 목록 컴포넌트
const Routines = ({ routines: initialRoutines }: RoutinesProps) => {
  const [localRoutines, setLocalRoutines] = useState<routineData[]>([]);

  useEffect(() => {
    if (initialRoutines) {
      setLocalRoutines(initialRoutines);
    }
  }, [initialRoutines]);

  const toggleRoutine = async (routineId: number, currentStatus: boolean) => {
    const nextStatus = !currentStatus;
    setLocalRoutines(prev =>
      prev.map(r => r.user_routine_id === routineId ? { ...r, is_completed: nextStatus } : r)
    );

    try {
      const response = await fetch(`${API_BASE_URL}/api/routines/complete/${routineId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error("루틴 상태 업데이트 실패");
    } catch (error) {
      console.error("네트워크 오류:", error);
      setLocalRoutines(prev =>
        prev.map(r => r.user_routine_id === routineId ? { ...r, is_completed: currentStatus } : r)
      );
    }
  };

  return (
    <View style={styles.routinesContainer}>
      {localRoutines?.map((routine, index) => {
        const isLast = index === localRoutines.length - 1;
        return (
            <TouchableOpacity
                key={routine.user_routine_id}
                style={[styles.routineItem, isLast && styles.routineItemLast]}
                onPress={() => toggleRoutine(routine.user_routine_id, routine.is_completed)}
                activeOpacity={0.7}
            >
                <View style={[styles.checkCircle, routine.is_completed && styles.checkCircleCompleted]}>
                    {routine.is_completed && <Text style={{color: 'white', fontSize: 12, fontWeight: 'bold'}}>✓</Text>}
                </View>
                <View style={styles.routineTextContainer}>
                    <Text style={routine.is_completed ? styles.routineTextCompleted : styles.routineText}>
                        {routine.content}
                    </Text>
                </View>
            </TouchableOpacity>
        );
      })}
      {(!localRoutines || localRoutines.length === 0) && (
          <Text style={{color: '#888', textAlign: 'center', padding: 10}}>오늘의 루틴이 없습니다.</Text>
      )}
    </View>
  );
};

const MainScreen = () => {
  const isFocused = useIsFocused();
  const navigation = useNavigation<any>();
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const { setBottomBarContent } = useBottomBar();
  const { handleLogOut, user, setUser } = useMainContext();
  const [currentUserData, setCurrentUserData] = useState<currentData | null>(null);
  const [emotionMessage, setEmotionMessage] = useState<emotionData | null>(null);
  const [reportData, setReportData] = useState<any>(null);

  const requestSurvey = async () => {
    try {
      const surveyType = 'DEPRESSION';
      const response = await fetch(`${API_BASE_URL}/api/survey/api/survey/${surveyType}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        const errorData = await response.json();
        Alert.alert('사전 테스트 요청 실패', errorData.detail || '서버 오류');
        return;
      }
      const data = await response.json();
    } catch (error) {
      console.error('사전 테스트 요청 실패:', error);
      Alert.alert('사전 테스트 요청 실패', '네트워크 오류');
    }
  };

  const startCategorySurvey = async () => {
    let surveyType = currentUserData?.assigned_category;
    if (currentUserData?.animal_category === "조용히 움츠린 거북이") {
      surveyType = "DEPRESSION";
    }

    if (!surveyType) {
      Alert.alert("알림", "아직 진행할 수 있는 유형 설문조사가 없습니다.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/survey/${surveyType}`);
      if (!response.ok) {
        Alert.alert('설문 문항 불러오기 실패', '서버 오류');
        return;
      }

      const data = await response.json();
      if (data && data.length > 0) {
        navigation.navigate("채팅", { surveyMode: true, surveyQuestions: data, surveyType: surveyType });
      } else {
        Alert.alert('알림', '가져올 설문 문항이 없습니다.');
      }
    } catch (error) {
      console.error('설문 문항 불러오기 실패:', error);
      Alert.alert('오류', '네트워크 연결을 확인해주세요.');
    }
  };

  useEffect(() => {
    const load = async () => {
      const data = await fetchCurrentData(user.user_id);
      if (data) {
        setCurrentUserData(data);
        if (setUser) setUser((prev: any) => ({ ...prev, ...data }));
      }
      const emotionData = await fetchEmotionData(user.user_id);
      if (emotionData) setEmotionMessage(emotionData);

      const report = await fetchReportData(user.user_id);
      if (report) {
        setReportData(report);
      }
    }
    if (isFocused) load();
  }, [user.user_id, isFocused]);

  useEffect(() => {
    if (isFocused) {
      setBottomBarContent(null);
      return () => setBottomBarContent(null);
    }
  }, [isFocused]);

  useEffect(() => {
    if (currentUserData?.diagnosis_result?.total_score !== undefined && currentUserData.diagnosis_result.total_score >= 20) {
      Alert.alert("알림", "현재 감정점수가 높게 측정되었습니다.\n루틴 수행을 추천드립니다.", [{ text: "확인" }]);
    }
  }, [currentUserData?.diagnosis_result?.total_score]);

  // 달성률 계산
  const routines = currentUserData?.today_routines || [];
  const completedRoutines = routines.filter(r => r.is_completed).length;
  const routineRate = routines.length > 0 ? Math.round((completedRoutines / routines.length) * 100) : 0;

  return (
    <View style={{ flex: 1, backgroundColor: '#F4F5F9' }}>
      <ScrollView contentContainerStyle={styles.scrollContainer} showsVerticalScrollIndicator={false}>
        <ReportModal isVisible={reportModalVisible} data={reportData ?? null} onClose={() => setReportModalVisible(false)} />

        {/* 헤더 영역 */}
        <View style={styles.header}>
            <View>
                <Text style={styles.headerGreeting}>안녕하세요,</Text>
                <Text style={styles.headerName}>{user.user_id}님!</Text>
            </View>
            <View style={styles.profileIconPlaceholder}>
                <Text style={{fontSize: 24}}>👤</Text>
            </View>
        </View>

        {/* 감정 메시지 알림바 */}
        {emotionMessage?.message && (
            <View style={styles.messageAlert}>
                <Text style={styles.messageText}>💡 {user?.diagnosis_result?.result_message || emotionMessage?.message}</Text>
            </View>
        )}

        {/* 중앙 메인 동물 카드 */}
        <View style={styles.mainCard}>
            <View style={styles.mainCardContent}>
                {/* 중앙 동물 캐릭터 */}
                <View style={styles.animalCenter}>
                    <Text style={styles.animalEmoji}>{user?.animal_emoji || '🌱'}</Text>
                </View>

                {/* 정보 및 진행률 행 */}
                <View style={styles.cardInfoRow}>
                    <View style={styles.cardTextInfo}>
                        <Text style={styles.animalCategory}>{user?.animal_category || '아직 동물이 없어요'}</Text>
                        <Text style={styles.animalDescription} numberOfLines={2}>
                            {user?.animal_description || '사전 테스트를 통해 나만의 동물을 확인해보세요.'}
                        </Text>
                    </View>
                    
                    <View style={styles.progressContainer}>
                        <AnimatedCircularProgress
                            size={64}
                            width={6}
                            fill={routineRate}
                            tintColor="#8c7ae6"
                            backgroundColor="#f1f2f6"
                            lineCap="round"
                        >
                            {() => (
                                <Text style={styles.progressText}>{routineRate}%</Text>
                            )}
                        </AnimatedCircularProgress>
                    </View>
                </View>
            </View>

            {/* 설문조사 메인 버튼 */}
            {(!currentUserData?.assigned_category && currentUserData?.animal_category !== "조용히 움츠린 거북이") ? (
                <TouchableOpacity style={styles.primaryButton} activeOpacity={0.8} onPress={() => { navigation.navigate("채팅", { initialMessage: "사전 테스트 시작하기" }); requestSurvey(); }}>
                    <Text style={styles.primaryButtonText}>마음의 숲 사전 테스트 진행하기</Text>
                </TouchableOpacity>
            ) : (
                <TouchableOpacity style={styles.primaryButton} activeOpacity={0.8} onPress={() => { navigation.navigate("채팅"); startCategorySurvey(); }}>
                    <Text style={styles.primaryButtonText}>유형별 심화 테스트 진행하기</Text>
                </TouchableOpacity>
            )}
        </View>

        {/* 리포트 진입 버튼 */}
        <TouchableOpacity style={styles.reportCard} activeOpacity={0.8} onPress={() => setReportModalVisible(true)}>
            <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <View style={styles.reportIconBg}>
                    <Text style={{fontSize: 24}}>📊</Text>
                </View>
                <View>
                    <Text style={styles.reportTitle}>나의 주간 리포트</Text>
                    <Text style={styles.reportSubtitle}>이번 주 감정 패턴 분석 보기</Text>
                </View>
            </View>
            <Text style={{fontSize: 24, color: '#b2bec3', fontWeight: 'bold'}}>›</Text>
        </TouchableOpacity>

        {/* 오늘의 루틴 영역 */}
        <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>오늘의 루틴</Text>
        </View>
        <Routines routines={currentUserData?.today_routines} />

        {/* 로그아웃 */}
        <TouchableOpacity onPress={handleLogOut} style={styles.logoutBtn}>
          <Text style={styles.logoutText}>로그아웃</Text>
        </TouchableOpacity>

      </ScrollView>
    </View>
  )
};

const styles = StyleSheet.create({
  scrollContainer: {
    flexGrow: 1,
    alignItems: 'center',
    paddingTop: 50,
    paddingBottom: 100,
    paddingHorizontal: 24,
  },
  header: {
    width: '100%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  headerGreeting: {
    fontSize: 15,
    color: '#636e72',
    fontFamily: 'NanumSquareRoundR',
  },
  headerName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2d3436',
    fontFamily: 'NanumSquareRoundB',
    marginTop: 4,
  },
  profileIconPlaceholder: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  
  messageAlert: {
    width: '100%',
    backgroundColor: '#e6e8fa',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
  },
  messageText: {
    fontSize: 14,
    color: '#341f97',
    fontFamily: 'NanumSquareRoundR',
    lineHeight: 20,
  },

  mainCard: {
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 32,
    padding: 24,
    shadowColor: '#8c7ae6',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 5,
    marginBottom: 24,
  },
  mainCardContent: {
    marginBottom: 24,
  },
  animalCenter: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
    backgroundColor: '#f8f9fa',
    borderRadius: 24,
    marginBottom: 24,
  },
  animalEmoji: {
    fontSize: 110,
  },
  cardInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTextInfo: {
    flex: 1,
    marginRight: 16,
  },
  animalCategory: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2d3436',
    marginBottom: 8,
    fontFamily: 'NanumSquareRoundB',
  },
  animalDescription: {
    fontSize: 13,
    color: '#636e72',
    lineHeight: 18,
    fontFamily: 'NanumSquareRoundR',
  },
  progressContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressText: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#8c7ae6',
  },
  primaryButton: {
    backgroundColor: '#8c7ae6',
    borderRadius: 20,
    paddingVertical: 18,
    alignItems: 'center',
    width: '100%',
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'NanumSquareRoundB',
  },

  reportCard: {
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  reportIconBg: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: '#f1f2f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  reportTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3436',
    marginBottom: 4,
  },
  reportSubtitle: {
    fontSize: 13,
    color: '#636e72',
  },

  sectionHeader: {
    width: '100%',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2d3436',
    fontFamily: 'NanumSquareRoundB',
  },
  routinesContainer: {
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 24,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
    marginBottom: 24,
  },
  routineItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f2f6',
  },
  routineItemLast: {
    borderBottomWidth: 0,
  },
  routineTextContainer: {
    flex: 1,
    marginLeft: 14,
  },
  routineText: {
    fontSize: 15,
    color: '#2d3436',
    fontFamily: 'NanumSquareRoundR',
  },
  routineTextCompleted: {
    fontSize: 15,
    color: '#b2bec3',
    textDecorationLine: 'line-through',
    fontFamily: 'NanumSquareRoundR',
  },
  checkCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    borderWidth: 2,
    borderColor: '#dfe6e9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkCircleCompleted: {
    borderColor: '#8c7ae6',
    backgroundColor: '#8c7ae6',
  },
  
  logoutBtn: {
    marginTop: 10,
    padding: 10,
  },
  logoutText: {
    fontSize: 14,
    color: '#b2bec3',
    textDecorationLine: 'underline',
  },
});

export default MainScreen;