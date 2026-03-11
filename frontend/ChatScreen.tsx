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
    <View>
      <Text>{item.text}</Text>
      <Text>{item.time}</Text>
    </View>
  );
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
export default ChatScreen;