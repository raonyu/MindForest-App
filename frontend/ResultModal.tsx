import {Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';


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
            <View style={styles.modalContent}>
                <Text>심리검사 결과</Text>
                <View><Text>{data.result_emoji}</Text></View>
                <Text>{data.result_name}</Text>
                <TouchableOpacity onPress={onClose}>
                    <Text>닫기</Text>
                </TouchableOpacity>
            </View>
            
        </Modal>
    );
}

const styles = StyleSheet.create({
    modalContent: {
        width: 300,
        height: 200,
        borderRadius: 16,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
    },
});


export default ResultModal;
