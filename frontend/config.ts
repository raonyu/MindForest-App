import { Platform } from 'react-native';

let BASE_URL = '';

if (Platform.OS === 'web') {
  BASE_URL = 'https://clench-clock-blob.ngrok-free.dev';

} else if (Platform.OS === 'android') {
  BASE_URL = 'http://10.0.2.2:8000';

} else {
  BASE_URL = 'http://127.0.0.1:8000';
}

export const API_BASE_URL = BASE_URL;