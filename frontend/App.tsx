/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */
import React, { useEffect } from 'react';
import {useState} from 'react';
import { StatusBar, StyleSheet, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';//네비게이션 라이브러리 불러오기
import {createMaterialTopTabNavigator} from '@react-navigation/material-top-tabs';
import {BottomBarProvider, useBottomBar} from './BottomBarContext';
import { useIsFocused } from '@react-navigation/native';

//하단바 컨텍스트 생성
const BottomBar = () => {
  const { BottomBar:content } = useBottomBar();
  if (!content) return null;
  return (
  <View style={styles.bottomBar}>
    {content}
  </View>
  );
};




//각 화면 컴포넌트 불러오기
import ChatScreen from './ChatScreen';


const MainScreen = () => {
  const isFocused = useIsFocused();//현재 화면이 포커스 되어있는지 확인
  const { setBottomBarContent } = useBottomBar();
  useEffect(() => {
    //하단바 설정
    if(isFocused){
      setBottomBarContent(
        <View>
          <Text>메인화면임</Text>
        </View>
    );
    //다른 화면으로 전환 시 하단바 초기화
    return () => setBottomBarContent(null);
    } 
  }, [isFocused]);
  //메인 화면 내용
  return (
  <View>
    <Text>여기는 메인화면입니다</Text>
    <TouchableOpacity style={{height: 50, backgroundColor: 'gray', justifyContent: 'center', alignItems: 'center', marginTop: 20, borderRadius: 10  }}>
      <Text style={{color: 'white'}}>마음의 숲 사전 테스트 시작하기</Text>
    </TouchableOpacity>
  </View>)
};
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
    <BottomBarProvider>
    <View style={styles.container}>
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
          <BottomBar/>
      </NavigationContainer>
    </View>
    </BottomBarProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1
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
  },
  bottomBar:{
    backgroundColor: 'blue',
    height: 68,
    justifyContent: 'center',
    paddingHorizontal: 20
  },
  bottomBarText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold'
  }

});




export default App;
