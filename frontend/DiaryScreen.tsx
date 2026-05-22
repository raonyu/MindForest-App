import React, { useState, useEffect } from 'react';
import { 
  View, Text, StyleSheet, TouchableOpacity, 
  TextInput, Platform, ScrollView, Alert, Image, Dimensions,
  ImageBackground, Keyboard // 💡 키보드 제어를 위한 모듈 추가
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
  
  const [isDakkuMode, setIsDakkuMode] = useState<boolean>(false);
  const [tempEmotion, setTempEmotion] = useState<string | null>(null);
  const [bgColor, setBgColor] = useState<any>(BACKGROUNDS[0]); 
  
  const [mainText, setMainText] = useState<string>(''); 
  const [currentFont, setCurrentFont] = useState<string>('System');

  const [elements, setElements] = useState<any[]>([]);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  
  const [activeTray, setActiveTray] = useState<string | null>(null);
  const [activeStickerCategory, setActiveStickerCategory] = useState<string>('생일/파티');

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
    } else {
      setTempEmotion(null);
      setMainText('');
      setCurrentFont('System');
      setElements([]);
      setBgColor(BACKGROUNDS[0]); 
    }
    setIsDakkuMode(true);
    setActiveTray(null);
  };

const handleSaveDiary = async () => {
    if (!tempEmotion) {
      Alert.alert("안내", "먼저 오늘의 감정을 선택해주세요.");
      return;
    }
    
    // 💡 dakkuData로 묶는 변수는 삭제하고 body에 직접 쪼개서 넣습니다.
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
          
          // 💡 분리해서 백엔드로 전송
          main_text: mainText,
          bg_color_id: bgColor.id,
          font: currentFont,
          elements: elements
        })
      });

      if (response.ok) {
        // 프론트엔드 화면 갱신용으로는 기존처럼 묶어서 저장해 줍니다.
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

  if (isDakkuMode) {
    return (
      <View style={styles.dakkuContainer}>
        <View style={styles.dakkuHeader}>
          <TouchableOpacity style={styles.headerLeftBtn} onPress={() => setIsDakkuMode(false)}>
            <Text style={styles.headerArrow}>◀</Text>
            <Text style={styles.headerBtnText}> 달력</Text>
          </TouchableOpacity>
          
          <Text style={styles.dakkuTitle}>{currentMonth}월 {selectedDate}일의 기록</Text>
          
          <TouchableOpacity style={styles.headerRightBtn} onPress={handleSaveDiary}>
            <Text style={styles.headerBtnText}>저장</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.emotionRow}>
          {EMOTIONS.map((emo: any) => {
            const EmotionIcon = emo.icon;
            const isSelected = tempEmotion === emo.id;
            return (
              <TouchableOpacity key={emo.id} onPress={() => setTempEmotion(emo.id)} style={[styles.miniEmotion, isSelected && { backgroundColor: emo.color + '33', borderColor: emo.color, borderWidth: 2 }]}>
                <EmotionIcon width={32} height={32} />
              </TouchableOpacity>
            );
          })}
        </View>

        {/* 💡 바탕 터치 시 편집 해제와 동시에 활성화된 키보드를 숨깁니다 */}
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

          {/* 💡 스티커/테이프가 조작 중일 때는 editable={false} 상태로 만들어 불필요한 키보드 팝업을 차단합니다 */}
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
                    Keyboard.dismiss(); // 💡 테이프나 사진을 터치했을 때도 키보드를 내려줍니다
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
                    <View style={styles.elementControls}>
                      {/* 💡 테이프/사진 리모컨 맨 앞에 배치된 완료(선택 해제) 버튼 */}
                      <TouchableOpacity onPress={() => setSelectedElementId(null)}>
                        <Text style={styles.controlIcon}>✅</Text>
                      </TouchableOpacity>
                      <TouchableOpacity onPress={() => updateElement(el.id, { size: el.size + 10 })}><Text style={styles.controlIcon}>➕</Text></TouchableOpacity>
                      <TouchableOpacity onPress={() => updateElement(el.id, { size: el.size - 10 })}><Text style={styles.controlIcon}>➖</Text></TouchableOpacity>
                      <View style={styles.moveControls}>
                        <TouchableOpacity onPress={() => updateElement(el.id, { y: (el.y || 0) - 10 })}><Text style={styles.controlIcon}>⬆️</Text></TouchableOpacity>
                        <TouchableOpacity onPress={() => updateElement(el.id, { y: (el.y || 0) + 10 })}><Text style={styles.controlIcon}>⬇️</Text></TouchableOpacity>
                        <TouchableOpacity onPress={() => updateElement(el.id, { x: (el.x || 0) - 10 })}><Text style={styles.controlIcon}>⬅️</Text></TouchableOpacity>
                        <TouchableOpacity onPress={() => updateElement(el.id, { x: (el.x || 0) + 10 })}><Text style={styles.controlIcon}>➡️</Text></TouchableOpacity>
                      </View>
                      <TouchableOpacity onPress={() => removeElement(el.id)}><Text style={styles.controlIcon}>🗑️</Text></TouchableOpacity>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </TouchableOpacity>

        {activeTray === 'font' && (
          <View style={styles.trayContainer} onStartShouldSetResponder={() => true}>
            <Text style={styles.trayTitle}>원하는 폰트를 선택하세요!</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} nestedScrollEnabled={true}>
              {FONTS.map((font: any) => (
                <TouchableOpacity key={font.id} onPress={() => applyFontToSelected(font.id)} style={[styles.fontItem, currentFont === font.id && styles.selectedFontItem]}>
                  <Text style={{ fontFamily: font.id === 'System' ? undefined : font.id, fontSize: 16 }}>{font.name}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {activeTray === 'sticker' && (
          <View style={styles.trayContainer} onStartShouldSetResponder={() => true}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 10 }} nestedScrollEnabled={true}>
              <View style={styles.categoryRow}>
                {Object.keys(STICKER_CATEGORIES).map((cat: string) => (
                  <TouchableOpacity key={cat} onPress={() => setActiveStickerCategory(cat)} style={[styles.categoryBtn, activeStickerCategory === cat && styles.activeCategoryBtn]}>
                    <Text style={activeStickerCategory === cat ? {fontWeight: 'bold', color: '#597d48'} : {color: '#777'}}>{cat}</Text>
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
            <Text style={styles.trayTitle}>마스킹 테이프 스티커 (선택 후 리모컨으로 이동시키세요)</Text>
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
                  bgColor.id === bg.id && { borderWidth: 2, borderColor: '#7ec96d' }
                ]} 
              />
            ))}
          </ScrollView>
          <View style={styles.toolButtons}>
            <TouchableOpacity style={styles.toolBtn} onPress={() => toggleTray('font')}><Text>🔤 폰트</Text></TouchableOpacity>
            <TouchableOpacity style={styles.toolBtn} onPress={addPolaroid}><Text>📸 사진</Text></TouchableOpacity>
            <TouchableOpacity style={styles.toolBtn} onPress={() => toggleTray('sticker')}><Text>🧸 스티커</Text></TouchableOpacity>
            <TouchableOpacity style={styles.toolBtn} onPress={() => toggleTray('highlighter')}><Text>🖍️ 테이프</Text></TouchableOpacity>
            {diaries[`${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(selectedDate).padStart(2, '0')}`] && (
               <TouchableOpacity style={styles.toolBtnDelete} onPress={handleDeleteDiary}><Text style={{color: 'white'}}>🗑️</Text></TouchableOpacity>
            )}
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
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

  dakkuContainer: { flex: 1, backgroundColor: '#f9f9f9', paddingTop: Platform.OS === 'ios' ? 50 : 20 },
  
  dakkuHeader: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', paddingVertical: 15, position: 'relative', height: 60 },
  headerLeftBtn: { position: 'absolute', left: 20, flexDirection: 'row', alignItems: 'center', zIndex: 10 },
  headerRightBtn: { position: 'absolute', right: 20, zIndex: 10 },
  headerArrow: { fontFamily: 'MemomentKkukkukk', fontSize: 17, color: '#2a3a21', marginRight: 4, marginTop: 2 },
  headerBtnText: { fontFamily: 'NanumSquareRoundR', fontSize: 16, color: '#2a3a21', fontWeight: 'bold' },
  dakkuTitle: { fontFamily: 'NanumSquareRoundR', fontSize: 18, fontWeight: 'bold', color: '#2a3a21' },

  emotionRow: { flexDirection: 'row', justifyContent: 'space-evenly', paddingBottom: 15, borderBottomWidth: 1, borderColor: '#eee' },
  miniEmotion: { padding: 5, borderRadius: 10 },
  
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

  elementWrapper: 
  { position: 'absolute',
    padding: 5,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  selectedElement: { borderColor: '#7ec96d', borderStyle: 'dashed' },
  
  polaroidFrame: { backgroundColor: 'white', padding: 12, paddingBottom: 35, shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 5, elevation: 5, transform: [{ rotate: '-2deg' }] },
  polaroidCaption: { position: 'absolute', bottom: 8, alignSelf: 'center', color: '#aaa', fontSize: 12 },
  highlighterDeco: { height: 22, borderRadius: 3, overflow: 'hidden', justifyContent: 'center' },

  elementControls: { flexDirection: 'row', alignItems: 'center', position: 'absolute', top: '100%', marginTop: 15, left: -10, backgroundColor: 'white', borderRadius: 12, padding: 8, shadowColor: '#000', shadowOpacity: 0.15, elevation: 5, gap: 8, zIndex: 9999 },
  moveControls: { flexDirection: 'row', backgroundColor: '#f0f0f0', borderRadius: 5, padding: 2, gap: 5 },
  controlIcon: { fontSize: 16 },
  
  // 💡 트레이 컨테이너 배경색 변경
  trayContainer: { backgroundColor: '#e8f5e9', paddingVertical: 15, paddingHorizontal: 10, borderTopWidth: 1, borderColor: '#eee' },
  trayTitle: { fontSize: 12, color: '#888', marginBottom: 10, paddingHorizontal: 10 },
  categoryRow: { flexDirection: 'row', paddingHorizontal: 10 },
  
  // 💡 선택되지 않은 기본 탭 상태: 뽀얀 흰색(#ffffff)으로 화사하게 수정
  categoryBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 15, backgroundColor: '#ffffff', marginRight: 8, borderWidth: 1, borderColor: '#eee' },
  // 💡 선택 시 MainScreen 전용 젤리 연두색(#eaffdf) 적용
  activeCategoryBtn: { backgroundColor: '#eaffdf', borderColor: '#eaffdf' },
  stickerItem: { marginHorizontal: 12, justifyContent: 'center', alignItems: 'center' },
  
  fontItem: { paddingHorizontal: 15, paddingVertical: 8, backgroundColor: '#fff', borderRadius: 10, marginRight: 10, borderWidth: 1, borderColor: '#ddd' },
  // 💡 폰트 선택 테두리 또한 젤리 연두색(#eaffdf)으로 일치
  selectedFontItem: { borderColor: '#eaffdf', borderWidth: 3 },
  
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
  toolBtn: { padding: 8, backgroundColor: '#f0f0f0', borderRadius: 10, minWidth: 50, alignItems: 'center' },
  toolBtnDelete: { padding: 8, backgroundColor: '#ff6b6b', borderRadius: 10, minWidth: 40, alignItems: 'center' },
});

export default DiaryScreen;