import React, { useState, ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface CheckboxProps {
  initialValue?: boolean;
  onCheck?: () => void;   // 체크될 때 실행할 함수
  onUncheck?: () => void; // 해제될 때 실행할 함수
  children? : ReactNode;
}

const Checkbox = ({initialValue = false, onCheck, onUncheck, children}:CheckboxProps)=>{
    const [checked, setchecked] = useState(initialValue);
    const checkboxPress = () =>{
        const currentValue = !checked;//체크하면 상태 바뀜
        setchecked(currentValue);
        
        if (currentValue == true){
            onCheck?.();
        }else{
            onUncheck?.();
        }
    }
    return(
        <Pressable
            onPress = {checkboxPress}
            style={{flexDirection: "row", marginVertical: 5}}
        >
            <View style = {[styles.checkboxBase, checked && styles.checkboxChecked]}>
                {checked && <Ionicons name="checkmark" size={18} color = "white"/>}
            </View>
            {children && <View style={{marginLeft: 12}}>{children}</View>}
        </Pressable>
    )
}

const styles = StyleSheet.create({
  checkboxBase: {
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 4,
    borderWidth: 2,
    borderColor: 'coral',
    backgroundColor: 'transparent',
  },
  checkboxChecked: {
    backgroundColor: 'coral',
  },
});


export default Checkbox;