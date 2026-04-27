/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */
import React, { useEffect, useRef , createContext, useContext, useState} from 'react';
import { Animated, StatusBar, StyleSheet, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';//네비게이션 라이브러리 불러오기
import {createMaterialTopTabNavigator} from '@react-navigation/material-top-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import {BottomBarProvider, useBottomBar} from './BottomBarContext';
import MainContext from './MainContext';

import { COLORS } from './assets/Maincolors';
import AsyncStorage from '@react-native-async-storage/async-storage';



//네비게이터 컴포넌트 생성
const Tab = createMaterialTopTabNavigator();
const Stack = createStackNavigator();

//하단바 컨텍스트 생성 및 애니메이션
const BottomBar = () => {
  const { BottomBar:content } = useBottomBar();
  const yPosAnim = useRef(new Animated.Value(100)).current;//하단바 애니메이션 초기위치 설정

  useEffect(() => {
    if (content){
      Animated.spring(yPosAnim, {toValue: 0, useNativeDriver: true}).start();
    }else{
      yPosAnim.setValue(100);
    }
  }, [content]);

  if (!content) return null;

  return (
  <Animated.View style={[styles.bottomBar, {transform: [{translateY: yPosAnim}]}]}>
    {content}
  </Animated.View>
  );
};


//각 화면 컴포넌트 불러오기
import LoginScreen from './LoginScreen';
import ChatScreen from './ChatScreen';
import DiaryScreen from './DiaryScreen';
import MainScreen from './MainScreen';




//마음의 숲 서비스 전체 서비스 화면
const ServiceScreen = () => (
  <BottomBarProvider>
    <View style={styles.container}>
        <Tab.Navigator initialRouteName = "마음의 숲"
                      screenOptions={{tabBarStyle: styles.tabBar,
                                      tabBarLabelStyle: {fontSize: 20, fontWeight: 'bold', color: 'black'},
                                      tabBarIndicatorStyle: {backgroundColor: '#00000013', height: 3},
                                      }}>     
          <Tab.Screen name="감정일기" component={DiaryScreen} />
          <Tab.Screen name="마음의 숲" component={MainScreen} />
          <Tab.Screen name="채팅" component={ChatScreen} />
        </Tab.Navigator>
        <BottomBar/>
    </View>
  </BottomBarProvider>
);

function App(){
  const isDarkMode = useColorScheme() === 'dark';
  const [user, setUser] = useState<any>(null);//사용자 정보 상태
  const [isLoading, setIsLoading] = useState(true);//로딩 상태 추적

  //사전에 로그인된 데이터가 있는지 채크
  useEffect(() =>{
    const checkLoginStatus = async() =>{
      try{
        const savedUser = await AsyncStorage.getItem('user_data');
        if(savedUser) setUser(JSON.parse(savedUser));
      }catch(e){
        console.error("데이터 불러오기 실패", e)
      }finally{
        setIsLoading(false);
      }
    }
    checkLoginStatus();
  }, [])
  //로그인 성공시 데이터 저장
  const handleLogin = async (userData:any)=>{
    try{
      await AsyncStorage.setItem('user_data', JSON.stringify(userData));
      setUser(userData);
    }catch(e){console.error("데이터 저장 실패", e)}
  }
  const handleLogOut = async () =>{
    await AsyncStorage.removeItem('user_data');
    setUser(null);
    console.log("로그아웃 되었습니다");
  }

  return (
    <MainContext.Provider value={{user, setUser, handleLogOut}}>
      <NavigationContainer>
        <Stack.Navigator>
          {user ? (<Stack.Screen name="메인서비스" component = {ServiceScreen} options={{headerShown: false}}/>
          ) :
          (<Stack.Screen name="로그인" >{(props: any) => <LoginScreen {...props} onLoginSuccess={handleLogin} />}</Stack.Screen>)
          }
        </Stack.Navigator>
      </NavigationContainer>
    </MainContext.Provider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  bigfont: {
    fontSize: 32,
    fontWeight: 'bold'
  },
  baseButton: {
    backgroundColor: "gray",
  },
  tabBar: {
    backgroundColor: '#E4E4E4',
  },
  bottomBar:{
    backgroundColor: COLORS.bar,
    justifyContent: 'center',
    paddingHorizontal: 20
  },
  bottomTitleContainer: {
    backgroundColor: '#00000030',
    height: 50,
    marginVertical: 16,
    borderRadius: 25,
    justifyContent: 'center',
    paddingLeft: 20
  },
  bottomBarText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold'
  }

});




export default App;
