import { useIsFocused, useNavigation } from '@react-navigation/native';
import { useMainContext } from './MainContext';
import React, { useEffect, useRef , createContext, useContext, useState} from 'react';
import { Animated, StatusBar, StyleSheet, Alert, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem} from 'react-native';
import Checkbox from './Checkbox';
import ReportModal, { ReportResult } from './ReportModal';
import { COLORS } from './assets/Maincolors';
import {useBottomBar} from './BottomBarContext';


//임시 리포트 데이터
const MOCK_REPORT = {"indicator_1":{"report_explain":"🐢","report_value":"🐢"},"indicator_2":{"report_explain":"현재 마음 온도는 72.5도 지난주보다 15도 높아졌어요","report_value":{"temp":"72.5","msg":"15"}},"indicator_3":{"report_explain":"이번 주 감정의 파동이 적절하게 유지되고 있습니다.","report_value":[{"created_at":"2026-04-01","temp_val":65.2},{"created_at":"2026-04-02","temp_val":70.1},{"created_at":"2026-04-03","temp_val":68.5}]},"indicator_4":{"report_explain":"루틴을 꾸준히 수행한 결과 회복 탄력성이 72.5%로 높게 나타납니다.","report_value":"72.5%"},"indicator_5":{"report_explain":"산책 루틴이 당신의 기분을 가장 빠르게 회복시켜 주었습니다.","report_value":[{"routine":"산책","effect":85},{"routine":"명상","effect":60}]},"indicator_6":{"report_explain":"14일 중 12일 기록 성공","report_value":"12"},"indicator_7":{"report_explain":"루틴 수행 여부에 따라 에너지가 15도 변화하는 패턴이 확인됩니다.","report_value":"15"},"indicator_8":{"report_explain":"🛡️ 이번 주 5번의 급격한 감정 하락 방어","report_value":"5"},"indicator_9":{"report_explain":"🔴 [8, 15, 22]개의 레드존 포인트가 감지되었습니다.","report_value":[8,15,22]},"indicator_10":{"report_explain":"사용자님의 감정점수는 AI 예측과 3.5도 차이가 나요.","report_value":{"user":72.5,"ai":69.0,"gap":3.5}},"indicator_11":{"report_explain":"이번 주 당신을 괴롭힌 키워드는 '업무', '불면', '관계'입니다.","report_value":["업무","불면","관계"]},"indicator_12":{"report_explain":"현재 패턴 유지 시 위기 도달 확률은 27.5%입니다.","report_value":"27.5"}};
//현제 데이터 구조
interface currentData{
  user_id: string;
  user_animal: string | null;
  assigned_category: string | null;
  signup_date: string;
  weekly_analysis: ReportResult | null;
  recommendations: string[];
}
//백엔드에서 데이터 불러오기
const fetchCurrentData = async (userID: string): Promise<currentData | null> => {
    try{
        const responce = await fetch(`http://localhost:8000/api/analysis/api/report/${userID}`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
        });
        //데이터 불러오기 실패 처리
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
        const responce = await fetch(`http://localhost:8000/api/analysis/api/emotion-alert/${userID}`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
        });
        //데이터 불러오기 실패 처리
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
const Routines = ({routines}: {routines: string[]|undefined})=>{
    return(
        <View style={{alignItems: 'center', margin: 40}}>
            <Text style={{fontSize: 20, fontWeight:'semibold'}}>오늘의 루틴</Text>
            <View style={styles.routineContainer}>
                {routines?.map((routine, index) => (
                        <Checkbox key={index}>
                            <Text style={{fontSize: 24, color: 'white'}}>{routine}</Text>
                        </Checkbox>
                    ))}
            </View>
        </View>)
}; 

const MainScreen = () => {
  const isFocused = useIsFocused();//현재 화면이 포커스 되어있는지 확인
  const navigation = useNavigation<any>();
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const { setBottomBarContent } = useBottomBar();
  const {handleLogOut, user} = useMainContext();
  const [currentUserData, setCurrentUserData] = useState<currentData | null>(null);
  const [emotionMessage, setEmotionMessage] = useState<emotionData | null>(null);

  //유저데이터 불러오기
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
    //하단바 설정
    if(isFocused){
      setBottomBarContent(
        <View>
          <View style={styles.bottomTitleContainer}>
            <Text style={styles.bottomBarText}>메인화면입니다</Text>
          </View>
        </View>
    );
    //다른 화면으로 전환 시 하단바 초기화
    return () => setBottomBarContent(null);
    } 
  }, [isFocused]);

  //메인 화면 내용
  return (
  <View style={{flex: 1, backgroundColor: 'transparent', alignItems: 'center'}}>
    <ReportModal isVisible={reportModalVisible} data={MOCK_REPORT} onClose={() => setReportModalVisible(false)}/>
    <Text style={{fontSize: 24}}>환영합니다 {user.user_id}님!</Text>
    <Text style={{fontSize: 12, textAlign: 'center'}}>{emotionMessage?.message}</Text>
    <TouchableOpacity style={styles.baseButton} onPress={() => {navigation.navigate("채팅", { startSurvey: { surveyType: 'DEPRESSION' } })}}>
      <Text style={styles.baseButtonText}>
          🌱마음의 숲 사전 테스트 시작하기
      </Text>
    </TouchableOpacity>
    <TouchableOpacity
      style={styles.baseButton}
      onPress={() => setReportModalVisible(true)}>
      <Text style={styles.baseButtonText}>주간 리포트 확인하기</Text>
    </TouchableOpacity>
    <TouchableOpacity onPress={handleLogOut} style={styles.baseButton}>
      <Text style={styles.baseButtonText}>로그아웃</Text>
    </TouchableOpacity>
    <Routines routines={currentUserData?.recommendations}></Routines>
  </View>
  )
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  bigfont: {
    fontSize: 32,
    fontWeight: 'bold'
  },
  baseButton: {
    width: 400,
    borderRadius: 28,
    backgroundColor: COLORS.user,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 40,
  },
  baseButtonText: {
    color: 'white',
    fontSize: 24,
    marginVertical: 12,
    marginHorizontal: 20
  },
  tabBar: {
    backgroundColor: '#E4E4E4',
  },
  bottomBar:{
    backgroundColor: COLORS.bar,
    justifyContent: 'center',
    paddingHorizontal: 20
  },
  bottomTitleContainer: {
    backgroundColor: '#00000030',
    height: 50,
    marginVertical: 16,
    borderRadius: 25,
    justifyContent: 'center',
    paddingLeft: 20
  },
  bottomBarText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold'
  },
  routineContainer: {
    padding: 20,
    borderWidth: 4,
    borderRadius: 32,
    borderColor: COLORS.user,
  }


});
export default MainScreen;