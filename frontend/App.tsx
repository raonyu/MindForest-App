/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */
import React from 'react';
import {useState} from 'react';
import { StatusBar, StyleSheet, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';//네비게이션 라이브러리 불러오기
import {createMaterialTopTabNavigator} from '@react-navigation/material-top-tabs';

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
const MainScreen = () => (
  <View><Text>여기는 메인화면입니다</Text></View>
);
const DiaryScreen = () => (
  <View><Text>감정일기 달력 화면</Text></View>
);
//텝 컴포넌트 생성
const Tab = createMaterialTopTabNavigator();
//버튼 선언
const CustomButton = () =>(
  <TouchableOpacity style = {styles.baseButton}><Text>버튼임</Text></TouchableOpacity>


);

function App(){
  const isDarkMode = useColorScheme() === 'dark';

  return (
    <NavigationContainer>
      <Tab.Navigator initialRouteName = "마음의 숲"
                     screenOptions={{tabBarStyle: styles.tabBar,
                                    tabBarLabelStyle: {fontSize: 20, fontWeight: 'bold', color: 'white'},
                                    tabBarIndicatorStyle: {backgroundColor: 'white', height: 3},
                                    }}>     
        <Tab.Screen name="감정일기" component={DiaryScreen} />
        <Tab.Screen name="마음의 숲" component={MainScreen} />
        <Tab.Screen name="채팅" component={ChatScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  bigfont: {
    fontSize: 32,
    fontWeight: 'bold'
  },
  baseButton: {
    backgroundColor: "gray",
  },
  tabBar: {
    backgroundColor: 'green',
  }   
});




export default App;
