import { useIsFocused, useNavigation } from '@react-navigation/native';
import { useMainContext } from './MainContext';
import React, { useEffect, useRef , createContext, useContext, useState} from 'react';
import { Animated, StatusBar, StyleSheet, Alert, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem, ScrollView} from 'react-native';
import Checkbox from './Checkbox';
import ReportModal, { ReportResult } from './ReportModal';
import { COLORS } from './assets/Maincolors';
import {useBottomBar} from './BottomBarContext';
import { API_BASE_URL } from './config';

import Svg, { Defs, Pattern, Rect, Path as SvgPath } from 'react-native-svg';

//임시 리포트 데이터
const MOCK_REPORT = {"indicator_1":{"report_explain":"🐢","report_value":"🐢"},"indicator_2":{"report_explain":"현재 마음 온도는 72.5도 지난주보다 15도 높아졌어요","report_value":{"temp":"72.5","msg":"15"}},"indicator_3":{"report_explain":"이번 주 감정의 파동이 적절하게 유지되고 있습니다.","report_value":[{"created_at":"2026-04-01","temp_val":65.2},{"created_at":"2026-04-02","temp_val":70.1},{"created_at":"2026-04-03","temp_val":68.5}]},"indicator_4":{"report_explain":"루틴을 꾸준히 수행한 결과 회복 탄력성이 72.5%로 높게 나타납니다.","report_value":"72.5%"},"indicator_5":{"report_explain":"산책 루틴이 당신의 기분을 가장 빠르게 회복시켜 주었습니다.","report_value":[{"routine":"산책","effect":85},{"routine":"명상","effect":60}]},"indicator_6":{"report_explain":"14일 중 12일 기록 성공","report_value":"12"},"indicator_7":{"report_explain":"루틴 수행 여부에 따라 에너지가 15도 변화하는 패턴이 확인됩니다.","report_value":"15"},"indicator_8":{"report_explain":"🛡️ 이번 주 5번의 급격한 감정 하락 방어","report_value":"5"},"indicator_9":{"report_explain":"🔴 [8, 15, 22]개의 레드존 포인트가 감지되었습니다.","report_value":[8,15,22]},"indicator_10":{"report_explain":"사용자님의 감정점수는 AI 예측과 3.5도 차이가 나요.","report_value":{"user":72.5,"ai":69.0,"gap":3.5}},"indicator_11":{"report_explain":"이번 주 당신을 괴롭힌 키워드는 '업무', '불면', '관계'입니다.","report_value":["업무","불면","관계"]},"indicator_12":{"report_explain":"현재 패턴 유지 시 위기 도달 확률은 27.5%입니다.","report_value":"27.5"}};

//현제 데이터 구조
interface currentData{
  user_id: string;
  user_animal: string | null;
  assigned_category: string | null;
  signup_date: string;
  weekly_analysis: ReportResult | { status: 'no_data' } | null;
  recommendations: string[];
}

//백엔드에서 데이터 불러오기
const fetchCurrentData = async (userID: string): Promise<currentData | null> => {
    try{
        const responce = await fetch(`${API_BASE_URL}/api/analysis/api/report/${userID}`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
        });
        if (!responce.ok){
          const errorData = await responce.json();
            Alert.alert("데이터 불러오기 실패", errorData.detail);
            return null;
        }
        const userData: currentData = await responce.json();
        console.log(userData);
        return userData;
    }catch(error){
        console.error('데이터 불러오기 실패:', error);
        return null;
    }
}

interface emotionData{
  level: string;
  message: string | null;
}

const fetchEmotionData = async (userID: string): Promise<emotionData | null> => {
    try{
        const responce = await fetch(`${API_BASE_URL}/api/analysis/api/emotion-alert/${userID}`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
        });
        if (!responce.ok){
          const errorData = await responce.json();
            Alert.alert("데이터 불러오기 실패", errorData.detail);
            return null;
        }
        const userData: emotionData = await responce.json();
        console.log(userData);
        return userData;
    }catch(error){
        console.error('데이터 불러오기 실패:', error);
        return null;
    }
}

const normalizeWeeklyAnalysis = (weeklyAnalysis: currentData['weekly_analysis']): ReportResult | null => {
  if (!weeklyAnalysis) return null;
  if ((weeklyAnalysis as { status?: string }).status === 'no_data') return null;
  return weeklyAnalysis as ReportResult;
};

// 💡 루틴 메모장 영역
const Routines = ({routines, userID}: {routines: string[]|undefined, userID: string})=>{
    const toggleRoutine = async (routine: string, isDone: boolean) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/diary/routine`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userID,
                    routine_name: routine,
                    is_done: isDone
                })
            });
            if (!response.ok) {
                console.error("루틴 상태 업데이트 실패");
            }
        } catch (error) {
            console.error("네트워크 오류:", error);
        }
    };

    return(
        <View style={styles.milkyCard}>
            <View style={styles.highlightedTitleContainer}>
              <View style={styles.highlighter}>
                <View style={styles.highlighterEnd} />
              </View>
              <Text style={styles.sectionTitle}>오늘의 숲 가꾸기</Text>
            </View>
            
            <View style={styles.routineListContainer}>
                {routines && routines.length > 0 ? (
                  routines.map((routine, index) => (
                      <View key={index} style={styles.routineItem}>
                        <Checkbox 
                            onCheck={() => toggleRoutine(routine, true)}
                            onUncheck={() => toggleRoutine(routine, false)}
                        >
                            <Text style={styles.routineText}>{routine}</Text>
                        </Checkbox>
                      </View>
                  ))
                ) : (
                  <Text style={styles.emptyRoutineText}>아직 등록된 루틴이 없어요.</Text>
                )}
            </View>
        </View>)
};

const MainScreen = () => {
  const isFocused = useIsFocused();
  const navigation = useNavigation<any>();
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const { setBottomBarContent } = useBottomBar();
  const {handleLogOut, user} = useMainContext();
  const [currentUserData, setCurrentUserData] = useState<currentData | null>(null);
  const [emotionMessage, setEmotionMessage] = useState<emotionData | null>(null);
  const reportData = normalizeWeeklyAnalysis(currentUserData?.weekly_analysis ?? null);

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
      console.log('사전 테스트 문항 응답:', data);
      Alert.alert('요청 성공', '설문 GET 요청을 보냈습니다.');
    } catch (error) {
      console.error('사전 테스트 요청 실패:', error);
      Alert.alert('사전 테스트 요청 실패', '네트워크 오류');
    }
  };

  useEffect(() => {
    const load= async () => {
      const data = await fetchCurrentData(user.user_id);
      if (data) setCurrentUserData(data);
      const emotionData = await fetchEmotionData(user.user_id);
      if (emotionData) setEmotionMessage(emotionData);
    }
    load();
  }, [user.user_id]);

  useEffect(() => {
    if(isFocused){
      setBottomBarContent(null); 
      return () => setBottomBarContent(null);
    } 
  }, [isFocused]);

  return (
    // 💡 하단 여백 너머로 회색이 비치지 않도록 전체 배경을 모눈종이 색상(#fafafa)으로 칠합니다!
    <View style={{ flex: 1, backgroundColor: '#fafafa' }}>
      {/* 배경 모눈종이 */}
      <View style={StyleSheet.absoluteFill}>
        <Svg width="100%" height="100%">
          <Defs>
            <Pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <Rect width="30" height="30" fill="#fafafa" />
              <SvgPath d="M 30 0 L 0 0 0 30" fill="none" stroke="#e6e6e6" strokeWidth="1" />
            </Pattern>
          </Defs>
          <Rect width="100%" height="100%" fill="url(#grid)" />
        </Svg>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContainer} showsVerticalScrollIndicator={false}>
        <ReportModal isVisible={reportModalVisible} data={reportData ?? null} onClose={() => setReportModalVisible(false)}/>
        
        {/* 환영 카드 */}
        <View style={styles.milkyCard}>
          <View style={styles.highlightedTitleContainer}>
            <View style={styles.highlighter}>
              <View style={styles.highlighterEnd} />
            </View>
            <Text style={styles.sectionTitle}>안녕하세요, {user.user_id}님!</Text>
          </View>
          
          {/* 감정 메시지 */}
          {emotionMessage?.message && (
            <View style={styles.messageContainer}>
              <Text style={styles.messageText}>{emotionMessage.message}</Text>
            </View>
          )}
        </View>

        {/* 젤리 버튼 그룹 */}
        <View style={styles.buttonGroup}>
          <TouchableOpacity activeOpacity={0.8} style={styles.unifiedBtnWrapper} onPress={() => { navigation.navigate("채팅"); requestSurvey(); }}>
            <View style={styles.unifiedBtnInner}>
              <Text style={styles.unifiedBtnText}>마음의 숲 사전 테스트 🌱</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity activeOpacity={0.8} style={styles.unifiedBtnWrapper} onPress={() => setReportModalVisible(true)}>
            <View style={styles.unifiedBtnInner}>
              <Text style={styles.unifiedBtnText}>나의 주간 리포트 열어보기</Text>
            </View>
          </TouchableOpacity> 
        </View>

        {/* 오늘의 루틴 */}
        <Routines routines={currentUserData?.recommendations} userID={user.user_id} />

        {/* 로그아웃 버튼 */}
        <TouchableOpacity onPress={handleLogOut} style={styles.logoutBtn}>
          <Text style={styles.logoutText}>숲에서 나가기 (로그아웃)</Text>
        </TouchableOpacity>
        
      </ScrollView>
    </View>
  )
};

const styles = StyleSheet.create({
  scrollContainer: {
    flexGrow: 1,
    alignItems: 'center',
    paddingTop: 30,
    paddingBottom: 100, 
    paddingHorizontal: 20,
    backgroundColor: 'transparent',
  },
  
  // 💡 뽀얀 우유 질감을 위해 테두리를 아예 지우고 그림자를 더 크고 은은하게 퍼뜨렸습니다!
  milkyCard: {
    width: '100%',
    backgroundColor: 'rgba(255, 255, 255, 0.95)', // 투명도를 아주 살짝 낮춰 우유의 탁함을 살림
    borderRadius: 24,
    padding: 24,
    borderWidth: 0, // 💡 선명한 테두리를 날려서 경계를 허뭅니다
    shadowColor: '#a1b594', // 부드럽고 따뜻한 연두빛 그림자
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15, // 그림자 농도를 연하게
    shadowRadius: 25, // 반경을 넓게 퍼뜨려 몽글몽글한 느낌 극대화
    elevation: 2, // 안드로이드에서도 날카롭지 않게 최소한의 값만 적용
    marginBottom: 25,
  },

  highlightedTitleContainer: {
    position: 'relative',
    paddingHorizontal: 6,
    justifyContent: 'center',
    alignSelf: 'flex-start', 
    marginBottom: 10,
  },
  highlighter: {
    position: 'absolute',
    bottom: 4, 
    left: -2,
    right: -4,
    height: 16, 
    backgroundColor: '#eaffdf', 
    borderRadius: 3,
    transform: [{ skewX: '-15deg' }, { rotate: '-2deg' }], 
    flexDirection: 'row', 
    justifyContent: 'flex-end', 
  },
  highlighterEnd: {
    width: 2, 
    height: '100%',
    backgroundColor: '#cffff1',
    borderTopRightRadius: 3,
    borderBottomRightRadius: 3,
  },
  sectionTitle: {
    fontFamily: 'ownglyph',
    fontSize: 32, 
    color: '#2a3a21',
  },

  messageContainer: {
    alignItems: 'flex-start', 
    marginTop: 6,
  },
  messageText: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 15,
    color: '#2a3a21', 
    textAlign: 'left',
    lineHeight: 22,
  },

  buttonGroup: {
    width: '100%',
    gap: 15, 
    marginBottom: 25,
  },
  unifiedBtnWrapper: {
    borderRadius: 20,
    shadowColor: '#D3D3D3', 
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  unifiedBtnInner: {
    height: 60, 
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)', 
    borderWidth: 1.5,
    borderColor: '#eaffdf', 
  },
  unifiedBtnText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 16,
    color: '#597d48', 
  },

  routineListContainer: {
    marginTop: 5,
  },
  routineItem: {
    marginVertical: 6, 
  },
  routineText: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 16,
    color: '#2a3a21', 
    marginLeft: 8,
  },
  emptyRoutineText: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 15,
    color: '#b4b4b4', 
    textAlign: 'left', 
    paddingVertical: 10,
  },

  logoutBtn: {
    marginTop: 10,
    padding: 10,
  },
  logoutText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 14,
    color: '#b4b4b4', 
    textDecorationLine: 'underline',
  },
});

export default MainScreen;