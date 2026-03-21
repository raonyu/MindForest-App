import React, { useEffect, useReducer } from 'react';
import {useState} from 'react';
import {StyleSheet,View, Text, Button, TextInput ,FlatList, ListRenderItem, Image} from 'react-native';
import {BottomBarProvider, useBottomBar} from './BottomBarContext';
import ChatInput from './ChatInput';
import SurveyInput from './SurveyInput';
import { useIsFocused } from '@react-navigation/native';

//메세지 구조 잡기
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  time: string;
  type: string;
  detail: string[];
}

//임시 메세지 데이터들
const MOCK_MESSAGES: Message[] = [
    {id: '1', text: "상대방 매세지", sender: 'ai', time: '오전 10:00', type: "text", detail: []},
    {id: '2', text: "나의 메세지", sender: 'user', time: '오전 11:00', type: "text", detail: []},
    {id: '3', text: "설문조사채팅임", sender: 'ai', time: '오전 12:00', type: "select", detail: ["옵션1", "옵션2", "옵션3"]},
];

//설문조사 데이터 확인(파싱)


//메세지 보내기 컴포넌트



//각 화면 컴포넌트들(달력, 매인, 채팅) 
const ChatScreen = () => {
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const [inputText, setInputText] = useState<string>('');
  const isFocused = useIsFocused();//현재 화면이 포커스 되어있는지 확인

  //메세지 보내는 함수(메세지 데이터들에서 추가하는거)
  const sendMessages = (inputText: string) => {
    const newMessage: Message = {
      id: (messages.length + 1).toString(),
      text: inputText,
      sender: 'user',
      time: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}),
      type: "text",
      detail: []
    };
    setMessages(prevMessages => [...prevMessages, newMessage]);
  };
  //하단바 채팅 입력창 생성
  const { setBottomBarContent } = useBottomBar();
  useEffect(() => {
    if(isFocused){
      const lastMessage = messages[messages.length - 1];
      const surveyData = lastMessage?.sender === 'ai' && lastMessage.type === 'select' ? {detail: lastMessage.detail, text: lastMessage.text} : null;

      if (surveyData){//설문데이터일 시
        setBottomBarContent(
          <SurveyInput
          title={surveyData.text}
          options={surveyData.detail}
          onSelect={(value) => {sendMessages(value);}}/>
        )
      }else{//그 이외에는 일반 채팅을 보여줌
        setBottomBarContent(
          <ChatInput
          onSend={(inputText) => {sendMessages(inputText);
          }}
          />
        );
      }
      //다른 화면으로 전환 시 하단바 초기화
      return () => setBottomBarContent(null);
    }
  }, [isFocused, messages]);//포커싱, 메세지 데이터 여부에 따라 재랜더링

  
  //메세지 렌더링 컴포넌트
  const renderMessages: ListRenderItem<Message> = ({item}: {item: Message}) => (
    <View>
      <View style={[item.sender === 'user' ? styles.userChatting : styles.otherChatting]}>
        {item.sender === 'ai' && <Image source={require('./assets/profile_icon.png')} style = {styles.otherProfileImage}/>}
        {item.sender === 'user' && <Image source={require('./assets/profile_icon.png')} style = {styles.userProfileImage}/>}
      </View>
      <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.otherBubble]}>
        <Text style={styles.messageText}>{item.text}</Text>
        <Text>{item.time}</Text>
      </View>
    </View>
  );

  //최종 스크린 보여주기
  return (
  <View>
    <Text>채팅 화면이 뜰겁니다</Text>
    <FlatList<Message>
      data={messages}
      renderItem= {renderMessages}
      keyExtractor={item => item.id}
    />
  </View>
  );
};

//스타일 시트
const styles = StyleSheet.create({
    messageBubble: {
        borderRadius: 15,
        padding: 10,
        shadowOffset: {width: 0, height: 2},
    },
    messageText: {
        fontSize: 16,
        color: 'white'
    },
    userChatting: {
        flexDirection: 'row',
    },
    userProfileImage: {
      width: 40,
      height: 40,
      borderRadius: 20,
    },
    userBubble: {
        alignSelf: 'flex-start',
        backgroundColor: '#84E291'
    },
    otherChatting: {
        flexDirection: 'row-reverse',
    },
    otherProfileImage: {
      width: 40,
      height: 40,
      borderRadius: 20,
    },
    otherBubble: {
        alignSelf: 'flex-end',
        backgroundColor: '#047857'
    }
});





export default ChatScreen;