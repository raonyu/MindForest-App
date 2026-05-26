import React, { useRef } from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity, PanResponder } from 'react-native';

interface ResizableElementProps {
  el: any;
  isSelected: boolean;
  onSelect: (id: string | null) => void; 
  onUpdate: (id: string, newProps: any) => void;
  onRemove: (id: string) => void;
  zIndex: number; 
}

const ResizableElement: React.FC<ResizableElementProps> = ({ el, isSelected, onSelect, onUpdate, onRemove, zIndex }) => {
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderMove: (evt, gestureState) => {
        onUpdate(el.id, {
          x: (el.x || 0) + gestureState.dx,
          y: (el.y || 0) + gestureState.dy,
        });
      },
      onPanResponderRelease: () => {},
    })
  ).current;

  return (
    <View
      style={[
        styles.wrapper,
        { top: el.y, left: el.x, zIndex: zIndex }, 
        isSelected && styles.selectedWrapper
      ]}
    >
      <TouchableOpacity activeOpacity={1} onPress={() => onSelect(el.id)} {...panResponder.panHandlers}>
        {el.stickerType === 'image' ? (
          <Image source={el.source} style={{ width: el.size, height: el.size, resizeMode: 'contain' }} />
        ) : (
          <Text style={{ fontSize: el.size, fontFamily: 'Galmuri9' }}>{el.content}</Text>
        )}
      </TouchableOpacity>

      {isSelected && (
        <>
          {/* 💡 확인 버튼: O - 요청하신 파란색 배경에 하얀 글씨로 변경 */}
          <TouchableOpacity style={styles.confirmBtn} onPress={() => onSelect(null)}>
            <Text style={[styles.iconText, { color: 'white' }]}>O</Text>
          </TouchableOpacity>

          {/* 삭제 버튼: X */}
          <TouchableOpacity style={styles.deleteBtn} onPress={() => onRemove(el.id)}>
            <Text style={[styles.iconText, { color: 'white' }]}>X</Text>
          </TouchableOpacity>

          {/* 확대 버튼 (+) : 시각적 균형을 위해 사이즈 16 적용 */}
          <TouchableOpacity style={styles.resizeBtn} onPress={() => onUpdate(el.id, { size: el.size + 10 })}>
            <Text style={[styles.iconText, { fontSize: 16 }]}>+</Text>
          </TouchableOpacity>

          {/* 축소 버튼 (-) : 시각적 균형을 위해 사이즈 16 적용 */}
          <TouchableOpacity style={styles.shrinkBtn} onPress={() => onUpdate(el.id, { size: Math.max(20, el.size - 10) })}>
            <Text style={[styles.iconText, { fontSize: 16 }]}>-</Text>
          </TouchableOpacity>

          {/* 💡 방향키 버튼 바: "리퀴드 글래스" 질감 및 우윳빛 색상 적용 컴포넌트 */}
          <View style={styles.moveControlBar}>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { y: (el.y || 0) - 5 })}>
              <Text style={styles.arrowText}>▲</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { y: (el.y || 0) + 5 })}>
              <Text style={styles.arrowText}>▼</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { x: (el.x || 0) - 5 })}>
              <Text style={styles.arrowText}>◀</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { x: (el.x || 0) + 5 })}>
              <Text style={styles.arrowText}>▶</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: { 
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,               
    borderColor: 'transparent',
  },
  selectedWrapper: { 
    borderColor: '#98cbf1',
    borderStyle: 'dashed'
  },
  
  // 모서리 버튼들 공통 및 개별 스타일 정의 (규격 및 좌표 통일)
  confirmBtn: { 
    position: 'absolute', 
    top: -10, 
    left: -10, 
    backgroundColor: '#98cbf1', // 💡 요청하신 파란색 배경
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    justifyContent: 'center', 
    alignItems: 'center', 
    elevation: 3, 
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 2, 
    shadowOffset: { width: 0, height: 1 } 
  },
  deleteBtn: { 
    position: 'absolute', 
    top: -10, 
    right: -10, 
    backgroundColor: '#ff6b6b', 
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    justifyContent: 'center', 
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 2, 
    shadowOffset: { width: 0, height: 1 } 
  },
  resizeBtn: { 
    position: 'absolute', 
    bottom: -10, 
    left: -10,
    backgroundColor: 'white', // 하얀 배경
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    justifyContent: 'center', 
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 2, 
    shadowOffset: { width: 0, height: 1 } 
  },
  shrinkBtn: { 
    position: 'absolute', 
    bottom: -10, 
    right: -10,
    backgroundColor: 'white', // 하얀 배경
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    justifyContent: 'center', 
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 2, 
    shadowOffset: { width: 0, height: 1 } 
  },
  
  iconText: { 
    fontFamily: 'Galmuri9',
    color: '#333', 
    fontSize: 12, // 💡 기본 크기 12px (+, - 버튼은 인라인 스타일로 16px 적용)
    includeFontPadding: false,
    textAlignVertical: 'center'
  },

  // 💡 방향키 버튼 바: "리퀴드 글래스" 질감 및 우윳빛 색상 적용
  moveControlBar: {
    flexDirection: 'row',
    position: 'absolute',
    top: '100%',
    left: '50%', // 중앙 정렬용
    marginLeft: -66, // 가로 폭(28*4+6*3+4*2)의 절반값
    marginTop: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.9)', // 💡 우윳빛 질감 및 투명도
    borderRadius: 14, // 💡 더 둥근 모서리
    padding: 4,
    gap: 6,
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 2 },
  },
  arrowBtn: {
    padding: 4,
    backgroundColor: '#EAEAEA', // 회색 네모 배경 (기존 느낌 유지)
    borderRadius: 8, // 조금 더 둥글게
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  arrowText: {
    fontFamily: 'Galmuri9',
    fontSize: 10, // 화살표 크기 미세 조정
    color: '#333',
    includeFontPadding: false,
    textAlignVertical: 'center'
  }
});

export default ResizableElement;