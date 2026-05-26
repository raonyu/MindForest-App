import React, { useEffect, useReducer, useRef } from 'react';
import { useState } from 'react';
import { useRoute, useNavigation, } from '@react-navigation/native';
import { StyleSheet, View, Text, Button, TextInput, FlatList, ListRenderItem, Image, Keyboard, Platform, TouchableOpacity } from 'react-native';
import { BottomBarProvider, useBottomBar } from './BottomBarContext';
import ChatInput from './ChatInput';
import SurveyInput from './SurveyInput';
import { useIsFocused } from '@react-navigation/native';
import { get } from 'react-native/Libraries/TurboModule/TurboModuleRegistry';
import { COLORS } from './assets/Maincolors';
import ResultModal, { SurveyResult } from './ResultModal';
import { useMainContext } from './MainContext';
import { API_BASE_URL } from './config';


//메세지 구조 잡기
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  time: string;
}



//임시 메세지 데이터들
/*
const MOCK_MESSAGES: Message[] = [
    {id: '1', text: "상대방 매세지", sender: 'ai', time: '오전 10:00'},
    {id: '2', text: "나의 메세지", sender: 'user', time: '오전 11:00'},
    //{id: '3', text: `{"type": "select", "title": "질문 내용", "detail": ["옵션1", "옵션2", "옵션3"]}`, sender: 'ai', time: '오전 12:00'},
    {id: '3', text: `{"is_finished": true,"result_emoji": "🐢","result_name": "조용히 숨 고르는 거북이"}`, sender: 'ai', time: '오전 12:00'},
];
*/
const MOCK_MESSAGES: Message[] = [
  { id: '1', text: "상대방 매세지", sender: 'ai', time: '오전 10:00' },
  { id: '3', text: `{"is_finished": true,"result_emoji": "🐢","result_name": "조용히 숨 고르는 거북이"}`, sender: 'ai', time: '오전 12:00' }
];

// 흔하게 발생하는 챗봇의 JSON 생성 오류(마크다운, 잉여 괄호, 오탈자 등)를 복구하여 파싱하는 헬퍼 함수
const parseRobustJSON = (text: string) => {
  if (!text) return null;
  let cleanText = text.trim();
  // 마크다운 블록 제거 (```json ... ```)
  cleanText = cleanText.replace(/^```json\s*/i, '').replace(/```\s*$/i, '').trim();

  try {
    return JSON.parse(cleanText);
  } catch (e) {
    // 앞뒤 잉여 문자로 인한 오류일 경우, '{' 와 '}' 사이의 부분만 추출 시도
    const startIdx = cleanText.indexOf('{');
    let endIdx = cleanText.lastIndexOf('}');

    while (startIdx !== -1 && endIdx > startIdx) {
      try {
        const candidate = cleanText.substring(startIdx, endIdx + 1);
        return JSON.parse(candidate);
      } catch (err) {
        // 실패 시 그 전의 '}'를 찾아서 다시 시도
        endIdx = cleanText.lastIndexOf('}', endIdx - 1);
      }
    }
  }
  return null;
};

// 결과 말풍선 커스텀 컴포넌트
const ResultBubble = ({ data, onPress }: { data: any; onPress: () => void }) => (
  <TouchableOpacity
    activeOpacity={0.8}
    onPress={onPress}
    style={styles.resultBubbleContainer}
  >
    <Text style={styles.resultBubbleEmoji}>{data.result_emoji}</Text>
    <View style={styles.resultBubbleTextWrapper}>
      <Text style={styles.resultBubbleTitle}>심리검사 완료</Text>
      <Text style={styles.resultBubbleName}>{data.result_name}</Text>
      <Text style={styles.resultBubbleHint}>눌러서 결과 확인하기</Text>
    </View>
  </TouchableOpacity>
);

//채팅 화면 컴포넌트
const ChatScreen = () => {
  const isFocused = useIsFocused();//현재 화면이 포커스 되어있는지 확인
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const route: any = useRoute();
  const navigation: any = useNavigation();
  const lastMessage = messages[messages.length - 1];//마지막 메세지 가져오기
  const flatListRef = useRef<FlatList<Message> | null>(null);
  const [keyboardHeight, setKeyboardHeight] = useState<number>(0);
  const [surveyResult, setSurveyResult] = useState<SurveyResult | null>(null);
  const [inputText, setInputText] = useState<string>('');
  const [modalVisible, setModalVisible] = useState(false);
  const { user } = useMainContext();

  // 설문조사 모드 관련 상태
  const [surveyMode, setSurveyMode] = useState(false);
  const [surveyQuestions, setSurveyQuestions] = useState<any[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [surveyAnswers, setSurveyAnswers] = useState<any[]>([]);
  const [surveyType, setSurveyType] = useState<string>('');

  // 동물 데이터 리스트
  const [animalList, setAnimalList] = useState<any[]>([]);

  // 최초 진입 시 자동 메세지 전송 & 유형 설문조사 시작 확인
  useEffect(() => {
    if (route.params?.initialMessage) {
      const msg = route.params.initialMessage;
      // 중복 전송을 막기 위해 파라미터 초기화
      navigation.setParams({ initialMessage: undefined });
      handleSendMessage(msg);
    }

    // 유형 설문조사 모드 진입
    if (route.params?.surveyMode && route.params?.surveyQuestions) {
      setSurveyMode(true);
      setSurveyQuestions(route.params.surveyQuestions);
      setSurveyType(route.params.surveyType);
      setCurrentQuestionIndex(0);
      setSurveyAnswers([]);

      // 파라미터 지우기 (무한 루프 방지)
      navigation.setParams({ surveyMode: undefined, surveyQuestions: undefined, surveyType: undefined });

      // 첫 번째 질문 띄우기
      const firstQ = route.params.surveyQuestions[0];
      const aimag: Message = {
        id: Date.now().toString(),
        text: JSON.stringify({
          type: "select",
          title: `[유형 설문조사] ${firstQ.question_num}. ${firstQ.question_text}`,
          detail: ["매우 그렇다", "그렇다", "그렇지 않다", "매우 그렇지 않다"]
        }),
        sender: 'ai',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, aimag]);
    }

    // 동물 도감 데이터 불러오기
    const fetchAnimals = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/animal/all`);
        if (response.ok) {
          const data = await response.json();
          setAnimalList(data);
        }
      } catch (e) {
        console.error("동물 데이터 불러오기 실패:", e);
      }
    };
    fetchAnimals();

  }, [route.params?.initialMessage, route.params?.surveyMode]);

  //백앤드 메세지 요청/응답 함수
  const handleSendMessage = async (inputText: string) => {
    //유저 메세지 보내기
    const userMsg: Message = {
      id: (MOCK_MESSAGES.length + 1).toString(),
      text: inputText,
      sender: 'user',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages(prev => [...prev, userMsg]);
    //백앤드로 메세지 보내고 응답 받기
    try {
      const response = await fetch(`${API_BASE_URL}/api/chatbot/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.user_id, message: inputText }),
      });
      console.log('보냈음', response);
      //ai 응답 후 메세지 보내는 함수
      const aiResponse = await response.json();
      // aiResponse가 설문/결과 객체 자체인지 확인 (reply_message가 없는 경우 대비)
      let replyText = aiResponse.reply_message;
      if (!replyText && (aiResponse.type === 'select' || aiResponse.is_finished)) {
        replyText = JSON.stringify(aiResponse);
      }

      const aimag: Message = {
        id: (MOCK_MESSAGES.length + 1).toString(),
        text: replyText || '응답을 받아오지 못했습니다.', // fallback text
        sender: 'ai',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, aimag]);
    } catch (error) { console.error('응답 실패', error); }
  }


  //메세지 보내는 함수(메세지 데이터들에서 추가하는거)
  const sendMessages = (inputText: string) => {
    const newMessage: Message = {
      id: (messages.length + 1).toString(),
      text: inputText,
      sender: 'user',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prevMessages => [...prevMessages, newMessage]);

  };

  // 자체 설문조사 모드 응답 처리기
  const handleSurveyAnswer = async (value: string) => {
    // 1. 유저 선택지를 화면에 표시
    const userMsg: Message = {
      id: Date.now().toString(),
      text: value,
      sender: 'user',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);

    // 2. 점수 매핑
    let score = 0;
    if (value === "매우 그렇다") score = 3;
    else if (value === "그렇다") score = 2;
    else if (value === "그렇지 않다") score = 1;
    else if (value === "매우 그렇지 않다") score = 0;

    const currentQ = surveyQuestions[currentQuestionIndex];
    const newAnswers = [...surveyAnswers, { question_num: currentQ.question_num, answer: score }];
    setSurveyAnswers(newAnswers);

    const nextIndex = currentQuestionIndex + 1;
    setCurrentQuestionIndex(nextIndex);

    // 3. 다음 질문 혹은 제출
    if (nextIndex < surveyQuestions.length) {
      const nextQ = surveyQuestions[nextIndex];
      const aimag: Message = {
        id: (Date.now() + 1).toString(),
        text: JSON.stringify({
          type: "select",
          title: `[유형 설문조사] ${nextQ.question_num}. ${nextQ.question_text}`,
          detail: ["매우 그렇다", "그렇다", "그렇지 않다", "매우 그렇지 않다"]
        }),
        sender: 'ai',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, aimag]);
    } else {
      // 모든 문항 완료 시 제출
      try {
        const payload = {
          user_id: user.user_id,
          survey_type: surveyType,
          answers: newAnswers
        };
        const response = await fetch(`${API_BASE_URL}/api/survey/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (response.ok) {
          const doneMsg: Message = {
            id: (Date.now() + 1).toString(),
            text: "수고하셨습니다. 설문조사가 성공적으로 제출되었습니다!",
            sender: 'ai',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
          setMessages(prev => [...prev, doneMsg]);
          setSurveyMode(false); // 설문 모드 종료
        } else {
          console.error("설문 제출 실패");
          const errMsg: Message = {
            id: (Date.now() + 1).toString(),
            text: "설문 제출에 실패했습니다. 다시 시도해주세요.",
            sender: 'ai',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
          setMessages(prev => [...prev, errMsg]);
        }
      } catch (err) {
        console.error("설문 제출 오류", err);
      }
    }
  };

  //설문데이터인지 판별하는 함수
  const getsurveyData = () => {
    if (lastMessage.sender !== `ai` || !lastMessage.text) return null;
    try {
      const aiJsonData = parseRobustJSON(lastMessage.text);
      if (aiJsonData && aiJsonData.type === 'select') {
        return { title: aiJsonData.title, detail: aiJsonData.detail };
      }
    } catch (error) {
      // 일반 텍스트이거나 JSON 파싱 실패인 경우
      return null;
    }
    return null;
  };


  //설문조사 데이터, 결과 등의 데이터 여부에 따라 이벤트 처리
  const { setBottomBarContent } = useBottomBar();
  useEffect(() => {
    if (isFocused) {
      const surveyData = getsurveyData();
      if (surveyData) {//설문데이터일 시 -> 하단바를 설문 입력창으로 변경
        setBottomBarContent(
          <SurveyInput
            title={surveyData.title}
            options={surveyData.detail}
            onSelect={(value) => {
              if (surveyMode) {
                handleSurveyAnswer(value);
              } else {
                handleSendMessage(value);
              }
            }} />
        )
      } else {
        let isResultData = false;
        if (lastMessage.sender === 'ai' && lastMessage.text) {
          try {
            const parsedData = parseRobustJSON(lastMessage.text);
            if (parsedData && parsedData.is_finished === true) {
              isResultData = true;
              console.log('결과 데이터 파싱 성공', parsedData);
              setBottomBarContent(<ChatInput onSend={(inputText) => { handleSendMessage(inputText); }} />);
            }
          } catch (error) {
            // 일반 텍스트
          }
        }

        if (!isResultData) {//그 이외에는 일반 채팅을 보여줌
          if (surveyMode) {
            // 설문조사 모드 진행 중에는 임의 텍스트 입력을 막음
            setBottomBarContent(null);
          } else {
            setBottomBarContent(
              <ChatInput
                onSend={(inputText) => {
                  handleSendMessage(inputText);
                }}
              />
            );
          }
        }
      }
      //다른 화면으로 전환 시 하단바 초기화
      return () => setBottomBarContent(null);
    }
  }, [isFocused, messages]);//포커싱, 메세지 데이터 여부에 따라 재랜더링

  // 키보드 이벤트: 키보드가 열리면 FlatList가 위로 올라가도록 패딩 조정
  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvent, (e: any) => {
      setKeyboardHeight(e.endCoordinates ? e.endCoordinates.height : 300);
    });
    const hideSub = Keyboard.addListener(hideEvent, () => setKeyboardHeight(0));
    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, []);

  // 새 메시지 추가 시 자동 스크롤
  useEffect(() => {
    if (flatListRef.current) {
      try {
        // @ts-ignore
        flatListRef.current.scrollToEnd({ animated: true });
      } catch (e) {/* ignore */ }
    }
  }, [messages, keyboardHeight]);


  const renderMessages: ListRenderItem<Message> = ({ item }: { item: Message }) => {
    //json 데이터 판별
    let surveyData = null;
    if (item.sender === 'ai' && item.text) {
      try {
        const parsedData = parseRobustJSON(item.text);
        if (parsedData && (parsedData.type === 'select' || parsedData.is_finished === true)) {
          surveyData = parsedData;
        }
      } catch (error) {
        // 일반 텍스트
      }
    }

    const isUser = item.sender === 'user';

    // 결과 말풍선인 경우 독립적으로 분리하여 렌더링
    if (surveyData && surveyData.is_finished === true) {
      // 동물 데이터를 기반으로 이모지와 이름 매핑
      let finalEmoji = surveyData.result_emoji;
      let finalName = surveyData.result_name;

      if (surveyData.category && animalList.length > 0) {
        const matchedAnimal = animalList.find(a => a.category === surveyData.category);
        if (matchedAnimal) {
          finalEmoji = matchedAnimal.emoji;
          finalName = matchedAnimal.name;
        }
      }

      const displayData = {
        ...surveyData,
        result_emoji: finalEmoji || '🌱',
        result_name: finalName || '결과를 분석 중입니다...',
      };

      return (
        <View style={[styles.messageContainer, styles.aiRow]}>
          <View style={styles.profileWrapper}>
            <View style={[styles.profileImage, { justifyContent: 'center', alignItems: 'center' }]}>
              <Text style={{ fontSize: 24 }}>{user?.animal_emoji || '🌱'}</Text>
            </View>
          </View>
          <View style={styles.bubbleAndTime}>
            <ResultBubble
              data={displayData}
              onPress={() => {
                setSurveyResult(displayData);
                setModalVisible(true);
              }}
            />
            <Text style={[styles.timeText, styles.timeTextAi]}>{item.time}</Text>
          </View>
        </View>
      );
    }

    // 일반 텍스트 또는 일반 설문 문항 렌더링
    return (
      <View style={[styles.messageContainer, isUser ? styles.userRow : styles.aiRow]}>
        {/** 프로필 이미지 영역 (AI만 표시)*/}
        {!isUser && (
          <View style={styles.profileWrapper}>
            <View style={[styles.profileImage, { justifyContent: 'center', alignItems: 'center' }]}>
              <Text style={{ fontSize: 24 }}>{user?.animal_emoji || '🌱'}</Text>
            </View>
          </View>
        )}

        <View style={styles.bubbleAndTime}>
          {/*메세지 말풍선 영역*/}
          <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.aiBubble]}>
            <Text style={[styles.messageText, isUser ? styles.userText : styles.aiText]}>
              {surveyData ? surveyData.title : item.text}
            </Text>
          </View>
          {/*시간*/}
          <Text style={[styles.timeText, isUser ? styles.timeTextUser : styles.timeTextAi]}>{item.time}</Text>
        </View>
      </View>
    );
  };

  //최종 스크린 보여주기
  return (
    <View style={styles.container}>
      <Text style={styles.screenTitle}>채팅 화면</Text>
      <FlatList<Message>
        data={messages}
        renderItem={renderMessages}
        keyExtractor={item => item.id}
        style={styles.list}
        contentContainerStyle={[styles.listContent, { paddingBottom: 24 + keyboardHeight }]}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        ref={(ref) => { /* @ts-ignore */ flatListRef.current = ref }}
      />
      <ResultModal isVisible={modalVisible} data={surveyResult} onClose={() => setModalVisible(false)} />
    </View>
  );
};



//스타일 시트
const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingBottom: 100, // 하단바가 고정일 때 내용이 가려지지 않도록 여유를 둠
  },
  screenTitle: {
    fontSize: 14,
    color: '#333',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  list: {
    flex: 1,
  },
  listContent: {
    paddingHorizontal: 8,
    paddingTop: 8,
    paddingBottom: 24,
  },
  messageContainer: {
    marginVertical: 6,
    marginHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  aiRow: {
    justifyContent: 'flex-start',
  },
  profileWrapper: {
    marginRight: 10,
  },
  profileImage: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#eaffdf',
  },
  bubbleAndTime: {
    flexDirection: 'column',
    maxWidth: '75%',
  },
  messageBubble: {
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  userBubble: {
    backgroundColor: '#9ee779',
    borderTopRightRadius: 4,
    alignSelf: 'flex-end',
  },
  aiBubble: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 4,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#e2ebd9',
  },
  messageText: {
    fontSize: 15,
    fontFamily: 'NanumSquareRoundR',
    lineHeight: 22,
  },
  userText: {
    color: '#15210f',
  },
  aiText: {
    color: '#2a3a21',
  },
  timeText: {
    fontSize: 11,
    color: '#a0a88f',
    fontFamily: 'NanumSquareRoundR',
    marginTop: 4,
  },
  timeTextUser: {
    alignSelf: 'flex-end',
    marginRight: 4,
  },
  timeTextAi: {
    alignSelf: 'flex-start',
    marginLeft: 4,
  },
  resultBubbleContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 12,
    borderWidth: 1.5,
    borderColor: '#9ee779',
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultBubbleEmoji: {
    fontSize: 36,
    marginRight: 12,
  },
  resultBubbleTextWrapper: {
    flexShrink: 1,
  },
  resultBubbleTitle: {
    fontSize: 12,
    color: '#719e5b',
    fontFamily: 'NanumSquareRoundB',
    marginBottom: 2,
  },
  resultBubbleName: {
    fontSize: 15,
    color: '#15210f',
    fontFamily: 'NanumSquareRoundB',
    marginBottom: 4,
  },
  resultBubbleHint: {
    fontSize: 11,
    color: '#a0a88f',
    fontFamily: 'NanumSquareRoundR',
    textDecorationLine: 'underline',
  }
});

export default ChatScreen;