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
  // 기본 드래그 이동을 위한 PanResponder
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
      {/* 스티커 본체 */}
      <TouchableOpacity activeOpacity={1} onPress={() => onSelect(el.id)} {...panResponder.panHandlers}>
        {el.stickerType === 'image' ? (
          <Image source={el.source} style={{ width: el.size, height: el.size, resizeMode: 'contain' }} />
        ) : (
          <Text style={{ fontSize: el.size }}>{el.content}</Text>
        )}
      </TouchableOpacity>

      {/* 선택 시 나타나는 상하좌우 모서리 제어 버튼들 */}
      {isSelected && (
        <>
          {/* 확인 버튼: 왼쪽 위 */}
          <TouchableOpacity style={styles.confirmBtn} onPress={() => onSelect(null)}>
            <Text style={{ fontSize: 12 }}>✅</Text>
          </TouchableOpacity>

          {/* 삭제 버튼: 오른쪽 위 */}
          <TouchableOpacity style={styles.deleteBtn} onPress={() => onRemove(el.id)}>
            <Text style={styles.btnText}>✕</Text>
          </TouchableOpacity>

          {/* 확대 버튼: 오른쪽 아래 */}
          <TouchableOpacity style={styles.resizeBtn} onPress={() => onUpdate(el.id, { size: el.size + 10 })}>
            <Text style={styles.btnText}>➕</Text>
          </TouchableOpacity>

          {/* 축소 버튼: 왼쪽 아래 */}
          <TouchableOpacity style={styles.shrinkBtn} onPress={() => onUpdate(el.id, { size: Math.max(20, el.size - 10) })}>
            <Text style={styles.btnText}>➖</Text>
          </TouchableOpacity>

          {/* 💡 새로 추가된 하단 이동 제어 방향키 버튼 바 */}
          <View style={styles.moveControlBar}>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { y: (el.y || 0) - 5 })}>
              <Text style={styles.arrowText}>⬆️</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { y: (el.y || 0) + 5 })}>
              <Text style={styles.arrowText}>⬇️</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { x: (el.x || 0) - 5 })}>
              <Text style={styles.arrowText}>⬅️</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.arrowBtn} onPress={() => onUpdate(el.id, { x: (el.x || 0) + 5 })}>
              <Text style={styles.arrowText}>➡️</Text>
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
    borderWidth: 2,               // 💡 투명한 2px 테두리로 자리 확보
    borderColor: 'transparent',
  },
  selectedWrapper: { 
    borderColor: '#7ec96d',       // 💡 선택 시 색깔만 짠! 하고 나타나게
    borderStyle: 'dashed'
  },
  
  // 모서리 버튼들 스타일
  confirmBtn: { 
    position: 'absolute', 
    top: -10, 
    left: -10, 
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
    alignItems: 'center' 
  },
  resizeBtn: { 
    position: 'absolute', 
    bottom: -10, 
    right: -10, 
    backgroundColor: '#7ec96d', 
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  shrinkBtn: { 
    position: 'absolute', 
    bottom: -10, 
    left: -10, 
    backgroundColor: '#7ec96d', 
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  btnText: { 
    color: 'white', 
    fontSize: 12, 
    fontWeight: 'bold' 
  },

  // 💡 하단 미세 이동 버튼 바 스타일
  moveControlBar: {
    flexDirection: 'row',
    position: 'absolute',
    top: '100%',
    marginTop: 18,
    backgroundColor: 'white',
    borderRadius: 10,
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
    backgroundColor: '#f5f5f5',
    borderRadius: 6,
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrowText: {
    fontSize: 14,
  }
});

export default ResizableElement;