import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet, View, Text, TouchableOpacity, Alert,
  TextInput, Platform, KeyboardAvoidingView, ScrollView, ImageBackground,
  Animated,
  Easing
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
// import{ LinearGradient }from 'expo-linear-gradient';
import { API_BASE_URL } from './config';

const LoginScreen = ({ onLoginSuccess }: any) => {
  const [screenStep, setScreenStep] = useState(0);
  const [authAction, setAuthAction] = useState<'login' | 'signup'>('signup');
  const [inputId, setInputId] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const titleText = "마음의 숲";
  const titleArray = titleText.split('');
  //애니메이션 엔진
  const bounceAnims = useRef(titleArray.map(() => new Animated.Value(0))).current;


  useEffect(() => {
    const runAnimation = () => {
      const animations = bounceAnims.map((anim: Animated.Value) =>
        Animated.sequence([
          Animated.timing(anim, {
            toValue: -5,
            duration: 600,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 600,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      );

      Animated.loop(
        Animated.sequence([
          Animated.stagger(300, animations),
          Animated.delay(2000)
        ])
      ).start();
    };

    runAnimation();
  }, [bounceAnims]);


  const startAuth = async () => {
    if (!inputId.trim() || !password.trim()) {
      Alert.alert('안내', '아이디와 비밀번호를 모두 입력해주세요.');
      return;
    }

    setIsLoading(true);
    const endpoint = authAction === 'login' ? '/api/user/api/login' : '/api/user/api/signup';

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: inputId.trim(), password: password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        Alert.alert(authAction === 'login' ? '로그인 실패' : '회원가입 실패', errorData.detail || '다시 시도해주세요.');
        setIsLoading(false);
        return;
      }

      const result = await response.json();

      if (authAction === 'login') {
        const normalizedUser = {
          ...result,
          user_id: result.user_id || result.id || inputId
        };
        onLoginSuccess(normalizedUser);
      } else {
        Alert.alert('환영합니다! 🎉', '새로운 씨앗 등록이 완료되었습니다. 이제 숲으로 입장해주세요!', [
          {
            text: '확인',
            onPress: () => {
              setPassword('');
              setAuthAction('login');
            },
          },
        ]);
      }
    } catch (error) {
      console.error('통신 실패:', error);
      Alert.alert('서버 오류', '서버와 연결할 수 없습니다. 인터넷을 확인해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const WelcomeView = () => (
    <View style={styles.welcomeContainer}>
      <View style={styles.welcomeTextContainer}>
        <Text style={styles.subTitle}>나만의 작은 휴식처</Text>

        <View style={{ flexDirection: 'row' }}>
          {titleArray.map((char, index) => (
            <Animated.Text
              key={index}
              style={[
                styles.mainTitleLarge,
                { transform: [{ translateY: bounceAnims[index] }] }
              ]}
            >
              {char}
            </Animated.Text>
          ))}
        </View>

      </View>

      <View style={styles.welcomeButtonContainer}>
        <TouchableOpacity
          activeOpacity={0.8}
          style={styles.actionButtonWrapper}
          onPress={() => {
            setAuthAction('signup');
            setScreenStep(1);
          }}
        >
          <LinearGradient colors={['#cffff1', '#9ee779']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.actionButton}>
            <Text style={styles.actionButtonTextLarge}>숲 가꾸기 시작 (회원가입)</Text>
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.textButtonWrapper}
          onPress={() => {
            setAuthAction('login');
            setScreenStep(1);
          }}
        >
          <Text style={styles.textButtonText}>이미 숲이 있어요 (로그인)</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const FormView = () => (
    <View style={styles.formViewContainer}>
      <TouchableOpacity style={styles.backButton} onPress={() => setScreenStep(0)}>
        <Text style={styles.backButtonText}>◀ 밖으로 나가기</Text>
      </TouchableOpacity>

      <View style={styles.formCard}>
        <View style={styles.formTitleContainer}>
          <Text style={styles.mainTitleSmall}>{authAction === 'login' ? '숲 입장하기' : '새로운 씨앗 등록'}</Text>
          <Text style={styles.subTitleSmall}>{authAction === 'login' ? '당신의 마음의 숲이 기다리고 있어요.' : '마음의 숲에 오신 것을 환영해요!'}</Text>
        </View>

        <Text style={styles.inputLabel}>아이디</Text>
        <TextInput
          placeholder="아이디를 입력해주세요"
          placeholderTextColor="#95d675"
          value={inputId}
          onChangeText={setInputId}
          style={styles.inputBox}
          autoCapitalize="none"
          editable={!isLoading}
        />

        <Text style={styles.inputLabel}>비밀번호</Text>
        <TextInput
          placeholder="비밀번호를 입력해주세요"
          placeholderTextColor="#95d675"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.inputBox}
          editable={!isLoading}
        />

        <TouchableOpacity
          activeOpacity={0.8}
          onPress={startAuth}
          disabled={isLoading}
          style={[styles.actionButtonWrapper, { marginTop: 10 }]}
        >
          <LinearGradient colors={['#cffff1', '#9ee779']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.actionButton}>
            <Text style={styles.actionButtonText}>
              {isLoading ? '숲으로 걸어가는 중...' : (authAction === 'login' ? '입장하기' : '가입하기')}
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <ImageBackground
      source={require('./assets/forest_bg.jpg')}
      style={styles.backgroundImage}
      resizeMode="cover"
    >
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
          {screenStep === 0 ? <WelcomeView /> : <FormView />}
        </ScrollView>
      </KeyboardAvoidingView>
    </ImageBackground>
  );
};

// --- 스타일 섹션 ---
const styles = StyleSheet.create({
  backgroundImage: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  scrollContainer: {
    flexGrow: 1,
    paddingHorizontal: 25,
  },

  // 🏠 Step 0 Styles
  welcomeContainer: {
    flex: 1,
    width: '100%',
    justifyContent: 'flex-end',
  },
  welcomeTextContainer: {
    position: 'absolute',
    top: '44%',
    width: '100%',
    alignItems: 'center',
  },
  subTitle: {
    fontFamily: 'ownglyph',
    fontSize: 22,
    color: '#A0A88F',
    marginBottom: 8,
  },
  mainTitleLarge: {
    fontFamily: 'ownglyph',
    fontSize: 58,
    color: '#2a3a21',
    textShadowColor: 'rgba(255, 255, 255, 0.9)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 8,
  },
  welcomeButtonContainer: {
    width: '100%',
    alignItems: 'center',
    gap: 12,
    marginBottom: 135,
  },
  actionButtonTextLarge: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 18,
    color: '#15210f',
  },
  textButtonWrapper: {
    paddingVertical: 10,
    paddingHorizontal: 20,
  },
  textButtonText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 16,
    color: '#719e5b',
    textDecorationLine: 'underline',
  },

  // 📝 Step 1 Styles
  formViewContainer: {
    flex: 1,
    width: '100%',
    justifyContent: 'flex-end',
    paddingBottom: 40,
  },
  backButton: {
    alignSelf: 'flex-start',
    marginBottom: 15,
    paddingVertical: 5,
  },
  backButtonText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 15,
    color: '#597d48',
  },
  formTitleContainer: {
    alignItems: 'center',
    marginBottom: 25,
  },
  mainTitleSmall: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 24,
    color: '#2a3a21',
    marginBottom: 6,
  },
  subTitleSmall: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 14,
    color: '#597d48',
  },
  formCard: {
    width: '100%',
    backgroundColor: 'rgba(255, 255, 255, 0.94)',
    borderRadius: 24,
    padding: 25,
    shadowColor: '#719e5b',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 4,
  },
  inputLabel: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 14,
    color: '#597d48',
    marginBottom: 8,
    marginLeft: 6,
  },
  inputBox: {
    fontFamily: 'NanumSquareRoundR',
    backgroundColor: '#ffffff',
    height: 52,
    borderRadius: 14,
    paddingHorizontal: 16,
    fontSize: 15,
    color: '#15210f',
    borderWidth: 1.5,
    borderColor: '#eaffdf',
    marginBottom: 20,
  },

  actionButtonWrapper: {
    width: '100%',
    borderRadius: 18,
    shadowColor: '#9ee779',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  actionButton: {
    height: 54,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionButtonText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 16,
    color: '#15210f',
  }
});

export default LoginScreen;