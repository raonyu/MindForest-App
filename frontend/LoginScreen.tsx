import React, { useEffect, useRef } from 'react';
import {useState} from 'react';
import { Animated, StatusBar, StyleSheet, useColorScheme, View, Text, Pressable, TouchableOpacity, FlatList, ListRenderItem, Alert, TextInput} from 'react-native';
import { COLORS } from './assets/Maincolors';

const LoginScreen = ({ onLoginSuccess }: any) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const MOCK_USER = {
    user_id: "user_01",
    email: "asdf",
    password: "1234",
    is_onboarding_done: true,
    user_animal: "거북이",
    assigned_category: "안정형"
  };
  const mockStartLogin = () =>{
    if (email === MOCK_USER.email && password === MOCK_USER.password){
      Alert.alert("로그인 성공", `환영합니다, ${MOCK_USER.user_animal}님!`);
      onLoginSuccess(MOCK_USER);
    }else{
      Alert.alert("로그인 실패", "이메일 또는 비밀번호가 올바르지 않습니다.");
    }
  }
  const startLogin = async () =>{
    try{
      const responce = await fetch('http://localhost:8000/api/user/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: email, password: password}),
      });
      //로그인 실패 처리
      if (!responce.ok){
        const errorData = await responce.json();
        Alert.alert("로그인 실패", errorData.detail);
        return;
      }
      const userData = await responce.json();
      onLoginSuccess(userData);

    }catch(error){
      console.error('로그인 실패:', error);
    }
  }
  return(
    <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
      <Text style={{fontSize: 40, fontWeight: 'bold', marginBottom: 20}}>로그인</Text>
        <TextInput
          placeholder="이메일"
          value={email}
          onChangeText={setEmail}
          style={styles.inputtext}
        />
        <TextInput
          placeholder="비밀번호"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.inputtext}
        />
        <TouchableOpacity onPress={startLogin} style={styles.loginButton}>
          <Text style={{color: 'white', fontSize: 24}}>로그인</Text>
        </TouchableOpacity>
    </View>
  )
}
const styles = StyleSheet.create({
  inputtext: {
    width: 300,
    height: 50,
    borderWidth: 4,
    borderColor: 'gray',
    borderRadius: 25,
    marginBottom: 20,
    paddingHorizontal: 10
  },
  loginButton: {
    width: 200,
    height: 56,
    backgroundColor: COLORS.user,
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 25,
    alignItems: 'center',
  }



});
export default LoginScreen;