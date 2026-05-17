import { Platform } from 'react-native';

export const API_BASE_URL = Platform.OS === 'android' ? 'https://clench-clock-blob.ngrok-free.dev' : 'http://127.0.0.1:8000';
