import React, { useState, ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Ionicons from 'react-native-vector-icons/Ionicons';
import { COLORS } from './assets/Maincolors';

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
            style={styles.checkboxContainer}
        >
            
            {children && (
                <Text
                    style={{marginLeft: 12, flex: 1, fontSize: 12, color: 'black'}}
                    numberOfLines={1}
                    adjustsFontSizeToFit
                    minimumFontScale={0.7}
                >
                    {children}
                </Text>
            )}
            <View style = {[styles.checkboxBase, checked && styles.checkboxChecked]}>
                {checked && <Ionicons name="checkmark" size={40} color = "black"/>}
            </View>
        </Pressable>
    )
}

const styles = StyleSheet.create({
    checkboxContainer:{
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 8,
        flexDirection: 'row',
        backgroundColor: COLORS.bar,
        borderRadius: 11,
        marginVertical: 8,
    },
  checkboxBase: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 7,
    borderWidth: 4,
    borderColor: 'black',
    backgroundColor: 'transparent',
  },
  checkboxChecked: {
    backgroundColor: "#FFFFFF30",
  },
});


export default Checkbox;