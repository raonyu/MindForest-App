import {Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS } from './assets/Maincolors';


//결과 데이터 구조
export interface SurveyResult {
    isComplete: boolean;
    result_emoji: string;
    result_name: string;
}


interface ResultModalProps {
    isVisible: boolean;
    data: SurveyResult | null;
    onClose: () => void;
}

const ResultModal = ({isVisible, data, onClose}: ResultModalProps) => {
    if (!data) return null;
    return(
        <Modal transparent = {true} visible={isVisible} animationType='fade' onRequestClose={onClose}>
            <TouchableOpacity style={styles.overlay} activeOpacity={1} onPressOut={onClose}>
            <View style={styles.card}>
                <View style={styles.cardImg}>
                    <Text style={{fontSize: 24,textAlign: 'center', color: 'white', marginTop: 16}}>심리검사 결과</Text>
                    <Text style = {{fontSize: 128, textAlign: 'center'}}>{data.result_emoji}</Text></View>
                <View style={styles.cardDetail}>
                    <Text
                        style={{fontSize: 36, textAlign: 'center', fontWeight: 'bold', width: '100%', padding: 4}}
                        numberOfLines={1}
                        minimumFontScale={0.1}>{data.result_name}</Text>
                    <TouchableOpacity style={styles.closeButton} onPress={onClose}>
                        <Text style={{ color: 'white',fontSize: 24}}>확인</Text>
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


export default ResultModal;
