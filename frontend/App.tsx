/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */
import React, { useEffect, useRef , createContext, useContext, useState} from 'react';
import { Animated, StatusBar, StyleSheet, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem, Platform, Keyboard } from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {createMaterialTopTabNavigator} from '@react-navigation/material-top-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import {BottomBarProvider, useBottomBar} from './BottomBarContext';
import MainContext from './MainContext';

import { COLORS } from './assets/Maincolors';
import AsyncStorage from '@react-native-async-storage/async-storage';
import LinearGradient from 'react-native-linear-gradient';

import Svg, { Defs, Pattern, Rect, Path as SvgPath } from 'react-native-svg';

//각 화면 컴포넌트 불러오기
import LoginScreen from './LoginScreen';
import ChatScreen from './ChatScreen';
import DiaryScreen from './DiaryScreen';
import MainScreen from './MainScreen';

const Tab = createMaterialTopTabNavigator();
const Stack = createStackNavigator();

//하단바 컨텍스트 생성 및 애니메이션
const BottomBar = () => {
  const { BottomBar:content } = useBottomBar();
  const yPosAnim = useRef(new Animated.Value(100)).current;
  const keyboardAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (content){
      Animated.spring(yPosAnim, {toValue: 0, useNativeDriver: true}).start();
    }else{
      yPosAnim.setValue(100);
    }
  }, [content]);

  // 키보드 이벤트로 바 위치 보정
  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvent, (e: any) => {
      const h = e.endCoordinates ? e.endCoordinates.height : 300;
      Animated.timing(keyboardAnim, {toValue: -h, duration: 200, useNativeDriver: true}).start();
    });
    const hideSub = Keyboard.addListener(hideEvent, () => {
      Animated.timing(keyboardAnim, {toValue: 0, duration: 200, useNativeDriver: true}).start();
    });
    return () => { showSub.remove(); hideSub.remove(); };
  }, []);

  if (!content) return null;

  return (
  <Animated.View style={[styles.bottomBar, {transform: [{translateY: Animated.add(yPosAnim, keyboardAnim)}]}]}>
    {content}
  </Animated.View>
  );
};


// 커스텀 탭바 컴포넌트 (밝은 애플 리퀴드 글래스 버전 🍎)
const CustomTopTabBar = ({ state, descriptors, navigation }: any) => {
  return (
    <View style={customTabStyles.wrapper}>
      {/* 💡 하얀색의 농도(Opacity)를 70~95%로 대폭 끌어올려서 어둡지 않고 뽀얀 유리 질감으로 변경! */}
      <LinearGradient
        colors={['rgba(255, 255, 255, 0.95)', 'rgba(255, 255, 255, 0.7)', 'rgba(255, 255, 255, 0.9)']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={customTabStyles.glassContainer}
      >
        {state.routes.map((route: any, index: number) => {
          const { options } = descriptors[route.key];
          const label = options.tabBarLabel !== undefined ? options.tabBarLabel : options.title !== undefined ? options.title : route.name;
          const isFocused = state.index === index;

          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });

            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate(route.name);
            }
          };

          return (
            <TouchableOpacity
              key={index}
              activeOpacity={0.8}
              onPress={onPress}
              style={customTabStyles.tabButton}
            >
              {isFocused ? (
                <LinearGradient
                  colors={['#cffff1', '#9ee779']} 
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={customTabStyles.activeTab}
                >
                  <Text style={customTabStyles.activeTabText}>{label}</Text>
                </LinearGradient>
              ) : (
                <View style={customTabStyles.inactiveTab}>
                  <Text style={customTabStyles.inactiveTabText}>{label}</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </LinearGradient>
    </View>
  );
};


//마음의 숲 서비스 전체 서비스 화면
const ServiceScreen = () => (
  <BottomBarProvider>
    <View style={styles.container}>
      
      {/* App 최상단에 모눈종이를 깔기 */}
      <View style={StyleSheet.absoluteFill}>
        <Svg width="100%" height="100%">
          <Defs>
            <Pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <Rect width="30" height="30" fill="#fafafa" />
              <SvgPath d="M 30 0 L 0 0 0 30" fill="none" stroke="#e6e6e6" strokeWidth="1" />
            </Pattern>
          </Defs>
          <Rect width="100%" height="100%" fill="url(#grid)" />
        </Svg>
      </View>

      <Tab.Navigator 
        initialRouteName="마음의 숲"
        tabBar={props => <CustomTopTabBar {...props} />}
        screenOptions={{ sceneStyle: { backgroundColor: 'transparent' } } as any}
      >     
        <Tab.Screen name="감정 일기" component={DiaryScreen} />
        <Tab.Screen name="마음의 숲" component={MainScreen} />
        <Tab.Screen name="채팅" component={ChatScreen} />
      </Tab.Navigator>
      <BottomBar/>
    </View>
  </BottomBarProvider>
);

function App(){
  const isDarkMode = useColorScheme() === 'dark';
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

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
          {user ? (
            <>
              <Stack.Screen name="메인서비스" component = {ServiceScreen} options={{headerShown: false}}/>
            </>
          ) : (
            <Stack.Screen name="로그인" options={{headerShown: false}}>{(props: any) => <LoginScreen {...props} onLoginSuccess={handleLogin} />}</Stack.Screen>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </MainContext.Provider>
  );
};

// --- 스타일 섹션 ---

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'transparent', 
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
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: COLORS.bar,
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    minHeight: 70,
    zIndex: 50,
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


const customTabStyles = StyleSheet.create({
  wrapper: {
    backgroundColor: 'transparent', 
    paddingTop: Platform.OS === 'ios' ? 60 : 30, 
    paddingBottom: 15,
    alignItems: 'center',
  },
  glassContainer: {
    flexDirection: 'row',
    width: '90%',
    height: 52,
    borderRadius: 26,
    padding: 6, 
    borderWidth: 1, // 💡 테두리를 살짝 더 두껍게 해서 유리의 두께감 표현
    borderColor: '#FFFFFF', // 💡 반투명이 아닌 100% 쨍한 흰색 테두리로 빛 반사(하이라이트) 극대화
    shadowColor: '#8E9E82',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15,
    shadowRadius: 15,
    elevation: 5,
  },
  tabButton: {
    flex: 1, 
  },
  activeTab: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 20, 
    shadowColor: '#9ee779',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  inactiveTab: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 20,
  },
  activeTabText: {
    fontFamily: 'NanumSquareRoundB', 
    fontSize: 15,
    color: '#15210f', 
  },
  inactiveTabText: {
    fontFamily: 'NanumSquareRoundB', 
    fontSize: 15,
    color: '#658a4e', 
  }
});


export default App;