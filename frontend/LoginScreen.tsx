import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Alert, TextInput, StyleSheet } from 'react-native';

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

  const startLogin = () => {
    if (email === MOCK_USER.email && password === MOCK_USER.password) {
      Alert.alert("로그인 성공", `환영합니다, ${MOCK_USER.user_animal}님!`);
      onLoginSuccess(MOCK_USER);
    } else {
      Alert.alert("로그인 실패", "이메일 또는 비밀번호가 올바르지 않습니다.");
    }
  }

  return (
    <View style={styles.container}>
      {/* 폰트 크기를 확 줄인 중앙 상단 타이틀 */}
      <Text style={styles.title}>로그인</Text>

      {/* 이모지 제거 & 텍스트(User)로 대체한 이메일 입력창 */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>User</Text>
        <TextInput
          style={styles.input}
          placeholder="이메일 (asdf 입력)"
          placeholderTextColor="#B0B0B0"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
        />
      </View>

      {/* 이모지 제거 & 텍스트(********)로 대체한 비밀번호 입력창 */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>********</Text>
        <TextInput
          style={styles.input}
          placeholder="비밀번호 (1234 입력)"
          placeholderTextColor="#B0B0B0"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
      </View>

      {/* 로그인 버튼 */}
      <TouchableOpacity style={styles.button} onPress={startLogin}>
        <Text style={styles.buttonText}>로그인</Text>
      </TouchableOpacity>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
    backgroundColor: '#F2F2F2',
  },
  title: {
    fontSize: 24, // 40에서 24로 대폭 축소
    fontWeight: '600',
    marginBottom: 40, // 입력창과의 간격도 적당히 조절
    color: '#333',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    height: 55,
    backgroundColor: '#F2F2F2',
    borderWidth: 1.5,
    borderColor: '#666666',
    borderRadius: 27.5,
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    color: '#333',
    width: 60, // 글씨가 달라도 입력창 시작선이 딱 맞도록 고정 너비 부여
    fontWeight: '500',
  },
  input: {
    flex: 1,
    height: '100%',
    color: '#000',
    fontSize: 14,
  },
  button: {
    width: '50%',
    height: 45,
    backgroundColor: '#4A4A4A',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 22.5,
    marginTop: 10,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  }
});

export default LoginScreen;