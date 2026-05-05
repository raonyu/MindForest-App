import React, { useState } from 'react';
import { 
  View, Text, StyleSheet, TouchableOpacity, Modal, 
  TextInput, KeyboardAvoidingView, Platform, ScrollView, Alert 
} from 'react-native';

import JoyEmoji from './assets/icons/JoyEmoji';
import CalmEmoji from './assets/icons/CalmEmoji';
import SadEmoji from './assets/icons/SadEmoji';
import AngryEmoji from './assets/icons/AngryEmoji';
import AnxiousEmoji from './assets/icons/AnxiousEmoji';
import CryingEmoji from './assets/icons/CryingEmoji';

const EMOTIONS = [
  { id: 'joy', color: '#FF5B5B', icon: JoyEmoji },
  { id: 'calm', color: '#64E671', icon: CalmEmoji },
  { id: 'sadness', color: '#FFB661', icon: SadEmoji },
  { id: 'anger', color: '#FFD25E', icon: AngryEmoji },
  { id: 'anxiety', color: '#FF6187', icon: AnxiousEmoji },
  { id: 'crying', color: '#E961FF', icon: CryingEmoji },
];

const DiaryScreen = () => {
  const realToday = new Date();
  const [currentDateObj, setCurrentDateObj] = useState(new Date());
  
  const currentYear = currentDateObj.getFullYear();
  const currentMonth = currentDateObj.getMonth() + 1;
  const isCurrentMonth = currentYear === realToday.getFullYear() && currentMonth === realToday.getMonth() + 1;

  const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
  const firstDayOfMonth = new Date(currentYear, currentMonth - 1, 1).getDay();
  const calendarDays = Array.from({ length: daysInMonth + firstDayOfMonth }, (_, i) => 
    i >= firstDayOfMonth ? i - firstDayOfMonth + 1 : null
  );

  const [diaries, setDiaries] = useState<Record<string, { emotion: string, text: string }>>({});
  
  const [selectedDate, setSelectedDate] = useState<number | null>(isCurrentMonth ? realToday.getDate() : null);
  const [isDetailModalVisible, setDetailModalVisible] = useState(false);
  const [isWriteModalVisible, setWriteModalVisible] = useState(false);
  
  const [tempEmotion, setTempEmotion] = useState<string | null>(null);
  const [diaryText, setDiaryText] = useState('');

  const goToPrevMonth = () => {
    setCurrentDateObj(new Date(currentYear, currentMonth - 2, 1));
    setSelectedDate(null);
  };

  const goToNextMonth = () => {
    setCurrentDateObj(new Date(currentYear, currentMonth, 1));
    setSelectedDate(null);
  };

  const handleDayPress = (day: number) => {
    setSelectedDate(day);
    const dateKey = `${currentYear}-${currentMonth}-${day}`;
    const existingDiary = diaries[dateKey];
    
    if (existingDiary) {
      setTempEmotion(existingDiary.emotion);
      setDiaryText(existingDiary.text);
    } else {
      setTempEmotion(null);
      setDiaryText('');
    }
    setDetailModalVisible(true);
  };

  const handleSelectEmotion = (emoId: string) => {
    setTempEmotion(emoId);
    
    if (selectedDate !== null) {
      const dateKey = `${currentYear}-${currentMonth}-${selectedDate}`;
      setDiaries(prev => ({
        ...prev,
        [dateKey]: { 
          emotion: emoId, 
          text: prev[dateKey]?.text || '' 
        }
      }));
    }
  };

  const handleSaveDiary = () => {
    if (!tempEmotion) {
      Alert.alert("안내", "먼저 오늘의 감정을 선택해주세요!");
      return;
    }
    const dateKey = `${currentYear}-${currentMonth}-${selectedDate}`;
    setDiaries(prev => ({
      ...prev,
      [dateKey]: { emotion: tempEmotion, text: diaryText }
    }));
    setWriteModalVisible(false);
    setDetailModalVisible(false);
  };

  const handleDeleteDiary = () => {
    Alert.alert("일기 지우기", "이 날의 기록을 지울까요?", [
      { text: "취소", style: "cancel" },
      { 
        text: "지우기", 
        style: "destructive",
        onPress: () => {
          const dateKey = `${currentYear}-${currentMonth}-${selectedDate}`;
          const newDiaries = { ...diaries };
          delete newDiaries[dateKey];
          setDiaries(newDiaries);
          setDetailModalVisible(false);
        }
      }
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.notebookContainer}>
        <View style={styles.calendarBoard}>
          
          <View style={styles.springContainer}>
            <View style={styles.springGroup}>
              {[...Array(2)].map((_, index) => (
                <View key={`left-${index}`} style={[styles.springWrapper, index === 1 && { marginLeft: 22 }]}>
                  <View style={styles.springPill} />
                  <View style={styles.springHole} />
                </View>
              ))}
            </View>
            <View style={styles.springGroup}>
              {[...Array(2)].map((_, index) => (
                <View key={`right-${index}`} style={[styles.springWrapper, index === 1 && { marginLeft: 22 }]}>
                  <View style={styles.springPill} />
                  <View style={styles.springHole} />
                </View>
              ))}
            </View>
          </View>

          <View style={styles.header}>
            <TouchableOpacity onPress={goToPrevMonth} style={styles.arrowBtn}>
              <Text style={styles.arrowText}>◀</Text>
            </TouchableOpacity>
            
            <View style={styles.monthTextContainer}>
              <View style={styles.highlighter}>
                <View style={styles.highlighterEnd} />
              </View>
              <Text style={styles.monthText}>{currentYear}년 {currentMonth}월</Text>
            </View>

            <TouchableOpacity onPress={goToNextMonth} style={styles.arrowBtn}>
              <Text style={styles.arrowText}>▶</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.weekRow}>
            {['일', '월', '화', '수', '목', '금', '토'].map((day, index) => (
              <Text key={index} style={[
                styles.weekText, 
                index === 0 ? { color: '#E53935' } : null,
                index === 6 ? { color: '#1E88E5' } : null
              ]}>
                {day}
              </Text>
            ))}
          </View>

          <View style={styles.daysGrid}>
            {calendarDays.map((day, index) => {
              const dateKey = day !== null ? `${currentYear}-${currentMonth}-${day}` : '';
              const diaryEntry = day !== null ? diaries[dateKey] : null;
              
              const isToday = day !== null && isCurrentMonth && day === realToday.getDate();
              const isSelected = day !== null && day === selectedDate;

              const emotionObj = diaryEntry ? EMOTIONS.find(e => e.id === diaryEntry.emotion) : null;
              const EmotionIcon = emotionObj ? emotionObj.icon : null;

              return (
                <TouchableOpacity 
                  key={index} 
                  style={[
                    styles.dayCell, 
                    (isToday && !diaryEntry) ? styles.todayCell : null,
                    (isSelected && !isToday && !diaryEntry) ? styles.selectedCell : null
                  ]}
                  onPress={() => day !== null && handleDayPress(day)}
                  disabled={day === null}
                >
                  {day !== null && (
                    <View style={styles.emotionCircle}>
                      {EmotionIcon ? (
                        <EmotionIcon width={36} height={36} />
                      ) : (
                        <Text style={[styles.dayText, isToday ? styles.todayText : null]}>{day}</Text>
                      )}
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      </View>

      <Modal visible={isDetailModalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.bottomSheet}>
            <Text style={styles.modalTitle}>{currentMonth}월 {selectedDate}일의 조각</Text>
            <Text style={styles.guideText}>오늘의 대표 감정은 어땠나요?</Text>
            
            <View style={styles.emotionRow}>
              {EMOTIONS.map((emo) => {
                const EmotionIcon = emo.icon;
                const isSelected = tempEmotion === emo.id;
                
                return (
                  <TouchableOpacity 
                    key={emo.id} 
                    style={[
                      styles.emotionSelector, 
                      isSelected ? { borderColor: emo.color } : null
                    ]}
                    onPress={() => handleSelectEmotion(emo.id)}
                  >
                    <EmotionIcon width={48} height={48} />
                  </TouchableOpacity>
                );
              })}
            </View>

            {tempEmotion && (
              <View style={styles.diaryPreviewContainer}>
                {diaryText ? (
                  <ScrollView style={styles.previewBox}>
                    <Text style={styles.previewText}>{diaryText}</Text>
                  </ScrollView>
                ) : (
                  <Text style={styles.emptyText}>아직 남겨진 이야기가 없어요</Text>
                )}
                
                <View style={styles.actionButtonRow}>
                  <TouchableOpacity style={styles.writeButton} onPress={() => setWriteModalVisible(true)}>
                    <Text style={styles.buttonText}>{diaryText ? '일기 수정하기' : '일기 쓰러가기'}</Text>
                  </TouchableOpacity>
                  {diaryText ? (
                    <TouchableOpacity style={styles.deleteButton} onPress={handleDeleteDiary}>
                      <Text style={styles.deleteButtonText}>지우기</Text>
                    </TouchableOpacity>
                  ) : null}
                </View>
              </View>
            )}

            <TouchableOpacity style={styles.closeButton} onPress={() => setDetailModalVisible(false)}>
              <Text style={styles.closeButtonText}>닫기</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <Modal visible={isWriteModalVisible} animationType="fade" transparent>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.modalOverlay}>
          <View style={styles.writeSheet}>
            <Text style={styles.modalTitle}>내 마음 끄적이기</Text>
            <TextInput
              style={styles.diaryInput}
              multiline
              placeholder="여기에 편하게 적어주세요..."
              placeholderTextColor="#719e5b"
              value={diaryText}
              onChangeText={setDiaryText}
              autoFocus
            />
            <View style={styles.actionButtonRow}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setWriteModalVisible(false)}>
                <Text style={styles.cancelButtonText}>취소</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.saveButton} onPress={handleSaveDiary}>
                <Text style={styles.buttonText}>저장하기</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    paddingTop: 60,
  },
  notebookContainer: {
    width: '90%',
    alignItems: 'center',
    marginTop: 20,
  },
  springContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    position: 'absolute',
    top: -15,
    left: 45,
    right: 45,
    zIndex: 20,
  },
  springGroup: {
    flexDirection: 'row',
  },
  springWrapper: {
    alignItems: 'center',
    width: 20,
  },
  springHole: {
    width: 14,
    height: 14,
    backgroundColor: '#3a4a31',
    borderRadius: 7,
    marginTop: 18,
  },
  springPill: {
    position: 'absolute',
    top: 0,
    width: 14,
    height: 36,
    backgroundColor: '#ffffff',
    borderRadius: 7,
    borderWidth: 1,
    borderColor: '#e5e5e5',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    elevation: 3,
    zIndex: 21,
  },
  calendarBoard: {
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 20,
    paddingTop: 40,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 25,
    paddingHorizontal: 10,
  },
  monthTextContainer: {
    position: 'relative',
    paddingHorizontal: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  highlighter: {
    position: 'absolute',
    bottom: 2,
    left: -4,
    right: -4,
    height: 14,
    backgroundColor: '#bce2ff', 
    borderRadius: 3,
    transform: [{ skewX: '-15deg' }, { rotate: '-2deg' }], 
    flexDirection: 'row', 
    justifyContent: 'flex-end', 
  },
  highlighterEnd: {
    width: 2, 
    height: '100%',
    backgroundColor: '#98cbf1',
    borderTopRightRadius: 3,
    borderBottomRightRadius: 3,
  },
  arrowBtn: {
    padding: 10,
  },
  arrowText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 18,
    color: '#2a3a21', 
  },
  monthText: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 22,
    color: '#2a3a21',
  },
  weekRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
  },
  weekText: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 16,
    color: '#2a3a21',
  },
  daysGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  dayCell: {
    width: '14.28%',
    height: 55,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  emotionCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  todayCell: {
    backgroundColor: '#eaffdf',
    borderRadius: 22,
  },
  selectedCell: {
    borderWidth: 2,
    borderColor: '#acff80',
    borderRadius: 22,
  },
  dayText: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 16,
    color: '#2a3a21',
  },
  todayText: {
    fontFamily: 'NanumSquareRoundB',
    color: '#15210f',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(21, 33, 15, 0.4)',
    justifyContent: 'flex-end',
  },
  bottomSheet: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    padding: 25,
    paddingBottom: 35,
  },
  writeSheet: {
    backgroundColor: '#ffffff',
    borderRadius: 30,
    padding: 25,
    margin: 20,
    marginBottom: Platform.OS === 'ios' ? 100 : 20,
  },
  modalTitle: {
    fontFamily: 'NanumSquareRoundB',
    fontSize: 20,
    color: '#2a3a21',
    textAlign: 'center',
    marginBottom: 10,
  },
  guideText: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 15,
    color: '#597d48',
    textAlign: 'center',
    marginBottom: 20,
  },
  emotionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    gap: 15,
    marginBottom: 25,
  },
  emotionSelector: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '28%',
    aspectRatio: 1,
    borderRadius: 22,
    borderWidth: 3,
    borderColor: 'transparent',
    backgroundColor: 'transparent',
    padding: 8,
  },
  diaryPreviewContainer: {
    backgroundColor: '#eaffdf',
    borderRadius: 20,
    padding: 15,
    marginBottom: 20,
  },
  previewBox: {
    maxHeight: 100,
    marginBottom: 15,
  },
  previewText: {
    fontFamily: 'NanumSquareRoundR',
    fontSize: 15,
    color: '#15210f',
    lineHeight: 22,
  },
  emptyText: {
    fontFamily: 'NanumSquareRoundR',
    textAlign: 'center',
    color: '#719e5b',
    marginVertical: 15,
    fontSize: 14,
  },
  diaryInput: {
    fontFamily: 'NanumSquareRoundR',
    height: 180,
    backgroundColor: '#eaffdf',
    borderRadius: 20,
    padding: 20,
    textAlignVertical: 'top',
    fontSize: 16,
    color: '#15210f',
    marginBottom: 20,
  },
  actionButtonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  writeButton: {
    flex: 2,
    backgroundColor: '#acff80',
    padding: 14,
    borderRadius: 15,
    alignItems: 'center',
    marginRight: 10,
  },
  saveButton: {
    flex: 2,
    backgroundColor: '#acff80',
    padding: 14,
    borderRadius: 15,
    alignItems: 'center',
    marginLeft: 10,
  },
  deleteButton: {
    flex: 1,
    backgroundColor: '#FFEBEE',
    padding: 14,
    borderRadius: 15,
    alignItems: 'center',
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 14,
    borderRadius: 15,
    alignItems: 'center',
  },
  buttonText: {
    fontFamily: 'NanumSquareRoundB',
    color: '#15210f',
    fontSize: 16,
  },
  deleteButtonText: {
    fontFamily: 'NanumSquareRoundB',
    color: '#E53935',
    fontSize: 16,
  },
  cancelButtonText: {
    fontFamily: 'NanumSquareRoundB',
    color: '#597d48',
    fontSize: 16,
  },
  closeButton: {
    alignItems: 'center',
    paddingVertical: 15,
  },
  closeButtonText: {
    fontFamily: 'NanumSquareRoundB',
    color: '#719e5b',
    fontSize: 16,
  }
});

export default DiaryScreen;