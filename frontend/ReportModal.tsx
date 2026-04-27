import React, { useState } from 'react';
import {Modal, View, Text, TouchableOpacity, StyleSheet} from 'react-native';
import { COLORS } from './assets/Maincolors';
import {LineChart} from 'react-native-chart-kit';
import { AnimatedCircularProgress } from 'react-native-circular-progress';


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



    const reportTitles = ["주간 지배 감정", "현재 마음 온도", "감정 롤러코스터 지수", "회복 탄력성", "루틴 효능 랭킹", "기록 성공률", "에너지 변화", "마음 안전망 방어", "레드존 확인", "마음의 가면", "아픔의 뿌리", "위기 도달 확률"];

    //카드 위쪽 부분 렌더링(보이는부분)
    const RenderCardImg = ({index}: {index: number}) => {
        switch(index){
            case 0:
                return <View style={[styles.cardImg, { backgroundColor: "blue"}]}><Text style = {{fontSize: 128, textAlign: 'center'}}>{currentData.report_value}</Text></View>
            case 1://마음 온도
                return(
                    <View style={[styles.cardImg, { backgroundColor: COLORS.user, justifyContent: 'center', alignItems: 'center'}]}>
                        <View>
                            <Text style = {{fontSize: 64, textAlign: 'center', color: 'white', fontWeight: 'bold'}}>{currentData.report_value.temp}°C</Text>
                            <Text style = {{fontSize: 16, textAlign: 'center', color: 'white', fontWeight: 'bold'}}>지난 주 보다 {currentData.report_value.msg}°C 상승</Text>

                        </View>
                        
                    </View>)
            case 2://감정 롤러코스터 그래프
                interface chartData{created_at: string; temp_val: number};
                const chartDate = currentData.report_value.map((item: chartData) => item.created_at.substring(5).replace('-', '/'));
                const chartValue = currentData.report_value.map((item: chartData) => Number(item.temp_val));
                return(
                    <View style={[styles.cardImg, { backgroundColor: "#A7C7E7", flexDirection: 'row', alignItems: 'flex-end'}]}>
                        <LineChart
                            data={{labels: chartDate, datasets: [{data: chartValue}]}}
                            width = {320}
                            height = {220}
                            style={{margin: 32}}
                            chartConfig={{
                                backgroundColor: "#A7C7E7", // 예시 이미지와 유사한 밝은 연청색
                                backgroundGradientFrom: "#A7C7E7",
                                backgroundGradientTo: "#A7C7E7",
                                decimalPlaces: 1, // 소수점 첫째자리까지 표시
                                color: (opacity = 1) => `rgba(138, 43, 226, ${opacity})`, // 보라색 선 (opacity 조절로 그라데이션 효과)
                                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`, // 검은색 라벨
                                style: {
                                    borderRadius: 16
                                    },
                                    propsForDots: {
                                    r: "6", // 점 크기
                                    strokeWidth: "2",
                                    stroke: "#8A2BE2" // 점 테두리 보라색
                                }
                            }}
                        />
                    </View>)
            case 3://회복 탄력성
                return(
                    <View style={[styles.cardImg, { backgroundColor: "#4d824f"}]}>
                        <Text style = {{fontSize: 60, textAlign: 'center', color: "#b7e6a4"}}>{currentData.report_value}</Text>
                        <View></View>
                    </View>
                )
            case 4://루틴 효능 랭킹
                interface RoutineData{
                    routine: string;
                    effect: number;
                }
                const data: RoutineData[] = currentData.report_value;
                const MAX_BAR_WIDTH = 240;
                return(
                    <View style={[styles.cardImg, { backgroundColor: "#4d824f", flexDirection: 'row', alignItems: 'flex-end'}]}>
                        <View style={{flexDirection: 'row', alignItems: 'flex-end', margin: 32}}>
                            {data.map((item, index) =>(
                                <View key={index} style={{alignItems: 'center', marginLeft: 12}}>           {/*boxWrapper*/}
                                    <View style={{height: MAX_BAR_WIDTH * (item.effect / 100), width: 48, backgroundColor: "#B7E6A4"}}>
                                        <Text style={{color: "#4d824f", width: 45, textAlign: 'center', fontSize: 20, fontWeight: 'bold'}}>{item.effect}</Text>
                                    </View>
                                    <Text style={{fontSize: 20, color: "#B7E6A4"}}>{item.routine}</Text>
                                </View>
                            ))}
                        </View>
                    </View>
                )
            case 5://기록 성공률
                return(
                    <View style={[styles.cardImg, { backgroundColor: "blue",flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}]}>
                        <Text style = {{fontSize: 64, textAlign: 'center', fontWeight: 'bold', color: 'white'}}>{currentData.report_value}/14</Text>
                    </View>
                )
            case 6://에너지 변화
                return(
                    <View style={[styles.cardImg, { backgroundColor: "blue",flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}]}>
                        <Text style = {{fontSize: 64, textAlign: 'center', fontWeight: 'bold', color: 'white'}}>{currentData.report_value}/14</Text>
                    </View>
                )
            case 7://마음 안전망 방어
                return(
                    <View style={[styles.cardImg, { backgroundColor: "#7D8D98",flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}]}>
                        <Text style = {{fontSize: 64, textAlign: 'center', fontWeight: 'bold', color: 'white'}}>{"🛡️️".repeat(currentData.report_value)}</Text>
                    </View>
                )
            case 8://레드존 확인
                return(
                    <View style={[styles.cardImg, { backgroundColor: "#970D32",flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}]}>
                        <Text style = {{fontSize: 64, textAlign: 'center', fontWeight: 'bold', color: 'white'}}>{currentData.report_value}</Text>
                    </View>
                )
            case 11://위기 도달 확률
                return(
                    <View style={[styles.cardImg, { backgroundColor: "#571314",flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}]}>
                        <AnimatedCircularProgress
                            size={200}
                            width={25}
                            fill={Number(currentData.report_value)}
                            tintColor="#B53511"
                            backgroundColor="#2D1714"
                            lineCap="butt"
                            rotation={0}
                        >
                            {() => (<Text style={{fontSize: 40, color: 'white', fontWeight: 'bold'}}>{currentData.report_value}%</Text>)}
                        </AnimatedCircularProgress>
                    </View>
                )
            default: return <View style={[styles.cardImg, { backgroundColor: COLORS.user,flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}]}></View>
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
                    <Text style={{fontSize: 18, marginTop: 8, alignSelf: 'flex-start'}}>{currentData.report_explain}</Text>
                    <View style={{flexDirection: 'row', marginTop: 'auto'}}>
                        <TouchableOpacity style={[styles.closeButton, {backgroundColor: '#A4A4A4'}]} onPress={()=>{setCurrentIndex(prev=>prev-1)}}>
                            <Text style={{ color: 'white',fontSize: 24}}>이전</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={styles.closeButton} onPress={()=>{setCurrentIndex(prev=>prev+1)}}>
                            <Text style={{ color: 'white',fontSize: 24}}>다음</Text>
                        </TouchableOpacity>
                    </View>
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
        width: 128,
        height: 52,
        backgroundColor: COLORS.user,
        marginTop: 'auto',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 28,
    }

});


export default ReportModal;
