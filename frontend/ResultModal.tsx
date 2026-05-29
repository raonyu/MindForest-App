import React from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';

//결과 데이터 구조
export interface SurveyResult {
    isComplete: boolean;
    result_emoji: string;
    result_name: string;
    result_description?: string;
}

interface ResultModalProps {
    isVisible: boolean;
    data: SurveyResult | null;
    onClose: () => void;
}

const { width } = Dimensions.get('window');

const ResultModal = ({ isVisible, data, onClose }: ResultModalProps) => {
    if (!data) return null;
    return (
        <Modal transparent={true} visible={isVisible} animationType='fade' onRequestClose={onClose}>
            <TouchableOpacity style={styles.overlay} activeOpacity={1} onPressOut={onClose}>
                <View style={styles.card} onStartShouldSetResponder={() => true}>
                    <View style={styles.emojiContainer}>
                        <Text style={styles.headerText}>분석 완료!</Text>
                        <Text style={styles.emojiText}>{data.result_emoji || '🌱'}</Text>
                    </View>
                    
                    <View style={styles.detailContainer}>
                        <Text style={styles.subText}>당신의 마음 속 동물은</Text>
                        <Text 
                            style={styles.resultNameText}
                            numberOfLines={2}
                            adjustsFontSizeToFit={true}
                            minimumFontScale={0.5}
                        >
                            {data.result_name || '결과를 불러오는 중...'}
                        </Text>
                        {data.result_description && (
                            <Text style={styles.descriptionText}>
                                {data.result_description}
                            </Text>
                        )}
                    </View>

                    <TouchableOpacity style={styles.primaryButton} activeOpacity={0.8} onPress={onClose}>
                        <Text style={styles.primaryButtonText}>결과 확인하기</Text>
                    </TouchableOpacity>
                </View>
            </TouchableOpacity>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 24,
    },
    card: {
        width: width - 48,
        maxWidth: 400,
        backgroundColor: '#ffffff',
        borderRadius: 32,
        padding: 24,
        shadowColor: '#8c7ae6',
        shadowOffset: { width: 0, height: 12 },
        shadowOpacity: 0.12,
        shadowRadius: 24,
        elevation: 5,
        alignItems: 'center',
    },
    emojiContainer: {
        width: '100%',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 32,
        backgroundColor: '#f8f9fa',
        borderRadius: 24,
        marginBottom: 24,
    },
    headerText: {
        fontSize: 16,
        color: '#8c7ae6',
        fontWeight: 'bold',
        marginBottom: 12,
        fontFamily: 'NanumSquareRoundB',
    },
    emojiText: {
        fontSize: 110,
    },
    detailContainer: {
        width: '100%',
        alignItems: 'center',
        marginBottom: 32,
    },
    subText: {
        fontSize: 15,
        color: '#636e72',
        marginBottom: 8,
        fontFamily: 'NanumSquareRoundR',
    },
    resultNameText: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#2d3436',
        textAlign: 'center',
        fontFamily: 'NanumSquareRoundB',
    },
    descriptionText: {
        fontSize: 14,
        color: '#636e72',
        textAlign: 'center',
        marginTop: 16,
        lineHeight: 22,
        fontFamily: 'NanumSquareRoundR',
        paddingHorizontal: 16,
    },
    primaryButton: {
        backgroundColor: '#8c7ae6',
        borderRadius: 20,
        paddingVertical: 18,
        alignItems: 'center',
        width: '100%',
    },
    primaryButtonText: {
        color: '#ffffff',
        fontSize: 16,
        fontWeight: 'bold',
        fontFamily: 'NanumSquareRoundB',
    }
});

export default ResultModal;
