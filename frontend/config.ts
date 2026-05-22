import { Platform } from 'react-native';

let BASE_URL = '';

if (Platform.OS === 'web') {
  // 💻 팀원분 환경 (웹 브라우저)
  // 팀원분이 켜둔 ngrok 주소나 localhost를 씁니다.
  BASE_URL = 'https://clench-clock-blob.ngrok-free.dev'; 
  
} else if (Platform.OS === 'android') {
  // 📱 질문자님 환경 (안드로이드 에뮬레이터)
  // 안드로이드 가상폰 전용 로컬 주소를 씁니다.
  BASE_URL = 'http://10.0.2.2:8000';
  
} else {
  // 🍎 혹시 모를 대비 (iOS 시뮬레이터)
  BASE_URL = 'http://127.0.0.1:8000';
}

export const API_BASE_URL = BASE_URL;