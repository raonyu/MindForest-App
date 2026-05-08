import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Alert, TextInput, Platform, Modal } from 'react-native';
import { COLORS } from './assets/Maincolors';

const API_BASE_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';

const LoginScreen = ({ onLoginSuccess }: any) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [signupVisible, setSignupVisible] = useState(false);
  const [signupId, setSignupId] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [isSigningUp, setIsSigningUp] = useState(false);

  const MOCK_USER = {
    user_id: "user_01",
    email: "asdf",
    password: "1234",
    is_onboarding_done: true,
    user_animal: "거북이",
    assigned_category: "안정형"
  };

  const mockStartLogin = () => {
    if (email === MOCK_USER.email && password === MOCK_USER.password){
      Alert.alert("로그인 성공", `환영합니다, ${MOCK_USER.user_animal}님!`);
      onLoginSuccess(MOCK_USER);
    } else {
      Alert.alert("로그인 실패", "이메일 또는 비밀번호가 올바르지 않습니다.");
    }
  }

  const startLogin = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/user/api/login`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: email, password: password}),
      });

      // 로그인 실패 처리
      if (!response.ok) {
        const errorData = await response.json();
        Alert.alert("로그인 실패", errorData.detail || "이메일 또는 비밀번호를 확인해주세요.");
        return;
      }

      const userData = await response.json();
      console.log("서버 응답 데이터:", userData); // 확인용 로그
      
      // 핵심 해결책: 프론트엔드가 원하는 user_id 키를 무조건 생성해 줍니다.
      const normalizedUser = {
        ...userData,
        user_id: userData.user_id || userData.id || email 
      };

      // 보정된 유저 데이터를 전송
      onLoginSuccess(normalizedUser);

    } catch (error) {
      console.error('로그인 실패:', error);
      Alert.alert("서버 오류", "서버와 연결할 수 없습니다.");
    }
  }

  const startSignup = async () => {
    if (!signupId.trim() || !signupPassword.trim()) {
      Alert.alert('회원가입 실패', '아이디와 비밀번호를 입력해주세요.');
      return;
    }

    try {
      setIsSigningUp(true);
      const response = await fetch(`${API_BASE_URL}/api/user/api/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: signupId.trim(), password: signupPassword }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        Alert.alert('회원가입 실패', errorData.detail || '회원가입 중 오류가 발생했습니다.');
        return;
      }

      const result = await response.json();
      if (response.status === 200 && result?.message === 'signup success') {
        Alert.alert('회원가입 완료', '회원가입이 완료되었습니다.', [
          {
            text: '확인',
            onPress: () => {
              setSignupVisible(false);
              setSignupId('');
              setSignupPassword('');
            },
          },
        ]);
        return;
      }

      Alert.alert('회원가입 실패', '예상하지 못한 응답입니다.');
    } catch (error) {
      console.error('회원가입 실패:', error);
      Alert.alert('서버 오류', '서버와 연결할 수 없습니다.');
    } finally {
      setIsSigningUp(false);
    }
  };


  return (
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
      <TouchableOpacity onPress={() => setSignupVisible(true)} style={styles.signupButton}>
        <Text style={{color: COLORS.user, fontSize: 20, fontWeight: 'bold'}}>회원가입</Text>
      </TouchableOpacity>

      <Modal visible={signupVisible} transparent animationType="fade" onRequestClose={() => setSignupVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>회원가입</Text>
            <TextInput
              placeholder="아이디"
              value={signupId}
              onChangeText={setSignupId}
              style={styles.inputtext}
              editable={!isSigningUp}
              autoCapitalize="none"
            />
            <TextInput
              placeholder="비밀번호"
              value={signupPassword}
              onChangeText={setSignupPassword}
              secureTextEntry
              style={styles.inputtext}
              editable={!isSigningUp}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setSignupVisible(false)}
                disabled={isSigningUp}
              >
                <Text style={styles.modalButtonText}>취소</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.confirmButton]}
                onPress={startSignup}
                disabled={isSigningUp}
              >
                <Text style={styles.modalButtonText}>{isSigningUp ? '처리중...' : '회원가입'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
  },
  signupButton: {
    marginTop: 16,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCard: {
    width: 340,
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  modalButtons: {
    width: '100%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  modalButton: {
    width: 145,
    height: 48,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#A5A5A5',
  },
  confirmButton: {
    backgroundColor: COLORS.user,
  },
  modalButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  }
});

export default LoginScreen;