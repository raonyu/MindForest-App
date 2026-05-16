import React, { useEffect, useReducer, useRef } from 'react';
import { useState } from 'react';
import { useRoute } from '@react-navigation/native';
import { StyleSheet, View, Text, Button, TextInput, FlatList, ListRenderItem, Image, Keyboard, Platform } from 'react-native';
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
  {
    id: '1',
    text: '{"type": "select", "title": "1. 아침에 눈을 떴을 때, 오늘 하루의 일정이 꽉 차 있다면?", "detail": ["\\"벌써 기가 빨려...\\" 이불 속으로 다시 들어가고 싶다.", "\\"시간 단위로 쪼개야 해!\\" 머릿속으로 완벽한 시뮬레이션을 돌린다.", "\\"일단 부딪혀!\\" 막상 나가면 어떻게든 흘러가겠지 생각한다."]}',
    sender: 'ai',
    time: '오전 10:00'
  },
];

//채팅 화면 컴포넌트
const ChatScreen = () => {
  const isFocused = useIsFocused();//현재 화면이 포커스 되어있는지 확인
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const route: any = useRoute();
  const lastMessage = messages[messages.length - 1];//마지막 메세지 가져오기
  const flatListRef = useRef<FlatList<Message> | null>(null);
  const [keyboardHeight, setKeyboardHeight] = useState<number>(0);
  const [surveyResult, setSurveyResult] = useState<SurveyResult | null>(null);
  const [inputText, setInputText] = useState<string>('');
  const [modalVisible, setModalVisible] = useState(false);
  const { user } = useMainContext();



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
      const aimag: Message = {
        id: (MOCK_MESSAGES.length + 1).toString(),
        text: aiResponse.reply_message,
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


  //설문데이터인지 판별하는 함수
  const getsurveyData = () => {
    if (lastMessage.sender !== `ai`) return null;
    try {
      if (lastMessage.text.includes(`{"type": "select"`)) {
        const aiJsonData = JSON.parse(lastMessage.text);
        return { title: aiJsonData.title, detail: aiJsonData.detail };
      }
    } catch (error) {
      console.error('json 파싱 실패', error);
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
            onSelect={(value) => { sendMessages(value); }} />
        )
      } else if (lastMessage.sender === 'ai' && lastMessage.text.includes(`"is_finished": true`)) {//결과 데이터일 시 -> 하단바를 결과 모달로 변경
        try {
          const parsedData = JSON.parse(lastMessage.text);
          setSurveyResult(parsedData);
          setModalVisible(true);
          console.log('결과 데이터 파싱 성공', parsedData);
        } catch (error) {
          console.error('json 파싱 실패', error);
        }
        setBottomBarContent(<ChatInput onSend={(inputText) => { sendMessages(inputText); }} />);
      } else {//그 이외에는 일반 채팅을 보여줌
        setBottomBarContent(
          <ChatInput
            onSend={(inputText) => {
              handleSendMessage(inputText);
            }}
          />
        );
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


  //메세지 렌더링 컴포넌트
  const renderMessages: ListRenderItem<Message> = ({ item }: { item: Message }) => {
    //json 데이터 판별
    let surveyData = null;
    if (item.sender === 'ai' && item.text.includes(`{"type": "select"`)) {//설문데이터일경우
      try {
        surveyData = JSON.parse(item.text);
      } catch (error) {
        console.error('json 파싱 실패', error);
      }
    } else if (item.sender === 'ai' && item.text.includes(`"is_finished": true`)) {//결과데이터일경우
      try {
        surveyData = JSON.parse(item.text);
        console.log('결과 데이터 파싱 성공', surveyData);
      } catch (error) {
        console.error('json 파싱 실패', error);
      }
    }

    const isUser = item.sender === 'user';
    return (
      <View style={[styles.messageContainer, isUser ? styles.userRow : styles.aiRow]}>
        {/** 프로필 이미지 영역 (AI만 표시)*/}
        {!isUser && (
          <View style={styles.profileWrapper}>
            <Image source={require('./assets/profile_icon.png')} style={styles.profileImage} />
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
  }
});

export default ChatScreen;