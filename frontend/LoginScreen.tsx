import React, { useEffect, useRef } from 'react';
import {useState} from 'react';
import { Animated, StatusBar, StyleSheet, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem, Alert, TextInput} from 'react-native';

const LoginScreen = ({ onLoginSuccess }: any) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const MOCK_USER = {
    id: "user_01",
    email: "asdf",
    password: "1234",
    is_onboarding_done: true,
    user_animal: "거북이",
    assigned_category: "안정형"
  };
  const startLogin = () =>{
    if (email === MOCK_USER.email && password === MOCK_USER.password){
      Alert.alert("로그인 성공", `환영합니다, ${MOCK_USER.user_animal}님!`);
      onLoginSuccess(MOCK_USER);
    }else{
      Alert.alert("로그인 실패", "이메일 또는 비밀번호가 올바르지 않습니다.");
    }
  }
  return(
    <View>
      <Text>로그인 화면</Text>
        <TextInput
          placeholder="이메일"
          value={email}
          onChangeText={setEmail}
        />
        <TextInput
          placeholder="비밀번호"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <TouchableOpacity onPress={startLogin}>
          <Text>로그인하기</Text>
        </TouchableOpacity>
    </View>
  )
}
export default LoginScreen;