import React from 'react';
import {useState} from 'react';
import {StyleSheet,View, Text, FlatList, ListRenderItem} from 'react-native';


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
    {id: '2', text: "나의 메세지", sender: 'user', time: '오전 11:00'}
];


//각 화면 컴포넌트들(달력, 매인, 채팅) 
const ChatScreen = () => {
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const [inputText, setInputText] = useState<string>('');

  //메세지 렌더링 컴포넌트
  const renderMessages: ListRenderItem<Message> = ({item}: {item: Message}) => (
    <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.otherBubble]}>
      <Text style={styles.messageText}>{item.text}</Text>
      <Text>{item.time}</Text>
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
    userBubble: {
        alignSelf: 'flex-start',
        backgroundColor: '#84E291'
    },
    otherBubble: {
        alignSelf: 'flex-end',
        backgroundColor: '#047857'
    }
});





export default ChatScreen;