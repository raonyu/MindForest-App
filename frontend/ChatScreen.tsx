import React, { useEffect, useReducer, useRef } from 'react';
import {useState} from 'react';
import { useRoute } from '@react-navigation/native';
import {StyleSheet,View, Text, Button, TextInput ,FlatList, ListRenderItem, Image, Keyboard, Platform} from 'react-native';
import {BottomBarProvider, useBottomBar} from './BottomBarContext';
import ChatInput from './ChatInput';
import SurveyInput from './SurveyInput';
import { useIsFocused } from '@react-navigation/native';
import { get } from 'react-native/Libraries/TurboModule/TurboModuleRegistry';
import { COLORS } from './assets/Maincolors';
import ResultModal, { SurveyResult } from './ResultModal';
import { useMainContext } from './MainContext';


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
  {
    id: '2',
    text: '"벌써 기가 빨려..." 이불 속으로 다시 들어가고 싶다.',
    sender: 'user',
    time: '오전 10:01'
  },
  {
    id: '3',
    text: '{"type": "select", "title": "2. 기분이 갑자기 롤러코스터처럼 오르락내리락할 때 나는?", "detail": ["나도 내 마음을 몰라 혼란스럽고 충동적인 행동을 한다.", "겉으로는 꾹 참고 숨기지만, 속으로는 심장이 쿵쾅거린다.", "감정이 터질 것 같아 주변에 뾰족하게 반응하거나 화를 낸다."]}',
    sender: 'ai',
    time: '오전 10:02'
  },
  {
    id: '4',
    text: '겉으로는 꾹 참고 숨기지만, 속으로는 심장이 쿵쾅거린다.',
    sender: 'user',
    time: '오전 10:03'
  },
  // ... 중략 (3번 ~ 19번 문항 진행) ...
  {
    id: '39',
    text: '{"type": "select", "title": "20. 마음의 숲에서 내가 찾고 싶은 장소는 어디일까?", "detail": ["아무도 나를 해칠 수 없는 푹신하고 안전한 오두막.", "모든 나무와 꽃이 규칙적으로 정돈된 깔끔한 정원.", "어디로 튈지 모르는 생물들이 가득한 모험의 숲."]}',
    sender: 'ai',
    time: '오전 10:20'
  },
  {
    id: '40',
    text: '아무도 나를 해칠 수 없는 푹신하고 안전한 오두막.',
    sender: 'user',
    time: '오전 10:21'
  },
  {
    id: '41',
    text: '{"is_finished": true, "result_emoji": "🐢", "result_name": "조용히 숨 고르는 거북이"}',
    sender: 'ai',
    time: '오전 10:21'
  }
];

//채팅 화면 컴포넌트
const ChatScreen = () => {
  const isFocused = useIsFocused();//현재 화면이 포커스 되어있는지 확인
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const route: any = useRoute();
  const lastMessage = messages[messages.length - 1];//마지막 메세지 가져오기
  const [surveyResult, setSurveyResult] = useState<SurveyResult | null>(null);
  const [inputText, setInputText] = useState<string>('');
  const [modalVisible, setModalVisible] = useState(false);
  const {user} = useMainContext();


  //백앤드 메세지 요청/응답 함수
  const handleSendMessage = async (inputText: string) => {
    //유저 메세지 보내기
    const userMsg: Message = {
      id: (MOCK_MESSAGES.length + 1).toString(),
      text: inputText,
      sender: 'user',
      time: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}),
    }
    setMessages(prev => [...prev, userMsg]);
    //백앤드로 메세지 보내고 응답 받기
    try{
      const response = await fetch('http://localhost:8000/api/chatbot/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_id: user.user_id, message: inputText}),
      });
       console.log('보냈음', response);
      //ai 응답 후 메세지 보내는 함수
      const aiResponse = await response.json();
      const aimag: Message = {
        id: (MOCK_MESSAGES.length + 1).toString(),
        text: aiResponse.reply_message,
        sender: 'ai',
        time: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}),
      };
      setMessages(prev => [...prev, aimag]);
    }catch (error){console.error('응답 실패', error);}
  } 


  //메세지 보내는 함수(메세지 데이터들에서 추가하는거)
  const sendMessages = (inputText: string) => {
    const newMessage: Message = {
      id: (messages.length + 1).toString(),
      text: inputText,
      sender: 'user',
      time: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}),
    };
    setMessages(prevMessages => [...prevMessages, newMessage]);
  };

  //설문데이터인지 판별하는 함수
  const getsurveyData = () => {
    if (lastMessage.sender !==`ai`) return null;
    try{
      if(lastMessage.text.includes(`{"type": "select"`)) {
        const aiJsonData = JSON.parse(lastMessage.text);
        return {title: aiJsonData.title, detail: aiJsonData.detail};
      }
    }catch (error){
      console.error('json 파싱 실패', error);
      return null;
    }
      return null;
  };

  //설문조사 데이터, 결과 등의 데이터 여부에 따라 이벤트 처리
  const { setBottomBarContent } = useBottomBar();
  useEffect(() => {
    if(isFocused){
      const surveyData = getsurveyData();
      if (surveyData){//설문데이터일 시 -> 하단바를 설문 입력창으로 변경
        setBottomBarContent(
          <SurveyInput
          title={surveyData.title}
          options={surveyData.detail}
          onSelect={(value) => {sendMessages(value);}}/>
        )
      }else if(lastMessage.sender === 'ai' && lastMessage.text.includes(`"is_finished": true`)){//결과 데이터일 시 -> 하단바를 결과 모달로 변경
        try{
          const parsedData = JSON.parse(lastMessage.text);
          setSurveyResult(parsedData);
          setModalVisible(true);
          console.log('결과 데이터 파싱 성공', parsedData);
        }catch (error){
          console.error('json 파싱 실패', error);
        }
        setBottomBarContent(<ChatInput onSend={(inputText) => {sendMessages(inputText);}}/>);
      }else{//그 이외에는 일반 채팅을 보여줌
        setBottomBarContent(
          <ChatInput
          onSend={(inputText) => {handleSendMessage(inputText);
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
      try{
        // @ts-ignore
        flatListRef.current.scrollToEnd({ animated: true });
      }catch(e){/* ignore */}
    }
  }, [messages, keyboardHeight]);

  
  //메세지 렌더링 컴포넌트
  const renderMessages: ListRenderItem<Message> = ({item}: {item: Message}) => {
    //json 데이터 판별
    let surveyData = null;
    if (item.sender === 'ai' && item.text.includes(`{"type": "select"`)) {//설문데이터일경우
      try {
        surveyData = JSON.parse(item.text);
      } catch (error) {
        console.error('json 파싱 실패', error);
      }
    }else if (item.sender === 'ai' && item.text.includes(`"is_finished": true`)) {//결과데이터일경우
        try {
          surveyData = JSON.parse(item.text);
          console.log('결과 데이터 파싱 성공', surveyData);
        } catch (error) {
          console.error('json 파싱 실패', error);
        }
    }

    return(
    <View style={[styles.messageContainer, item.sender === 'user'? {flexDirection: 'row'} : {flexDirection: 'row-reverse'}]}>
      {/** 프로필 이미지 영역*/}
      <View style={[item.sender === 'user' ? styles.userChatting : styles.otherChatting]}>
        {item.sender === 'ai' && <Image source={require('./assets/profile_icon.png')} style = {[styles.profileImage,styles.otherProfileImage]}/>}
        {item.sender === 'user' && <Image source={require('./assets/profile_icon.png')} style = {[styles.profileImage,styles.userProfileImage]}/>}
      </View>
      {/*메세지 말풍선 영역*/}
      <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.otherBubble]}>
        <Text style={[item.sender === 'user' ? styles.userText : styles.otherText]}>
          {surveyData ? surveyData.title : item.text}{/* 설문조사 JSON 데이터일 경우 title부분을 표시함*/}
        </Text>
        <Text style={{fontSize: 12, color: 'gray'}}>{item.time}</Text>
        {item.sender === 'user' && <View style={styles.userArrow}/>}
        {item.sender === 'ai' && <View style={styles.otherArrow}/>}
      </View>
    </View>
    );
  };

  //최종 스크린 보여주기
  return (
  <View>
    <Text>채팅 화면이 뜰겁니다</Text>
    <FlatList<Message>
      data={messages}
      renderItem= {renderMessages}
      keyExtractor={item => item.id}
      style={styles.list}
      contentContainerStyle={[styles.listContent, {paddingBottom: 24 + keyboardHeight}]}
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="interactive"
      ref={(ref) => { /* @ts-ignore */ flatListRef.current = ref }}
    />
    <ResultModal isVisible={modalVisible} data={surveyResult} onClose={() => setModalVisible(false)}/>
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
    messageContainer: {//프로필 + 말풍선 컨테이너
        marginVertical: 8,
        marginHorizontal: 16,
        display: 'flex',
        alignItems: 'flex-end',
        gap: 20,
    },
    messageBubble: {//공통 말풍선 스타일
        borderRadius: 12,
        paddingHorizontal: 16,
        paddingVertical: 8,
        shadowOffset: {width: 0, height: 2},
        marginVertical: 4,
        maxWidth: '75%',
        flexShrink: 1,
    },
    profileImage:{
      width: 64,
      height: 64,
      borderRadius: 32,
    },
    userText: {
      fontSize: 16,
      color: 'white',
      flexWrap: 'wrap',
      flexShrink: 1,
    },
    userChatting: {
        flexDirection: 'row',
    },
    userProfileImage: {
    },
    userBubble: {
        alignSelf: 'flex-start',
        backgroundColor: COLORS.user
    },
    userArrow: {//화살표 만들기
        position: 'absolute',
        bottom: 0,
        left: -10,
        width: 0,
        height: 0,
        backgroundColor: 'transparent',
        borderStyle: 'solid',
        borderTopWidth: 10,
        borderLeftWidth : 10,
        borderRightWidth: 10,
        borderBottomWidth: 10,
        
        borderTopColor: 'transparent',
        borderLeftColor: 'transparent',
        borderRightColor: 'transparent',
        borderBottomColor: COLORS.user,
    },

    otherText: {
      fontSize: 16,
      color: 'black',
      flexWrap: 'wrap',
      flexShrink: 1,
    },
    otherChatting: {
        flexDirection: 'row-reverse',
    },
    otherProfileImage: {
    },
    otherBubble: {
        alignSelf: 'flex-end',
        backgroundColor: COLORS.other
    },
    otherArrow: {
        position: 'absolute',
        bottom: 0,
        right: -10,
        width: 0,
        height: 0,
        backgroundColor: 'transparent',
        borderStyle: 'solid',
        borderTopWidth: 10,
        borderLeftWidth : 10,
        borderRightWidth: 10,
        borderBottomWidth: 10,
        
        borderTopColor: 'transparent',
        borderLeftColor: 'transparent',
        borderRightColor: 'transparent',
        borderBottomColor: COLORS.other,
    }
});





export default ChatScreen;