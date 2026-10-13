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
  const startPos = useRef({ x: el.x || 0, y: el.y || 0 });

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderGrant: () => {
        startPos.current = { x: el.x || 0, y: el.y || 0 };
      },
      onPanResponderMove: (evt, gestureState) => {
        onUpdate(el.id, {
          x: startPos.current.x + gestureState.dx,
          y: startPos.current.y + gestureState.dy,
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
          {/* 확인 버튼: O  */}
          <TouchableOpacity style={styles.confirmBtn} onPress={() => onSelect(null)}>
            <Text style={[styles.iconText, { color: 'white' }]}>O</Text>
          </TouchableOpacity>

          {/* 삭제 버튼: X */}
          <TouchableOpacity style={styles.deleteBtn} onPress={() => onRemove(el.id)}>
            <Text style={[styles.iconText, { color: 'white' }]}>X</Text>
          </TouchableOpacity>

          {/* 확대 버튼 (+) */}
          <TouchableOpacity style={styles.resizeBtn} onPress={() => onUpdate(el.id, { size: el.size + 10 })}>
            <Text style={[styles.iconText, { fontSize: 16 }]}>+</Text>
          </TouchableOpacity>

          {/* 축소 버튼 (-) */}
          <TouchableOpacity style={styles.shrinkBtn} onPress={() => onUpdate(el.id, { size: Math.max(20, el.size - 10) })}>
            <Text style={[styles.iconText, { fontSize: 16 }]}>-</Text>
          </TouchableOpacity>

          {/* 방향키 버튼 바 */}
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
    backgroundColor: '#98cbf1',
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
  shrinkBtn: { 
    position: 'absolute', 
    bottom: -10, 
    right: -10,
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
  
  iconText: { 
    fontFamily: 'Galmuri9',
    color: '#333', 
    fontSize: 12,
    includeFontPadding: false,
    textAlignVertical: 'center'
  },

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
  arrowBtn: {
    padding: 4,
    backgroundColor: '#EAEAEA', 
    borderRadius: 8,
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  arrowText: {
    fontFamily: 'Galmuri9',
    fontSize: 10,
    color: '#333',
    includeFontPadding: false,
    textAlignVertical: 'center'
  }
});

export default ResizableElement;