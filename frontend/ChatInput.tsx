import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, Text, StyleSheet } from 'react-native';

const ChatInput = ({ onSend }: { onSend: (text: string) => void }) => {
  const [localText, setLocalText] = useState('');

  const handleSend = () => {
    const trimmedText = localText.trim();
    if (!trimmedText) return; // 빈 문자열이나 공백만 있을 때는 전송하지 않음
    onSend(trimmedText);
    setLocalText('');
  };

  return (
    <View style={styles.container}>
      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.textInput}
          value={localText}
          onChangeText={setLocalText}
          placeholder="메시지를 입력하세요..."
          placeholderTextColor="#A0A88F"
          multiline={true}
          maxLength={500}
        />
        <TouchableOpacity 
          onPress={handleSend} 
          style={[styles.sendButton, !localText.trim() ? styles.sendButtonDisabled : styles.sendButtonActive]}
          disabled={!localText.trim()}
          activeOpacity={0.8}
        >
          <Text style={[styles.sendButtonText, !localText.trim() ? styles.sendButtonTextDisabled : styles.sendButtonTextActive]}>전송</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff', // 전반적으로 하얀 톤
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.03,
    shadowRadius: 5,
    elevation: 3,
    width: '100%',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#f9fbf7', // 아주 연한 녹색/회색 톤으로 입력창 구분
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#e2ebd9',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  textInput: {
    flex: 1,
    color: '#2a3a21',
    fontSize: 16,
    fontFamily: 'NanumSquareRoundR', // 앱 전반적인 폰트 적용
    minHeight: 36,
    maxHeight: 120, // 내용이 길어지면 위로 늘어나도록
    paddingTop: 8,
    paddingBottom: 8,
  },
  sendButton: {
    justifyContent: 'center',
    alignItems: 'center',
    height: 36,
    borderRadius: 18,
    paddingHorizontal: 18,
    marginLeft: 12,
    marginBottom: 4,
  },
  sendButtonActive: {
    backgroundColor: '#9ee779', // 숲 테마의 밝은 녹색 포인트
  },
  sendButtonDisabled: {
    backgroundColor: '#f0f0f0',
  },
  sendButtonText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 14,
  },
  sendButtonTextActive: {
    color: '#15210f',
  },
  sendButtonTextDisabled: {
    color: '#a0a0a0',
  }
});

export default ChatInput;