import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal, Alert, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { Svg, Circle, Rect, Defs, LinearGradient, Stop } from 'react-native-svg';

// 초기 데이터 (테스트용)
const initialDiaries: Record<string, string> = {
  '2026-04-28': '오늘은 하늘이 참 맑았다. 공원에 가서 산책을 했는데 강아지들이 뛰어노는 모습이 너무 귀여웠다. 소소한 행복을 느낀 하루였다.',
};

const simulatedAiComfort = '오늘 하루도 정말 고생 많으셨어요. 당신의 마음이 조금이나마 편안해지기를 바랍니다. 🌿';

const FigmaSpringRing = () => (
  <View style={styles.ringWrapper}>
    <Svg width="24" height="55" viewBox="0 0 24 55" fill="none">
      <Circle cx="12" cy="39" r="12" fill="black" fillOpacity="0.28" />
      <Rect x="5" y="5" width="14" height="46" rx="7" fill="black" fillOpacity="0.15" />
      <Rect x="5" y="0" width="14" height="46" rx="7" fill="#D9D9D9" />
      <Defs>
        <LinearGradient id="innerShadowMock" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor="black" stopOpacity="0.25" />
          <Stop offset="0.15" stopColor="transparent" stopOpacity="0" />
          <Stop offset="1" stopColor="transparent" stopOpacity="0" />
        </LinearGradient>
      </Defs>
      <Rect x="5" y="0" width="14" height="46" rx="7" fill="url(#innerShadowMock)" />
    </Svg>
  </View>
);

const DiaryScreen: React.FC = () => {
  // 날짜 로직
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth() + 1;
  const todayString = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  const [selectedDate, setSelectedDate] = useState<string>(todayString);
  const [viewDate, setViewDate] = useState({ year: currentYear, month: currentMonth });
  const [diaries, setDiaries] = useState<Record<string, string>>(initialDiaries);
  const [isWriteModalVisible, setIsWriteModalVisible] = useState<boolean>(false);
  const [diaryText, setDiaryText] = useState<string>('');
  const [isAiPopupVisible, setIsAiPopupVisible] = useState<boolean>(false);

  // 월 이동 함수
  const handlePrevMonth = () => {
    if (viewDate.month === 1) setViewDate({ year: viewDate.year - 1, month: 12 });
    else setViewDate({ year: viewDate.year, month: viewDate.month - 1 });
  };
  const handleNextMonth = () => {
    if (viewDate.month === 12) setViewDate({ year: viewDate.year + 1, month: 1 });
    else setViewDate({ year: viewDate.year, month: viewDate.month + 1 });
  };

  // 로컬 저장 함수 (UI 흐름 확인용)
  const handleSaveDiary = () => {
    if (diaryText.trim() === '') {
      Alert.alert('알림', '일기 내용을 입력해주세요!');
      return;
    }
    setDiaries(prev => ({ ...prev, [selectedDate]: diaryText }));
    setIsWriteModalVisible(false);
    setDiaryText('');
    setTimeout(() => { setIsAiPopupVisible(true); }, 500);
  };

  // 삭제 함수 (휴지통 기능)
  const handleDeleteDiary = () => {
    Alert.alert(
      '일기 삭제',
      '정말로 이 일기를 삭제하시겠습니까?',
      [
        { text: '취소', style: 'cancel' },
        { 
          text: '삭제', 
          style: 'destructive',
          onPress: () => {
            const newDiaries = { ...diaries };
            delete newDiaries[selectedDate];
            setDiaries(newDiaries);
          }
        }
      ]
    );
  };

  const renderCalendarGrid = () => {
    const daysInMonth = new Date(viewDate.year, viewDate.month, 0).getDate();
    let firstDayOfWeek = new Date(viewDate.year, viewDate.month - 1, 1).getDay();
    let startEmptyCells = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;

    const days = [];
    for (let i = 0; i < startEmptyCells; i++) days.push(null);
    for (let i = 1; i <= daysInMonth; i++) days.push(i);
    while (days.length % 7 !== 0) days.push(null);

    return days.map((day, index) => {
      if (day === null) return <View key={index} style={[styles.dateCell, { backgroundColor: 'transparent' }]} />;
      const dateString = `${viewDate.year}-${String(viewDate.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isSelected = selectedDate === dateString;
      const isToday = todayString === dateString;
      const hasDiary = diaries[dateString];

      return (
        <TouchableOpacity 
          key={index} 
          style={[styles.dateCell, isSelected && styles.selectedDateCell, isToday && !isSelected && styles.todayHighlight]}
          onPress={() => setSelectedDate(dateString)}
        >
          <Text style={[styles.dateText, isSelected && styles.selectedDateText, isToday && styles.todayText]}>{day}</Text>
          {hasDiary && <Text style={styles.sproutIcon}>🌿</Text>}
        </TouchableOpacity>
      );
    });
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        
        {/* 달력 스프링 영역 */}
        <View style={styles.springSection}>
          <View style={styles.springGroup}><FigmaSpringRing /><FigmaSpringRing /></View>
          <View style={styles.springGroup}><FigmaSpringRing /><FigmaSpringRing /></View>
        </View>

        <View style={styles.calendarContainer}>
          <View style={styles.calendarHeader}>
            <TouchableOpacity onPress={handlePrevMonth} style={styles.navButton}><Text style={styles.calendarNav}>◀</Text></TouchableOpacity>
            <View style={styles.calendarTitleContainer}><Text style={styles.calendarTitle}>{`${viewDate.year}년 ${viewDate.month}월`}</Text></View>
            <TouchableOpacity onPress={handleNextMonth} style={styles.navButton}><Text style={styles.calendarNav}>▶</Text></TouchableOpacity>
          </View>
          <View style={styles.weekDaysContainer}>
            {['월', '화', '수', '목', '금', '토', '일'].map((day, index) => (
              <Text key={index} style={[styles.weekDayText, index === 5 && styles.saturday, index === 6 && styles.sunday]}>{day}</Text>
            ))}
          </View>
          <View style={styles.calendarGrid}>{renderCalendarGrid()}</View>
        </View>

        <TouchableOpacity style={styles.addDiaryButton} onPress={() => setIsWriteModalVisible(true)}>
          <Text style={styles.addDiaryButtonText}>오늘의 감정일기 추가</Text>
        </TouchableOpacity>

        <View style={styles.diaryCard}>
          <View style={styles.diaryCardHeader}>
            <Text style={styles.diaryCardTitle}>{selectedDate === todayString ? '🌱 오늘 나의 마음' : `${selectedDate}의 마음`}</Text>
            {diaries[selectedDate] && (
              <TouchableOpacity onPress={handleDeleteDiary} style={styles.deleteButton}>
                <Text style={styles.deleteIconText}>🗑️</Text>
              </TouchableOpacity>
            )}
          </View>
          <Text style={styles.diaryCardText} numberOfLines={4}>
            {diaries[selectedDate] || '이날은 아직 일기를 작성하지 않았어요!'}
          </Text>
        </View>
      </ScrollView>

      {/* 일기 작성 모달 */}
      <Modal visible={isWriteModalVisible} transparent={true} animationType="slide">
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.modalOverlay}>
          <View style={styles.writePopup}>
            <Text style={styles.writePopupTitle}>{selectedDate}의 감정 기록하기</Text>
            <TextInput
              style={styles.textInput}
              multiline={true}
              placeholder="오늘 어떤 마음이 드나요?"
              placeholderTextColor="#A0A0A0"
              value={diaryText}
              onChangeText={setDiaryText}
              textAlignVertical="top"
            />
            <View style={styles.buttonRow}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setIsWriteModalVisible(false)}><Text style={styles.cancelButtonText}>취소</Text></TouchableOpacity>
              <TouchableOpacity style={styles.saveButton} onPress={handleSaveDiary}><Text style={styles.saveButtonText}>저장하기</Text></TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* AI 위로 모달 */}
      <Modal visible={isAiPopupVisible} transparent={true} animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.aiPopup}>
            <Text style={styles.aiPopupTitle}>🌿 마음의 숲</Text>
            <Text style={styles.aiPopupText}>{simulatedAiComfort}</Text>
            <TouchableOpacity style={styles.closePopupButton} onPress={() => setIsAiPopupVisible(false)}>
              <Text style={styles.closePopupButtonText}>닫기</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#E8F5E9' },
  scrollContent: { padding: 20 },
  springSection: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 40, marginBottom: -35, zIndex: 10 },
  springGroup: { flexDirection: 'row', gap: 10 },
  ringWrapper: { backgroundColor: 'transparent' },
  calendarContainer: { backgroundColor: '#1E824C', borderRadius: 20, padding: 15, paddingTop: 40, paddingBottom: 25, marginBottom: 20, elevation: 5 },
  calendarHeader: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
  navButton: { padding: 10 },
  calendarNav: { color: 'white', fontSize: 20, marginHorizontal: 10 },
  calendarTitleContainer: { flexDirection: 'row', alignItems: 'center' },
  calendarTitle: { color: 'white', fontSize: 20, fontWeight: 'bold' },
  weekDaysContainer: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 10, marginBottom: 15 },
  weekDayText: { color: 'white', fontSize: 16, width: 30, textAlign: 'center' },
  saturday: { color: '#87CEFA' },
  sunday: { color: '#FF7F50' },
  calendarGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  dateCell: { width: '13%', aspectRatio: 1, justifyContent: 'center', alignItems: 'center', marginBottom: 10, backgroundColor: '#145A32', borderRadius: 8 },
  selectedDateCell: { borderWidth: 2, borderColor: '#A9DFBF', backgroundColor: '#0B3B24' },
  todayHighlight: { borderBottomWidth: 3, borderBottomColor: '#A9DFBF' },
  dateText: { color: 'white', fontSize: 16 },
  selectedDateText: { fontWeight: 'bold', color: '#A9DFBF' },
  todayText: { color: '#FFF59D', fontWeight: 'bold' },
  sproutIcon: { position: 'absolute', top: -5, right: -5, fontSize: 12 },
  addDiaryButton: { backgroundColor: '#0B3B24', padding: 15, borderRadius: 25, alignItems: 'center', marginBottom: 20 },
  addDiaryButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  diaryCard: { backgroundColor: 'white', padding: 20, borderRadius: 15, elevation: 3, minHeight: 120 },
  diaryCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  diaryCardTitle: { fontSize: 16, fontWeight: 'bold', color: '#1E824C' },
  deleteButton: { padding: 5 },
  deleteIconText: { fontSize: 20 },
  diaryCardText: { fontSize: 15, color: '#555', lineHeight: 22 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'center', alignItems: 'center' },
  writePopup: { backgroundColor: 'white', padding: 25, borderRadius: 20, width: '90%', maxHeight: '80%', elevation: 10 },
  writePopupTitle: { fontSize: 18, fontWeight: 'bold', color: '#1E824C', marginBottom: 15, textAlign: 'center' },
  textInput: { backgroundColor: '#F5F5F5', borderRadius: 10, padding: 15, fontSize: 16, height: 200, marginBottom: 20, color: '#333' },
  buttonRow: { flexDirection: 'row', justifyContent: 'space-between' },
  cancelButton: { flex: 1, backgroundColor: '#E0E0E0', padding: 15, borderRadius: 10, alignItems: 'center', marginRight: 10 },
  cancelButtonText: { color: '#555', fontSize: 16, fontWeight: 'bold' },
  saveButton: { flex: 1, backgroundColor: '#1E824C', padding: 15, borderRadius: 10, alignItems: 'center', marginLeft: 10 },
  saveButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  aiPopup: { backgroundColor: 'white', padding: 25, borderRadius: 20, width: '80%', alignItems: 'center', elevation: 10 },
  aiPopupTitle: { fontSize: 20, fontWeight: 'bold', color: '#1E824C', marginBottom: 15 },
  aiPopupText: { fontSize: 16, color: '#333', textAlign: 'center', marginBottom: 25, lineHeight: 24 },
  closePopupButton: { backgroundColor: '#1E824C', paddingVertical: 12, paddingHorizontal: 30, borderRadius: 25 },
  closePopupButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' }
});

export default DiaryScreen;