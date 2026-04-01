import React, { useEffect, useReducer } from 'react';
import {useState} from 'react';
import {StyleSheet,View, Text, Button, TextInput ,FlatList, ListRenderItem, Image,} from 'react-native';
import {BottomBarProvider, useBottomBar} from './BottomBarContext';
import ChatInput from './ChatInput';
import SurveyInput from './SurveyInput';
import { useIsFocused } from '@react-navigation/native';
import { get } from 'react-native/Libraries/TurboModule/TurboModuleRegistry';
import { COLORS } from './assets/Maincolors';
import ResultModal, { SurveyResult } from './ResultModal';


//메세지 구조 잡기
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  time: string;
}

//임시 메세지 데이터들
const MOCK_MESSAGES: Message[] = [
    {id: '1', text: "상대방 매세지", sender: 'ai', time: '오전 10:00'},
    {id: '2', text: "나의 메세지", sender: 'user', time: '오전 11:00'},
    //{id: '3', text: `{"type": "select", "title": "질문 내용", "detail": ["옵션1", "옵션2", "옵션3"]}`, sender: 'ai', time: '오전 12:00'},
    {id: '3', text: `{"is_finished": true,"result_emoji": "🐢","result_name": "조용히 숨 고르는 거북이"}`, sender: 'ai', time: '오전 12:00'},
];


//채팅 화면 컴포넌트
const ChatScreen = () => {
  const isFocused = useIsFocused();//현재 화면이 포커스 되어있는지 확인
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const lastMessage = messages[messages.length - 1];//마지막 메세지 가져오기
  const [surveyResult, setSurveyResult] = useState<SurveyResult | null>(null);
  const [inputText, setInputText] = useState<string>('');
  const [modalVisible, setModalVisible] = useState(false);


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
    try{
      const response = await fetch('http://127.0.0.1:8000/docs', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: inputText, history: messages}),
      });
       console.log('보냈음', response);
      //ai 응답 후 메세지 보내는 함수
      const aiResponse = await response.json();
      const aimag: Message = {
        id: (MOCK_MESSAGES.length + 1).toString(),
        text: aiResponse.message,
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
        setBottomBarContent(<ChatInput onSend={(inputText) => {handleSendMessage(inputText);}}/>);
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

  
  //메세지 렌더링 컴포넌트
  const renderMessages: ListRenderItem<Message> = ({item}: {item: Message}) => {
    //설문 데이터인지 판별하는거 다시만듬
    let surveyData = null;
    if (item.sender === 'ai' && item.text.includes(`{"type": "select"`)) {
      try {
        surveyData = JSON.parse(item.text);
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
    />
    <ResultModal isVisible={modalVisible} data={surveyResult} onClose={() => setModalVisible(false)}/>
  </View>
  );
};

//스타일 시트



const styles = StyleSheet.create({
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
        paddingVertical: 4,
        shadowOffset: {width: 0, height: 2},
        bottom: 12
    },
    profileImage:{
      width: 64,
      height: 64,
      borderRadius: 32,
    },
    userText: {
        fontSize: 16,
        color: 'white'
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
        color: 'black'
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