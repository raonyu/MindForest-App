import React, { useState } from 'react';
import {Modal, View, Text, TouchableOpacity, StyleSheet} from 'react-native';
import { COLORS } from './assets/Maincolors';


//결과 데이터 구조
export interface ReportItems{
    report_explain: string;
    report_value: any;
}

export interface ReportResult {
    [key: string]: ReportItems;
}

interface ReportModalProps {
    isVisible: boolean;
    data: ReportResult | null;
    onClose: () => void;
}

const ReportModal = ({isVisible, data, onClose}: ReportModalProps) => {
    if (!data) return null;
    const [currentIndex, setCurrentIndex] = useState(0);
    const currentKey = `indicator_${currentIndex + 1}`;
    const currentData = data[currentKey];



    const reportTitles = ["주간 지배 감정", "마음 온도", "감정 롤러코스터", "루틴 효능 랭킹", "마음의 빈자리", "감정 레드 존", "마음 안전망 방어", "마음의 가면", "아픔의 뿌리", "위기 도달 확률"];

    //카드 위쪽 부분 렌더링
    const RenderCardImg = ({index}: {index: number}) => {
        switch(index){
            case 0:
                return <View style={[styles.cardImg, { backgroundColor: "blue"}]}><Text style = {{fontSize: 128, textAlign: 'center'}}>{currentData.report_value}</Text></View>
            case 1:
                return <View style={[styles.cardImg, { backgroundColor: "green"}]}><Text style = {{fontSize: 128, textAlign: 'center'}}>{currentData.report_value.msg}</Text></View>
        }
    }

    return(
        <Modal transparent = {true} visible={isVisible} animationType='fade' onRequestClose={onClose}>
            <TouchableOpacity style={styles.overlay} activeOpacity={1} onPressOut={onClose}>
            <View style={styles.card}>
                <RenderCardImg index={currentIndex}></RenderCardImg>
                <View style={styles.cardDetail}>
                    <Text
                        style={{fontSize: 36, fontWeight: 'bold', width: '100%', padding: 4}}
                        numberOfLines={1}
                        minimumFontScale={0.1}>
                            {reportTitles[currentIndex]}
                    </Text>
                    <Text style={{fontSize: 18, marginTop: 8}}>{currentData.report_explain}</Text>
                    <TouchableOpacity style={styles.closeButton} onPress={()=>{setCurrentIndex(prev=>prev+1)}}>
                        <Text style={{ color: 'white',fontSize: 24}}>다음</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.closeButton} onPress={()=>{setCurrentIndex(prev=>prev-1)}}>
                        <Text style={{ color: 'white',fontSize: 24}}>이전</Text>
                    </TouchableOpacity>
                </View>
            </View>
            </TouchableOpacity>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    card: {
        width: 336,
        height: 512,
        borderRadius: 26,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
    },
    cardImg: {
        borderTopLeftRadius: 26,
        borderTopRightRadius: 26,
        width: '100%',
        height: '60%',
        backgroundColor: COLORS.user,
        top: 0,
    },
    cardDetail: {
        paddingTop: 4,
        width: '100%',
        height: '40%',
        backgroundColor: 'COLORS.background',
        borderBottomLeftRadius: 26,
        borderBottomRightRadius: 26,
        padding:20,
        alignItems: 'center',
    },
    closeButton: {
        width: 216,
        height: 56,
        backgroundColor: COLORS.user,
        marginTop: 'auto',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 28,
    }
});


export default ReportModal;
