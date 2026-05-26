import React, { useState, useEffect } from 'react';
import { 
  View, Text, StyleSheet, TouchableOpacity, 
  TextInput, Platform, ScrollView, Alert, Image, Dimensions,
  ImageBackground, Keyboard, Modal
} from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker'; 
import { useMainContext } from './MainContext';
import { API_BASE_URL } from './config';

import { EMOTIONS, BACKGROUNDS, STICKER_CATEGORIES, FONTS, HIGHLIGHTERS } from './constants';
import ResizableElement from './ResizableElement';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

const DiaryScreen = () => {
  const { user } = useMainContext();

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

  const [diaries, setDiaries] = useState<Record<string, any>>({});
  const [selectedDate, setSelectedDate] = useState<number | null>(isCurrentMonth ? realToday.getDate() : null);
  
  const [isEmotionModalVisible, setIsEmotionModalVisible] = useState<boolean>(false);
  const [isDakkuMode, setIsDakkuMode] = useState<boolean>(false);
  const [tempEmotion, setTempEmotion] = useState<string | null>(null);
  
  const [bgColor, setBgColor] = useState<any>(BACKGROUNDS[0]); 
  const [mainText, setMainText] = useState<string>(''); 
  const [currentFont, setCurrentFont] = useState<string>('System');

  const [elements, setElements] = useState<any[]>([]);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  
  const [activeTray, setActiveTray] = useState<string | null>(null);
  const [activeStickerCategory, setActiveStickerCategory] = useState<string>('생일/파티');

  const getDayOfWeek = (year: number, month: number, day: number) => {
    const days = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
    const date = new Date(year, month - 1, day);
    return days[date.getDay()];
  };

  const fetchMonthlyDiaries = async () => {
    if (!user?.user_id) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/diary/monthly?user_id=${user.user_id}&year=${currentYear}&month=${currentMonth}`);
      if (response.ok) {
        const result = await response.json();
        const loadedDiaries: Record<string, any> = {};
        if (result.data) {
          result.data.forEach((item: any) => {
            loadedDiaries[item.date] = { emotion: item.emotion, text: item.content };
          });
        }
        setDiaries(loadedDiaries);
      }
    } catch (error) {
      console.error("일기 불러오기 실패:", error);
    }
  };

  useEffect(() => {
    fetchMonthlyDiaries();
  }, [currentYear, currentMonth, user?.user_id]);

  const goToPrevMonth = () => { setCurrentDateObj(new Date(currentYear, currentMonth - 2, 1)); setSelectedDate(null); };
  const goToNextMonth = () => { setCurrentDateObj(new Date(currentYear, currentMonth, 1)); setSelectedDate(null); };

  const handleDayPress = (day: number) => {
    setSelectedDate(day);
    const mm = String(currentMonth).padStart(2, '0');
    const dd = String(day).padStart(2, '0');
    const dateKey = `${currentYear}-${mm}-${dd}`; 
    const existingDiary = diaries[dateKey];
    
    setActiveTray(null);

    if (existingDiary) {
      setTempEmotion(existingDiary.emotion);
      try {
        const parsedData = JSON.parse(existingDiary.text);
        if (parsedData.elements !== undefined) {
          setElements(parsedData.elements);
          setBgColor(BACKGROUNDS.find((bg: any) => bg.id === parsedData.bgColorId) || BACKGROUNDS[0]);
          setMainText(parsedData.mainText || '');
          setCurrentFont(parsedData.font || 'System');
        } else {
          setMainText(existingDiary.text);
          setElements([]);
        }
      } catch {
        setMainText(existingDiary.text);
        setElements([]);
      }
      setIsDakkuMode(true); 
    } else {
      setTempEmotion(null);
      setMainText('');
      setCurrentFont('System');
      setElements([]);
      setBgColor(BACKGROUNDS[0]); 
      setIsEmotionModalVisible(true); 
    }
  };

  const handleEmotionSelect = (emotionId: string) => {
    setTempEmotion(emotionId);
    setIsEmotionModalVisible(false);
    
    if (!isDakkuMode) {
      setTimeout(() => {
        setIsDakkuMode(true);
      }, 100);
    }
  };

  const handleSaveDiary = async () => {
    if (!tempEmotion) {
      Alert.alert("안내", "먼저 오늘의 감정을 선택해주세요.");
      return;
    }
    
    const mm = String(currentMonth).padStart(2, '0');
    const dd = String(selectedDate).padStart(2, '0');
    const dateKey = `${currentYear}-${mm}-${dd}`;

    try {
      const response = await fetch(`${API_BASE_URL}/api/diary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.user_id,
          date: dateKey,
          emotion: tempEmotion,
          main_text: mainText,
          bg_color_id: bgColor.id,
          font: currentFont,
          elements: elements
        })
      });

      if (response.ok) {
        const dakkuData = JSON.stringify({ bgColorId: bgColor.id, mainText, font: currentFont, elements });
        setDiaries(prev => ({ ...prev, [dateKey]: { emotion: tempEmotion, text: dakkuData } }));
        setIsDakkuMode(false);
      } else {
        Alert.alert("오류", "서버 저장에 실패했습니다.");
      }
    } catch (error) {
      Alert.alert("오류", "서버와 연결할 수 없습니다.");
    }
  };

  const handleDeleteDiary = () => {
    Alert.alert("일기 지우기", "이 날의 기록을 지울까요?", [
      { text: "취소", style: "cancel" },
      { 
        text: "지우기", style: "destructive",
        onPress: async () => {
          const mm = String(currentMonth).padStart(2, '0');
          const dd = String(selectedDate).padStart(2, '0');
          const dateKey = `${currentYear}-${mm}-${dd}`; 
          try {
            const response = await fetch(`${API_BASE_URL}/api/diary?user_id=${user.user_id}&date=${dateKey}`, { method: 'DELETE' });
            if (response.ok) {
              const newDiaries = { ...diaries };
              delete newDiaries[dateKey];
              setDiaries(newDiaries);
              setIsDakkuMode(false);
            }
          } catch (error) { Alert.alert("오류", "서버와 연결할 수 없습니다."); }
        }
      }
    ]);
  };

  const addSticker = (sticker: any) => {
    setElements([...elements, { 
      id: Date.now().toString(), 
      type: 'sticker', 
      stickerType: sticker.type, 
      content: sticker.type === 'text' ? sticker.content : null,
      source: sticker.type === 'image' ? sticker.source : null,
      size: sticker.type === 'image' ? 70 : 50, 
      x: 100, y: 150 
    }]);
    setActiveTray(null);
  };

  const addHighlighter = (hl: any) => {
    setElements([...elements, { 
      id: Date.now().toString(), 
      type: 'highlighter', 
      color: hl.color || null, 
      texture: hl.texture || null,
      highlighterType: hl.type,
      design: hl.design || null,
      size: 140, 
      x: 50, y: 150 
    }]);
    setActiveTray(null);
  };

  const addPolaroid = async () => {
    const result = await launchImageLibrary({ mediaType: 'photo', quality: 0.8, selectionLimit: 1 });
    if (!result.didCancel && result.assets && result.assets.length > 0) {
      const uri = result.assets[0].uri;
      setElements([...elements, { id: Date.now().toString(), type: 'polaroid', uri: uri, size: 150, x: 80, y: 100 }]);
      setActiveTray(null);
    }
  };

  const applyFontToSelected = (fontId: string) => {
    setCurrentFont(fontId);
  };

  const updateElement = (id: string, newProps: any) => setElements(elements.map(el => el.id === id ? { ...el, ...newProps } : el));
  const removeElement = (id: string) => setElements(elements.filter(el => el.id !== id));
  const toggleTray = (trayName: string) => { setActiveTray(activeTray === trayName ? null : trayName); };

  const renderEmotionModal = () => (
    <Modal
      visible={isEmotionModalVisible}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setIsEmotionModalVisible(false)}
    >
      <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setIsEmotionModalVisible(false)}>
        <View style={styles.emotionModalContainer} onStartShouldSetResponder={() => true}>
          <View style={styles.modalDragHandle} />
          <Text style={styles.modalDateText}>
            {currentYear}.{String(currentMonth).padStart(2, '0')}.{String(selectedDate).padStart(2, '0')} {selectedDate ? getDayOfWeek(currentYear, currentMonth, selectedDate) : ''}
          </Text>
          <Text style={styles.modalTitleText}>오늘은 어떤 하루였나요?</Text>
          
          <View style={styles.modalEmotionGrid}>
            {EMOTIONS.map((emo: any) => {
              const EmotionIcon = emo.icon;
              return (
                <TouchableOpacity 
                  key={emo.id} 
                  style={styles.modalEmotionItem}
                  onPress={() => handleEmotionSelect(emo.id)}
                >
                  <EmotionIcon width={55} height={55} />
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      </TouchableOpacity>
    </Modal>
  );

  if (isDakkuMode) {
    const SelectedEmotionObj = EMOTIONS.find(e => e.id === tempEmotion);
    const SelectedEmotionIcon = SelectedEmotionObj ? SelectedEmotionObj.icon : null;
    const dayOfWeek = selectedDate ? getDayOfWeek(currentYear, currentMonth, selectedDate) : '';

    return (
      <View style={styles.dakkuContainer}>
        
        {renderEmotionModal()}

        <View style={styles.dakkuHeader}>
          <TouchableOpacity style={styles.headerLeftBtn} onPress={() => setIsDakkuMode(false)}>
            <Text style={styles.headerArrow}>◀</Text>
          </TouchableOpacity>
          
          <View style={styles.headerCenterContent}>
            <TouchableOpacity activeOpacity={0.7} onPress={() => setIsEmotionModalVisible(true)}>
              {SelectedEmotionIcon && <SelectedEmotionIcon width={45} height={45} style={{ marginBottom: 5 }} />}
            </TouchableOpacity>
            
            <Text style={styles.headerCenterDate}>
              {currentYear}.{String(currentMonth).padStart(2, '0')}.{String(selectedDate).padStart(2, '0')} {dayOfWeek}
            </Text>
          </View>
          
          <TouchableOpacity style={styles.headerRightBtn} onPress={handleSaveDiary}>
            <Text style={styles.headerSaveText}>저장</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity 
          activeOpacity={1} 
          style={[styles.canvas, bgColor.id === 'grid' ? { backgroundColor: '#ffffff' } : { backgroundColor: bgColor.color }]} 
          onPress={() => { 
            setSelectedElementId(null); 
            setActiveTray(null); 
            Keyboard.dismiss(); 
          }}
        >
          {bgColor.id === 'grid' && (
            <View style={StyleSheet.absoluteFill}>
              {Array.from({ length: Math.ceil(SCREEN_WIDTH / 26) }).map((_, i) => <View key={`v-${i}`} style={[styles.gridLineV, { left: i * 26 }]} />)}
              {Array.from({ length: Math.ceil(SCREEN_HEIGHT / 26) }).map((_, i) => <View key={`h-${i}`} style={[styles.gridLineH, { top: i * 26 }]} />)}
            </View>
          )}

          <TextInput 
            style={[styles.mainTextInput, { fontFamily: currentFont === 'System' ? undefined : currentFont }]} 
            multiline={true} 
            textAlignVertical="top" 
            value={mainText} 
            onChangeText={setMainText} 
            placeholder="화면을 터치해 일기를 작성해보세요..." 
            placeholderTextColor="#b4b4b4"
            blurOnSubmit={false}
            autoCapitalize="none"
            autoComplete="off"
            autoCorrect={false}
            spellCheck={false}
            editable={selectedElementId === null} 
          />

          <View style={[StyleSheet.absoluteFill, { zIndex: 10 }]} pointerEvents="box-none">
            {elements.map((el, index) => {
              const isSelected = selectedElementId === el.id;
              const currentZIndex = 100 + index; 
              
              if (el.type === 'sticker') {
                return (
                  <ResizableElement 
                    key={el.id} 
                    el={el} 
                    isSelected={isSelected}
                    onSelect={setSelectedElementId}
                    onUpdate={updateElement}
                    onRemove={removeElement}
                    zIndex={currentZIndex}
                  />
                );
              }

              return (
                <TouchableOpacity 
                  key={el.id} activeOpacity={0.9} 
                  onPress={() => {
                    setSelectedElementId(el.id);
                    Keyboard.dismiss(); 
                  }}
                  style={[
                    styles.elementWrapper, 
                    { top: el.y !== undefined ? el.y : 0, left: el.x !== undefined ? el.x : 0, zIndex: currentZIndex },
                    isSelected && styles.selectedElement
                  ]}
                >
                  {el.type === 'polaroid' && (
                    <View style={styles.polaroidFrame}>
                      <Image source={{ uri: el.uri }} style={{ width: el.size, height: el.size }} />
                      <Text style={styles.polaroidCaption}>Photo</Text>
                    </View>
                  )}
                  
                  {el.type === 'highlighter' && (
                    el.highlighterType === 'pattern' ? (
                      <ImageBackground source={el.texture} style={[styles.highlighterDeco, { width: el.size }]} imageStyle={{ opacity: 0.65 }} resizeMode="repeat" />
                    ) : (
                      <View style={[styles.highlighterDeco, { width: el.size, backgroundColor: el.color }]} />
                    )
                  )}

                  {isSelected && (
                    <>
                      {/* 확인 버튼: 파란 배경에 하얀 글씨 */}
                      <TouchableOpacity style={[styles.controlCircleBtn, styles.cornerConfirm]} onPress={() => setSelectedElementId(null)}>
                        <Text style={[styles.controlText, { color: 'white' }]}>O</Text>
                      </TouchableOpacity>
                      
                      {/* 확대 버튼 (+) */}
                      <TouchableOpacity style={[styles.controlCircleBtn, styles.cornerResize]} onPress={() => updateElement(el.id, { size: el.size + 10 })}>
                        <Text style={[styles.controlText, { fontSize: 16 }]}>+</Text>
                      </TouchableOpacity>
                      
                      {/* 축소 버튼 (-) */}
                      <TouchableOpacity style={[styles.controlCircleBtn, styles.cornerShrink]} onPress={() => updateElement(el.id, { size: Math.max(20, el.size - 10) })}>
                        <Text style={[styles.controlText, { fontSize: 16 }]}>-</Text>
                      </TouchableOpacity>
                      
                      {/* 삭제 버튼 (X) */}
                      <TouchableOpacity style={[styles.controlCircleBtn, styles.cornerDelete]} onPress={() => removeElement(el.id)}>
                        <Text style={[styles.controlText, { color: 'white' }]}>X</Text>
                      </TouchableOpacity>
                      
                      {/* 방향키 버튼 바 */}
                      <View style={styles.moveControlBar}>
                        <TouchableOpacity style={styles.moveArrowBtn} onPress={() => updateElement(el.id, { y: (el.y || 0) - 5 })}>
                          <Text style={styles.moveArrowText}>▲</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={styles.moveArrowBtn} onPress={() => updateElement(el.id, { y: (el.y || 0) + 5 })}>
                          <Text style={styles.moveArrowText}>▼</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={styles.moveArrowBtn} onPress={() => updateElement(el.id, { x: (el.x || 0) - 5 })}>
                          <Text style={styles.moveArrowText}>◀</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={styles.moveArrowBtn} onPress={() => updateElement(el.id, { x: (el.x || 0) + 5 })}>
                          <Text style={styles.moveArrowText}>▶</Text>
                        </TouchableOpacity>
                      </View>
                    </>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </TouchableOpacity>

        {activeTray === 'font' && (
          <View style={styles.trayContainer} onStartShouldSetResponder={() => true}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} nestedScrollEnabled={true}>
              {FONTS.map((font: any) => (
                <TouchableOpacity 
                  key={font.id} 
                  onPress={() => applyFontToSelected(font.id)} 
                  style={[styles.fontItem, currentFont === font.id && styles.selectedFontItem]}
                >
                  <Text style={{ 
                    fontFamily: font.id === 'System' ? undefined : font.id, 
                    fontSize: 16,
                    includeFontPadding: false,
                    textAlignVertical: 'center',
                    color: currentFont === font.id ? '#2a3a21' : '#555' 
                  }}>
                    {font.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {activeTray === 'sticker' && (
          <View style={styles.trayContainer} onStartShouldSetResponder={() => true}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 15 }} nestedScrollEnabled={true}>
              <View style={styles.categoryRow}>
                {Object.keys(STICKER_CATEGORIES).map((cat: string) => (
                  <TouchableOpacity 
                    key={cat} 
                    onPress={() => setActiveStickerCategory(cat)} 
                    style={[styles.categoryBtn, activeStickerCategory === cat && styles.activeCategoryBtn]}
                  >
                    <Text style={[
                      styles.categoryBtnText, 
                      activeStickerCategory === cat && styles.activeCategoryBtnText
                    ]}>{cat}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
            
            <ScrollView horizontal showsHorizontalScrollIndicator={false} nestedScrollEnabled={true}>
              {STICKER_CATEGORIES[activeStickerCategory as keyof typeof STICKER_CATEGORIES].map((sticker: any, idx: number) => (
                <TouchableOpacity key={sticker.id || idx} onPress={() => addSticker(sticker)} style={styles.stickerItem}>
                  {sticker.type === 'image' ? (
                    <Image source={sticker.source} style={styles.stickerTrayPreview} />
                  ) : (
                    <Text style={{ fontSize: 32 }}>{sticker.content}</Text>
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {activeTray === 'highlighter' && (
          <View style={styles.trayContainer} onStartShouldSetResponder={() => true}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} nestedScrollEnabled={true}>
              {HIGHLIGHTERS.map((hl: any) => (
                <TouchableOpacity key={hl.id} onPress={() => addHighlighter(hl)} style={styles.hlItemBtn}>
                  {hl.type === 'pattern' ? (
                    <Image source={hl.texture} style={styles.hlPreviewPattern} />
                  ) : (
                    <View style={[styles.hlPreviewColor, { backgroundColor: hl.color }]} />
                  )}
                  <Text style={styles.hlItemText}>{hl.name}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        <View style={styles.dakkuToolbar}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.bgSelector} nestedScrollEnabled={true}>
            {BACKGROUNDS.map((bg: any, idx: number) => (
              <TouchableOpacity key={idx} onPress={() => setBgColor(bg)} style={[
                  styles.bgCircle, 
                  bg.id === 'grid' ? styles.gridPreview : { backgroundColor: bg.color },
                  bgColor.id === bg.id && { borderWidth: 2, borderColor: '#98cbf1' }
                ]} 
              />
            ))}
          </ScrollView>
          <View style={styles.toolButtons}>
            <TouchableOpacity style={styles.toolBtn} onPress={() => toggleTray('font')}><Text style={styles.toolBtnText}>폰트</Text></TouchableOpacity>
            <TouchableOpacity style={styles.toolBtn} onPress={addPolaroid}><Text style={styles.toolBtnText}>사진</Text></TouchableOpacity>
            <TouchableOpacity style={styles.toolBtn} onPress={() => toggleTray('sticker')}><Text style={styles.toolBtnText}>스티커</Text></TouchableOpacity>
            <TouchableOpacity style={styles.toolBtn} onPress={() => toggleTray('highlighter')}><Text style={styles.toolBtnText}>테이프</Text></TouchableOpacity>
            {diaries[`${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(selectedDate).padStart(2, '0')}`] && (
               <TouchableOpacity style={styles.toolBtnDelete} onPress={handleDeleteDiary}><Text style={{color: 'white', fontWeight: 'bold'}}>삭제</Text></TouchableOpacity>
            )}
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      
      {renderEmotionModal()}

      <View style={styles.notebookContainer}>
        <View style={styles.calendarBoard}>
          <View style={styles.springContainer}>
            <View style={styles.springGroup}>
              {[...Array(2)].map((_, index) => (
                <View key={`left-${index}`} style={[styles.springWrapper, index === 1 && { marginLeft: 22 }]}>
                  <View style={styles.springPill} /><View style={styles.springHole} />
                </View>
              ))}
            </View>
            <View style={styles.springGroup}>
              {[...Array(2)].map((_, index) => (
                <View key={`right-${index}`} style={[styles.springWrapper, index === 1 && { marginLeft: 22 }]}>
                  <View style={styles.springPill} /><View style={styles.springHole} />
                </View>
              ))}
            </View>
          </View>

          <View style={styles.header}>
            <TouchableOpacity onPress={goToPrevMonth} style={styles.arrowBtn}><Text style={styles.arrowText}>◀</Text></TouchableOpacity>
            <View style={styles.monthTextContainer}>
              <View style={styles.highlighter}>
                <View style={styles.highlighterEnd} />
              </View>
              <Text style={styles.monthText}>{currentYear}년 {currentMonth}월</Text>
            </View>
            <TouchableOpacity onPress={goToNextMonth} style={styles.arrowBtn}><Text style={styles.arrowText}>▶</Text></TouchableOpacity>
          </View>

          <View style={styles.weekRow}>
            {['일', '월', '화', '수', '목', '금', '토'].map((day, index) => (
              <Text key={index} style={[styles.weekText, index === 0 ? { color: '#E53935' } : null, index === 6 ? { color: '#1E88E5' } : null]}>{day}</Text>
            ))}
          </View>

          <View style={styles.daysGrid}>
            {calendarDays.map((day, index) => {
              const mm = String(currentMonth).padStart(2, '0');
              const dd = String(day).padStart(2, '0');
              const dateKey = day !== null ? `${currentYear}-${mm}-${dd}` : '';
              const diaryEntry = day !== null ? diaries[dateKey] : null;
              
              const isToday = day !== null && isCurrentMonth && day === realToday.getDate();
              const isSelected = day !== null && day === selectedDate;
              const emotionObj = diaryEntry ? EMOTIONS.find((e: any) => e.id === diaryEntry.emotion) : null;
              const EmotionIcon = emotionObj ? emotionObj.icon : null;

              return (
                <TouchableOpacity 
                  key={index} 
                  style={[styles.dayCell, (isToday && !diaryEntry) ? styles.todayCell : null, (isSelected && !isToday && !diaryEntry) ? styles.selectedCell : null]}
                  onPress={() => day !== null && handleDayPress(day)}
                  disabled={day === null}
                >
                  {day !== null && (
                    <View style={styles.emotionCircle}>
                      {EmotionIcon ? <EmotionIcon width={36} height={36} /> : <Text style={[styles.dayText, isToday ? styles.todayText : null]}>{day}</Text>}
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', paddingTop: 60 },
  notebookContainer: { width: '90%', alignItems: 'center', marginTop: 20 },
  springContainer: { flexDirection: 'row', justifyContent: 'space-between', position: 'absolute', top: -15, left: 45, right: 45, zIndex: 20 },
  springGroup: { flexDirection: 'row' },
  springWrapper: { alignItems: 'center', width: 20 },
  springHole: { width: 14, height: 14, backgroundColor: '#e6eade', borderRadius: 7, marginTop: 18, borderWidth: 1, borderColor: '#dce3d4' },
  springPill: { position: 'absolute', top: 0, width: 14, height: 36, backgroundColor: '#ffffff', borderRadius: 7, borderWidth: 1, borderColor: '#e5e5e5', shadowColor: '#9bb08f', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 3, elevation: 2, zIndex: 21 },
  calendarBoard: { width: '100%', backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: 24, padding: 20, paddingTop: 40, borderWidth: 0, shadowColor: '#a1b594', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.15, shadowRadius: 25, elevation: 2, marginBottom: 25 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 25 },
  monthTextContainer: { position: 'relative', paddingHorizontal: 6, justifyContent: 'center', alignItems: 'center' },
  highlighter: { position: 'absolute', bottom: 2, left: -4, right: -4, height: 14, backgroundColor: '#bce2ff', borderRadius: 3, transform: [{ skewX: '-15deg' }, { rotate: '-2deg' }], flexDirection: 'row', justifyContent: 'flex-end' },
  highlighterEnd: { width: 2, height: '100%', backgroundColor: '#98cbf1', borderTopRightRadius: 3, borderBottomRightRadius: 3 },
  arrowBtn: { padding: 10 },
  arrowText: { fontFamily: 'MemomentKkukkukk', fontSize: 20, color: '#2a3a21' },
  monthText: { fontFamily: 'ownglyph', fontSize: 26, color: '#2a3a21' },
  weekRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 15 },
  weekText: { fontFamily: 'NanumSquareRoundR', fontSize: 16, color: '#2a3a21' },
  daysGrid: { flexDirection: 'row', flexWrap: 'wrap' },
  dayCell: { width: '14.28%', height: 55, justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  emotionCircle: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  todayCell: { backgroundColor: '#eaffdf', borderRadius: 22 },
  selectedCell: { borderWidth: 2, borderColor: '#acff80', borderRadius: 22 },
  dayText: { fontFamily: 'NanumSquareRoundR', fontSize: 16, color: '#2a3a21' },
  todayText: { fontFamily: 'NanumSquareRoundB', color: '#15210f' },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'flex-end' },
  emotionModalContainer: { backgroundColor: '#2a2a2a', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 25, alignItems: 'center', paddingBottom: Platform.OS === 'ios' ? 40 : 25 },
  modalDragHandle: { width: 40, height: 4, backgroundColor: '#555', borderRadius: 2, marginBottom: 20 },
  modalDateText: { fontSize: 13, color: '#999', marginBottom: 8 },
  modalTitleText: { fontSize: 18, color: '#ffffff', fontWeight: 'bold', marginBottom: 30 },

  // 💡 수정된 부분: 이모지가 9개(또는 그 이상)가 되어도 예쁘게 줄바꿈되도록 수정
  modalEmotionGrid: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    justifyContent: 'center', 
    gap: 15, // 이모지 사이의 간격
    width: '100%' // 그리드가 꽉 차게 해서 균형을 맞춤
  },

  modalEmotionItem: { 
    padding: 10, 
    // 💡 화면 넓이에 맞춰 한 줄에 3~4개씩 적절히 들어가도록 여백 조정
    marginHorizontal: 5, 
    marginBottom: 10 
  },

  dakkuContainer: { flex: 1, backgroundColor: '#f9f9f9', paddingTop: Platform.OS === 'ios' ? 50 : 20 },
  dakkuHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', paddingHorizontal: 20, paddingVertical: 10, height: 90 },
  headerLeftBtn: { padding: 10, marginTop: 5 },
  headerRightBtn: { padding: 10, marginTop: 5 },
  headerArrow: { fontFamily: 'MemomentKkukkukk', fontSize: 20, color: '#333' },
  headerSaveText: { fontFamily: 'NanumSquareRoundB', fontSize: 16, color: '#2a3a21', fontWeight: 'bold' },
  headerCenterContent: { alignItems: 'center', justifyContent: 'center' },
  headerCenterDate: { fontSize: 13, color: '#777' },

  canvas: { flex: 1, position: 'relative', overflow: 'hidden' }, 
  gridCanvas: { backgroundColor: '#ffffff', borderColor: '#e0e0e0', borderWidth: 2, borderStyle: 'dashed' },
  gridLineV: { position: 'absolute', top: 0, bottom: 0, width: 1, backgroundColor: 'rgba(215, 215, 215, 0.45)' },
  gridLineH: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(215, 215, 215, 0.45)' },

  mainTextInput: {
    ...StyleSheet.absoluteFillObject,
    padding: 20,
    fontSize: 18,
    color: '#2a3a21',
    zIndex: 1,
  },

  elementWrapper: { position: 'absolute', padding: 5, borderWidth: 1, borderColor: 'transparent' },
  selectedElement: { borderColor: '#98cbf1', borderStyle: 'dashed' },
  
  polaroidFrame: { backgroundColor: 'white', padding: 12, paddingBottom: 35, shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 5, elevation: 5, transform: [{ rotate: '-2deg' }] },
  polaroidCaption: { position: 'absolute', bottom: 8, alignSelf: 'center', color: '#aaa', fontSize: 12 },
  highlighterDeco: { height: 22, borderRadius: 3, overflow: 'hidden', justifyContent: 'center' },

  elementControls: { 
    position: 'absolute', 
    top: '100%', 
    left: -10, 
    right: -10,
    bottom: -15, 
    zIndex: 9999 
  },
  controlCircleBtn: {
    backgroundColor: 'white',
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
    position: 'absolute', 
  },
  controlText: {
    fontFamily: 'Galmuri9',
    fontSize: 12, 
    includeFontPadding: false,
    textAlignVertical: 'center',
    color: '#333',
  },

  // 💡 방향키 버튼 바 (이름 변경)
  moveControlBar: {
    flexDirection: 'row',
    position: 'absolute',
    top: '100%',
    left: '50%', 
    marginLeft: -66, 
    marginTop: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.9)', 
    borderRadius: 14, 
    padding: 4,
    gap: 6,
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 2 },
  },
  // 💡 이름 충돌 방지용으로 moveArrowBtn 변경
  moveArrowBtn: {
    padding: 4,
    backgroundColor: '#EAEAEA',
    borderRadius: 8,
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  moveArrowText: {
    fontFamily: 'Galmuri9',
    fontSize: 10, 
    color: '#333',
    includeFontPadding: false,
    textAlignVertical: 'center'
  },

  cornerConfirm: { 
    top: -10, 
    left: -10, 
    backgroundColor: '#98cbf1', 
  },
  cornerDelete: { 
    top: -10, 
    right: -10, 
    backgroundColor: '#ff6b6b' 
  },
  cornerResize: { 
    bottom: -10, 
    left: -10 
  },
  cornerShrink: { 
    bottom: -10, 
    right: -10 
  },
  
  trayContainer: { backgroundColor: '#e8f5e9', paddingVertical: 15, paddingHorizontal: 10, borderTopWidth: 1, borderColor: '#eee' },
  trayTitle: { fontSize: 12, color: '#888', marginBottom: 10, paddingHorizontal: 10 },
  categoryRow: { flexDirection: 'row', paddingHorizontal: 10 },
  
  categoryBtn: { 
    paddingHorizontal: 12, 
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 15, 
    backgroundColor: '#ffffff', 
    marginRight: 8, 
    borderWidth: 2, 
    borderColor: '#eee' 
  },
  
  activeCategoryBtn: { 
    borderColor: '#98cbf1'
  },
  categoryBtnText: {
    color: '#777'
  },
  activeCategoryBtnText: {
    color: '#2a3a21',
    fontWeight: 'bold'
  },

  stickerItem: { marginHorizontal: 12, justifyContent: 'center', alignItems: 'center' },
  
  fontItem: { 
    paddingHorizontal: 15, 
    height: 40, 
    justifyContent: 'center', 
    alignItems: 'center', 
    backgroundColor: '#fff', 
    borderRadius: 10, 
    marginRight: 10, 
    borderWidth: 2, 
    borderColor: '#eee'
  },
  
  selectedFontItem: { 
    borderColor: '#98cbf1' 
  },
  
  stickerTrayPreview: { width: 44, height: 44, resizeMode: 'contain' },
  hlPreviewColor: { width: 50, height: 22, borderRadius: 4, marginBottom: 5 },
  hlPreviewPattern: { width: 50, height: 22, borderRadius: 4, marginBottom: 5, resizeMode: 'cover' },
  hlItemText: { fontSize: 10, color: '#555' },
  hlItemBtn: { alignItems: 'center', marginRight: 15 },

  dakkuToolbar: { backgroundColor: 'white', paddingBottom: Platform.OS === 'ios' ? 30 : 15, paddingTop: 10, borderTopWidth: 1, borderColor: '#eee', zIndex: 1000 },
  bgSelector: { flexDirection: 'row', paddingHorizontal: 20, marginBottom: 10 },
  bgCircle: { width: 30, height: 30, borderRadius: 15, marginHorizontal: 5, borderWidth: 1, borderColor: '#ddd' },
  gridPreview: { backgroundColor: '#ffffff', borderColor: '#ccc', borderWidth: 1, borderStyle: 'dashed' }, 
  
  toolButtons: { flexDirection: 'row', justifyContent: 'space-around', paddingHorizontal: 10 },
  toolBtn: { paddingVertical: 8, paddingHorizontal: 12, backgroundColor: '#f5f5f5', borderRadius: 8, minWidth: 60, alignItems: 'center' },
  toolBtnText: { fontSize: 14, color: '#333', fontWeight: '600' },
  toolBtnDelete: { paddingVertical: 8, paddingHorizontal: 12, backgroundColor: '#ff6b6b', borderRadius: 8, minWidth: 60, alignItems: 'center' },
});

export default DiaryScreen;