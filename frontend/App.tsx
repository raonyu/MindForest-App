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
//각 화면 컴포넌트 불러오기
import ChatScreen from './ChatScreen';


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
        <View style={styles.bottomBar}>
          <Text style={styles.bottomBarText}>커스텀텍스트</Text>
        </View>
      </NavigationContainer>
    </View>
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
