import React from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, ScrollView, Dimensions, SafeAreaView } from 'react-native';
import { COLORS } from './assets/Maincolors';
import { LineChart } from 'react-native-chart-kit';
import { AnimatedCircularProgress } from 'react-native-circular-progress';

//결과 데이터 구조
export interface ReportItems {
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

const screenWidth = Dimensions.get('window').width;

const reportTitles = [
    "주간 지배 감정", "현재 마음 온도", "감정 롤러코스터 지수", "회복 탄력성",
    "루틴 효능 랭킹", "기록 성공률", "에너지 변화", "마음 안전망 방어",
    "레드존 확인", "마음의 가면", "아픔의 뿌리", "위기 도달 확률"
];

const getTemperatureColor = (tempStr: string | number) => {
    // 온도를 0~100 사이로 제한
    const temp = Math.max(0, Math.min(100, parseFloat(String(tempStr)) || 0));
    // 0도일 때는 검은색에 가깝게, 100도에 가까워질수록 빨간색의 채도와 밝기가 상승하도록 처리
    const lightness = 10 + (temp / 100) * 50; // 10% (거의 검은색) ~ 60% (밝은 빨간색)
    const saturation = 20 + (temp / 100) * 80; // 20% ~ 100% (채도 상승)
    
    return `hsl(0, ${saturation}%, ${lightness}%)`;
};

const IndicatorCard = ({ index, data, title }: { index: number, data: any, title: string }) => {
    if (!data) return null;

    // 백엔드 데이터 구조가 일관되지 않을 수 있으므로, report_value로 래핑되어 있는지 확인합니다.
    const hasReportValue = data && typeof data === 'object' && !Array.isArray(data) && 'report_value' in data;
    const reportValue = hasReportValue ? data.report_value : data;
    const reportExplain = hasReportValue ? data.report_explain : null;

    const renderVisualization = () => {
        switch(index) {
            case 0: // 주간 지배 감정
                return (
                    <View style={styles.vizContainer}>
                        <Text style={{ fontSize: 80, textAlign: 'center' }}>{reportValue}</Text>
                    </View>
                );
            case 1: // 현재 마음 온도
                if (!reportValue || typeof reportValue !== 'object') return null;
                const tempValue = reportValue.temp || 0;
                const bgColor = getTemperatureColor(tempValue);
                return (
                    <View style={[styles.vizContainer, { backgroundColor: bgColor, borderRadius: 20, padding: 24, alignItems: 'center' }]}>
                        <Text style={{ fontSize: 48, color: 'white', fontWeight: 'bold' }}>{tempValue}°C</Text>
                        <View style={{ backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, marginTop: 14 }}>
                            <Text style={{ fontSize: 15, color: 'white', fontWeight: '600' }}>지난 주 보다 {reportValue.msg || 0}°C 상승 📈</Text>
                        </View>
                    </View>
                );
            case 2: // 감정 롤러코스터 지수
                const arr2 = Array.isArray(reportValue) ? reportValue : [];
                if (arr2.length === 0) return <Text style={{textAlign: 'center', marginTop: 10, color: '#888'}}>데이터가 부족합니다.</Text>;
                const chartDate = arr2.map((item: any) => item.created_at ? item.created_at.substring(5, 10).replace('-', '/') : '');
                const chartValue = arr2.map((item: any) => Number(item.temp_val) || 0);
                return (
                    <View style={[styles.vizContainer, { alignItems: 'center' }]}>
                        <LineChart
                            data={{ labels: chartDate, datasets: [{ data: chartValue }] }}
                            width={screenWidth - 88} // 화면 여백 고려
                            height={220}
                            chartConfig={{
                                backgroundColor: "#ffffff",
                                backgroundGradientFrom: "#ffffff",
                                backgroundGradientTo: "#ffffff",
                                decimalPlaces: 1,
                                color: (opacity = 1) => `rgba(138, 43, 226, ${opacity})`,
                                labelColor: (opacity = 1) => `rgba(100, 100, 100, ${opacity})`,
                                style: { borderRadius: 16 },
                                propsForDots: { r: "5", strokeWidth: "2", stroke: "#8A2BE2" }
                            }}
                            bezier
                            style={{ borderRadius: 16, marginVertical: 8 }}
                        />
                    </View>
                );
            case 3: // 회복 탄력성
                const num3 = parseFloat(String(reportValue)) || 0;
                return (
                    <View style={[styles.vizContainer, { alignItems: 'center', paddingVertical: 20 }]}>
                         <AnimatedCircularProgress
                            size={160}
                            width={16}
                            fill={num3}
                            tintColor="#4d824f"
                            backgroundColor="#eaffdf"
                            lineCap="round"
                        >
                            {() => <Text style={{ fontSize: 36, fontWeight: 'bold', color: '#4d824f' }}>{typeof reportValue === 'string' ? reportValue : `${num3}%`}</Text>}
                        </AnimatedCircularProgress>
                    </View>
                );
            case 4: // 루틴 효능 랭킹
                const arr4 = Array.isArray(reportValue) ? reportValue : [];
                if (arr4.length === 0) return <Text style={{textAlign: 'center', marginTop: 10, color: '#888'}}>데이터가 부족합니다.</Text>;
                const MAX_HEIGHT = 120;
                return (
                    <View style={[styles.vizContainer, { flexDirection: 'row', justifyContent: 'space-evenly', alignItems: 'flex-end', height: MAX_HEIGHT + 60, marginTop: 20 }]}>
                        {arr4.map((item: any, idx: number) => (
                            <View key={idx} style={{ alignItems: 'center', width: 60 }}>
                                <Text style={{ marginBottom: 8, fontWeight: 'bold', color: '#4d824f', fontSize: 16 }}>{item.effect}</Text>
                                <View style={{ width: 44, height: MAX_HEIGHT * ((item.effect || 0) / 100), backgroundColor: idx === 0 ? '#B7E6A4' : '#eaffdf', borderTopLeftRadius: 10, borderTopRightRadius: 10 }} />
                                <Text style={{ marginTop: 10, color: '#555', fontWeight: 'bold' }}>{item.routine}</Text>
                            </View>
                        ))}
                    </View>
                );
            case 5: // 기록 성공률
                const successDays = Number(reportValue) || 0;
                const totalDays = 14;
                const percentage = (successDays / totalDays) * 100;
                return (
                    <View style={[styles.vizContainer, { marginTop: 10 }]}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 12 }}>
                            <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#333' }}>{successDays}<Text style={{ fontSize: 16, color: '#888', fontWeight: 'normal' }}> 일 성공</Text></Text>
                            <Text style={{ fontSize: 16, color: '#888' }}>총 {totalDays}일</Text>
                        </View>
                        <View style={{ height: 20, backgroundColor: '#f0f0f0', borderRadius: 10, overflow: 'hidden' }}>
                            <View style={{ width: `${percentage}%`, height: '100%', backgroundColor: '#81c784' }} />
                        </View>
                    </View>
                );
            case 6: // 에너지 변화
                return (
                    <View style={[styles.vizContainer, { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff8e1', padding: 24, borderRadius: 20, marginTop: 10 }]}>
                         <Text style={{ fontSize: 48 }}>⚡</Text>
                         <Text style={{ fontSize: 32, fontWeight: 'bold', color: '#f57c00', marginLeft: 16 }}>{reportValue}° 변화</Text>
                    </View>
                );
            case 7: // 마음 안전망 방어
                const defenseCount = Number(reportValue) || 0;
                return (
                    <View style={[styles.vizContainer, { backgroundColor: '#f0f4f8', padding: 20, borderRadius: 20, marginTop: 10, alignItems: 'center' }]}>
                        <Text style={{ fontSize: 18, color: '#455a64', marginBottom: 16, fontWeight: 'bold' }}>이번 주 {defenseCount}번의 하락 방어</Text>
                        <View style={{ flexDirection: 'row', justifyContent: 'center', flexWrap: 'wrap', gap: 12 }}>
                            {Array.from({ length: defenseCount }).map((_, i) => (
                                <Text key={i} style={{ fontSize: 36 }}>🛡️</Text>
                            ))}
                        </View>
                    </View>
                );
            case 8: // 레드존 확인
                const redZones = Array.isArray(reportValue) ? reportValue : [];
                if (redZones.length === 0) return <Text style={{textAlign: 'center', marginTop: 10, color: '#888'}}>레드존이 감지되지 않았습니다.</Text>;
                return (
                    <View style={[styles.vizContainer, { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 10 }]}>
                        {redZones.map((zone: any, idx: number) => (
                            <View key={idx} style={{ backgroundColor: '#ffebee', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 24, borderWidth: 1, borderColor: '#ffcdd2' }}>
                                <Text style={{ color: '#d32f2f', fontWeight: 'bold', fontSize: 16 }}>🔴 {zone}일</Text>
                            </View>
                        ))}
                    </View>
                );
            case 9: // 마음의 가면
                if (!reportValue || typeof reportValue !== 'object') return null;
                const { user, ai, gap } = reportValue as any;
                return (
                    <View style={[styles.vizContainer, { marginTop: 10 }]}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 }}>
                            <View style={{ alignItems: 'center', backgroundColor: '#f1f8e9', padding: 16, borderRadius: 16, width: '47%' }}>
                                <Text style={{ fontSize: 14, color: '#555', marginBottom: 8 }}>나의 느낌</Text>
                                <Text style={{ fontSize: 28, fontWeight: 'bold', color: '#388e3c' }}>{user}°</Text>
                            </View>
                            <View style={{ alignItems: 'center', backgroundColor: '#e3f2fd', padding: 16, borderRadius: 16, width: '47%' }}>
                                <Text style={{ fontSize: 14, color: '#555', marginBottom: 8 }}>AI 분석</Text>
                                <Text style={{ fontSize: 28, fontWeight: 'bold', color: '#1976d2' }}>{ai}°</Text>
                            </View>
                        </View>
                        <View style={{ backgroundColor: '#fff', borderWidth: 1, borderColor: '#eee', padding: 16, borderRadius: 12, alignItems: 'center' }}>
                            <Text style={{ fontSize: 16, color: '#333' }}>
                                감정 괴리: <Text style={{ fontWeight: 'bold', color: '#d32f2f', fontSize: 18 }}> {gap}°C</Text>
                            </Text>
                        </View>
                    </View>
                );
            case 10: // 아픔의 뿌리
                const keywords = Array.isArray(reportValue) ? reportValue : [];
                if (keywords.length === 0) return <Text style={{textAlign: 'center', marginTop: 10, color: '#888'}}>감지된 키워드가 없습니다.</Text>;
                return (
                    <View style={[styles.vizContainer, { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 10 }]}>
                        {keywords.map((kw: any, idx: number) => (
                            <View key={idx} style={{ backgroundColor: '#e0f2f1', paddingHorizontal: 18, paddingVertical: 12, borderRadius: 24, borderWidth: 1, borderColor: '#b2dfdb' }}>
                                <Text style={{ color: '#00796b', fontWeight: 'bold', fontSize: 16 }}># {kw}</Text>
                            </View>
                        ))}
                    </View>
                );
            case 11: // 위기 도달 확률
                const num11 = parseFloat(String(reportValue)) || 0;
                return (
                    <View style={[styles.vizContainer, { alignItems: 'center', paddingVertical: 10 }]}>
                        <AnimatedCircularProgress
                            size={180}
                            width={18}
                            fill={num11}
                            tintColor="#d32f2f"
                            backgroundColor="#ffebee"
                            lineCap="round"
                            rotation={0}
                            arcSweepAngle={240}
                        >
                            {() => (
                                <View style={{ alignItems: 'center' }}>
                                    <Text style={{ fontSize: 40, color: '#d32f2f', fontWeight: 'bold' }}>{num11}%</Text>
                                    <Text style={{ fontSize: 14, color: '#777', marginTop: 4 }}>위험도</Text>
                                </View>
                            )}
                        </AnimatedCircularProgress>
                    </View>
                );
            default:
                return null;
        }
    };

    return (
        <View style={styles.card}>
            <Text style={styles.cardTitle}>{title}</Text>
            {reportExplain && <Text style={styles.cardExplain}>{reportExplain}</Text>}
            {renderVisualization()}
        </View>
    );
};

const ReportModal = ({ isVisible, data, onClose }: ReportModalProps) => {
    if (!data) {
        return (
            <Modal transparent={true} visible={isVisible} animationType='slide' onRequestClose={onClose}>
                <View style={styles.overlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.header}>
                            <Text style={styles.headerTitle}>주간 감성 리포트</Text>
                            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                                <Text style={styles.closeBtnText}>✕</Text>
                            </TouchableOpacity>
                        </View>
                        <View style={styles.emptyContainer}>
                            <Text style={styles.emptyText}>데이터가 없습니다</Text>
                        </View>
                    </View>
                </View>
            </Modal>
        );
    }

    return (
        <Modal transparent={true} visible={isVisible} animationType='slide' onRequestClose={onClose}>
            <View style={styles.overlay}>
                <SafeAreaView style={styles.modalContent}>
                    <View style={styles.header}>
                        <Text style={styles.headerTitle}>주간 감성 리포트</Text>
                        <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                            <Text style={styles.closeBtnText}>✕</Text>
                        </TouchableOpacity>
                    </View>
                    
                    <ScrollView 
                        contentContainerStyle={styles.scrollContent}
                        showsVerticalScrollIndicator={false}
                    >
                        {reportTitles.map((title, index) => {
                            const key = `indicator_${index + 1}`;
                            const itemData = data[key];
                            if (!itemData) return null;
                            return (
                                <IndicatorCard 
                                    key={key} 
                                    index={index} 
                                    data={itemData} 
                                    title={title} 
                                />
                            );
                        })}
                    </ScrollView>
                </SafeAreaView>
            </View>
        </Modal>
    );
};

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        justifyContent: 'flex-end',
    },
    modalContent: {
        backgroundColor: '#f5f7fa',
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        height: '90%',
        width: '100%',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 20,
        backgroundColor: '#ffffff',
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        borderBottomWidth: 1,
        borderBottomColor: '#f0f0f0',
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
    },
    closeBtn: {
        position: 'absolute',
        right: 20,
        padding: 10,
    },
    closeBtnText: {
        fontSize: 20,
        color: '#888',
        fontWeight: 'bold',
    },
    scrollContent: {
        padding: 20,
        paddingBottom: 50,
    },
    card: {
        backgroundColor: '#ffffff',
        borderRadius: 24,
        padding: 24,
        marginBottom: 20,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.05,
        shadowRadius: 12,
        elevation: 3,
    },
    cardTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#2a3a21',
        marginBottom: 8,
    },
    cardExplain: {
        fontSize: 15,
        color: '#666',
        marginBottom: 16,
        lineHeight: 22,
    },
    vizContainer: {
        marginTop: 4,
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    emptyText: {
        fontSize: 16,
        color: '#888',
    }
});

export default ReportModal;
