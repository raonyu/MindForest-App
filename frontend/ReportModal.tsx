import React, { useState } from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, ScrollView, Dimensions, SafeAreaView } from 'react-native';
import { LineChart } from 'react-native-chart-kit';

/* 백엔드(services/weekly_report.py)가 내려주는 카드 구조 */
export type CardStatus = 'ready' | 'building' | 'insufficient' | 'processing';

export interface ReportCard<T = any> {
    status: CardStatus;
    message: string | null;
    data: T | null;
}

export interface EmotionValue {
    emotion: string;
    label: string;
    emoji: string;
    score?: number;
}

export interface WeeklyReport {
    status: string;
    generated_at?: string;
    period?: { start: string; end: string; days: number };
    consistency?: { days_recorded: number; days_total: number };
    card_status?: Record<string, CardStatus>;
    cards: Record<string, ReportCard>;
    message?: string;
}

interface ReportModalProps {
    isVisible: boolean;
    data: WeeklyReport | null;
    onClose: () => void;
}

const screenWidth = Dimensions.get('window').width;

const DEFAULT_MESSAGE: Record<CardStatus, string> = {
    ready: '',
    building: '조금 더 기록하면 분석을 시작할 수 있어요.',
    insufficient: '아직 기록이 충분하지 않아요.\n조금 더 기록하면 이 분석을 확인할 수 있어요.',
    processing: '숲지기가 최근 기록을 분석하고 있어요.',
};

const LEVEL_STYLE: Record<string, { label: string; color: string; background: string }> = {
    LOW: { label: '안정', color: '#2f6b4f', background: '#e4f1e9' },
    MEDIUM: { label: '주의', color: '#9a6412', background: '#f8eeda' },
    HIGH: { label: '집중 관리', color: '#a8402f', background: '#f7e2dd' },
};

/* 상승/하락은 방향을 반드시 함께 표시한다 (절댓값만 쓰지 않는다) */
const directionMark = (direction?: string) => {
    if (direction === 'up') return '▲';
    if (direction === 'down') return '▼';
    return '―';
};

const directionColor = (direction?: string, upIsGood = true) => {
    if (direction === 'flat' || !direction) return '#666';
    const good = direction === 'up' ? upIsGood : !upIsGood;
    return good ? '#2f6b4f' : '#a8402f';
};

const formatDate = (iso: string) => (iso.length >= 10 ? `${iso.substring(5, 7)}/${iso.substring(8, 10)}` : iso);

/* 카드 껍데기: 상태가 ready가 아니면 안내 문구만 보여준다 */
const Card = ({ title, card, children }: { title: string; card?: ReportCard; children?: React.ReactNode }) => {
    if (!card) return null;

    const isReady = card.status === 'ready';
    const hasPartialData = card.status === 'building' && card.data;

    return (
        <View style={styles.card}>
            <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>{title}</Text>
                {!isReady && (
                    <View style={styles.statusBadge}>
                        <Text style={styles.statusBadgeText}>
                            {card.status === 'processing' ? '분석 중' : '준비 중'}
                        </Text>
                    </View>
                )}
            </View>

            {!isReady && (
                <Text style={styles.cardNotice}>{card.message || DEFAULT_MESSAGE[card.status]}</Text>
            )}

            {(isReady || hasPartialData) && <View style={styles.cardBody}>{children}</View>}
        </View>
    );
};

const Note = ({ text }: { text: string }) => <Text style={styles.note}>{text}</Text>;

/* --- Part 1. 현재 상태 --- */

const SummaryCard = ({ card }: { card?: ReportCard }) => {
    const [showEvidence, setShowEvidence] = useState(false);
    if (!card?.data || card.status !== 'ready') return <Card title="현재 상태" card={card} />;

    const { level, message, dominant_emotion, evidence, records } = card.data;
    const style = LEVEL_STYLE[level] || LEVEL_STYLE.LOW;

    return (
        <Card title="현재 상태" card={card}>
            <View style={styles.summaryTop}>
                <View style={[styles.levelPill, { backgroundColor: style.background }]}>
                    <Text style={[styles.levelPillText, { color: style.color }]}>{style.label}</Text>
                </View>
                {dominant_emotion && (
                    <Text style={styles.summaryEmotion}>
                        {dominant_emotion.emoji} {dominant_emotion.label}
                    </Text>
                )}
                <Text style={styles.summaryRecords}>기록 {records}개</Text>
            </View>

            <Text style={styles.summaryMessage}>{message}</Text>

            {Array.isArray(evidence) && evidence.length > 0 && (
                <View>
                    <TouchableOpacity onPress={() => setShowEvidence(!showEvidence)} style={styles.evidenceToggle}>
                        <Text style={styles.evidenceToggleText}>
                            {showEvidence ? '판단 근거 닫기' : '왜 이런 결과가 나왔나요?'}
                        </Text>
                    </TouchableOpacity>
                    {showEvidence && (
                        <View style={styles.evidenceBox}>
                            {evidence.map((item: string, index: number) => (
                                <Text key={index} style={styles.evidenceItem}>• {item}</Text>
                            ))}
                        </View>
                    )}
                </View>
            )}
        </Card>
    );
};

const SpectrumCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data || card.status !== 'ready') return <Card title="주간 감정 스펙트럼" card={card} />;

    const { top3, distribution } = card.data;
    const maxScore = Math.max(...distribution.map((item: EmotionValue) => item.score || 0), 1);

    return (
        <Card title="주간 감정 스펙트럼" card={card}>
            <View style={styles.chipRow}>
                {top3.map((item: EmotionValue, index: number) => (
                    <View key={item.emotion} style={[styles.emotionChip, index === 0 && styles.emotionChipTop]}>
                        <Text style={styles.emotionChipEmoji}>{item.emoji}</Text>
                        <Text style={styles.emotionChipLabel}>{item.label}</Text>
                        <Text style={styles.emotionChipScore}>{item.score}점</Text>
                    </View>
                ))}
            </View>

            <View style={styles.barList}>
                {distribution.map((item: EmotionValue) => (
                    <View key={item.emotion} style={styles.barRow}>
                        <Text style={styles.barLabel}>{item.label}</Text>
                        <View style={styles.barTrack}>
                            <View style={[styles.barFill, { width: `${((item.score || 0) / maxScore) * 100}%` }]} />
                        </View>
                        <Text style={styles.barValue}>{item.score}</Text>
                    </View>
                ))}
            </View>
        </Card>
    );
};

const TrendCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data) return <Card title="마음 온도" card={card} />;

    const { current_avg, comparison, points, days_recorded } = card.data;
    const labels = points.map((point: any) => formatDate(point.date));
    const values = points.map((point: any) => Number(point.value) || 0);

    return (
        <Card title="마음 온도" card={card}>
            <View style={styles.trendTop}>
                <Text style={styles.trendValue}>{current_avg}점</Text>
                {comparison ? (
                    <Text style={[styles.trendDelta, { color: directionColor(comparison.direction) }]}>
                        {directionMark(comparison.direction)} 지난주보다 {comparison.delta}점{' '}
                        {comparison.direction === 'up' ? '상승' : comparison.direction === 'down' ? '하락' : '변화 없음'}
                    </Text>
                ) : (
                    <Text style={styles.trendDeltaMuted}>지난주와 비교할 기록이 아직 없어요</Text>
                )}
            </View>

            {values.length >= 2 && (
                <LineChart
                    data={{ labels, datasets: [{ data: values }] }}
                    width={screenWidth - 88}
                    height={200}
                    chartConfig={{
                        backgroundGradientFrom: '#ffffff',
                        backgroundGradientTo: '#ffffff',
                        decimalPlaces: 0,
                        color: (opacity = 1) => `rgba(47, 107, 79, ${opacity})`,
                        labelColor: (opacity = 1) => `rgba(90, 100, 94, ${opacity})`,
                        propsForDots: { r: '4', strokeWidth: '2', stroke: '#2f6b4f' },
                    }}
                    bezier
                    style={{ borderRadius: 16, marginVertical: 8, marginLeft: -8 }}
                />
            )}
            <Note text={`최근 7일 중 ${days_recorded}일 기록 기준이에요.`} />
        </Card>
    );
};

const SurveyCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data || card.status !== 'ready') return <Card title="검사 점수 변화" card={card} />;

    const { label, latest, previous, delta, direction, note } = card.data;

    return (
        <Card title="검사 점수 변화" card={card}>
            <View style={styles.compareRow}>
                <View style={styles.compareBox}>
                    <Text style={styles.compareCaption}>이전 ({formatDate(previous.date)})</Text>
                    <Text style={styles.compareValue}>{previous.score}점</Text>
                </View>
                <View style={styles.compareBox}>
                    <Text style={styles.compareCaption}>최근 ({formatDate(latest.date)})</Text>
                    <Text style={styles.compareValue}>{latest.score}점</Text>
                </View>
            </View>
            <Text style={[styles.trendDelta, { color: directionColor(direction, false) }]}>
                {directionMark(direction)} {label} 점수가 {delta}점{' '}
                {direction === 'up' ? '올랐어요' : direction === 'down' ? '내렸어요' : '그대로예요'}
            </Text>
            {latest.message ? <Text style={styles.bodyText}>{latest.message}</Text> : null}
            <Note text={note} />
        </Card>
    );
};

/* --- Part 2. 상세 감정 분석 --- */

const CompositeCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data || card.status !== 'ready') return <Card title="복합 감정 데이" card={card} />;

    const { days, note } = card.data;

    return (
        <Card title="복합 감정 데이" card={card}>
            {days.map((day: any, index: number) => (
                <View key={index} style={styles.listRow}>
                    <Text style={styles.listDate}>{formatDate(day.date)}</Text>
                    <View style={styles.listBody}>
                        <Text style={styles.bodyText}>
                            {day.candidates.map((item: EmotionValue) => `${item.emoji} ${item.label}`).join('  ·  ')}
                        </Text>
                        {day.best && <Text style={styles.subText}>가장 가까운 감정: {day.best.label}</Text>}
                    </View>
                </View>
            ))}
            <Note text={note} />
        </Card>
    );
};

const ResilienceCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data || card.status !== 'ready') return <Card title="회복 탄력성" card={card} />;

    const { drop_count, recovered_count, avg_recovery_days, events, days_analyzed } = card.data;

    return (
        <Card title="회복 탄력성" card={card}>
            {drop_count === 0 ? (
                <Text style={styles.bodyText}>최근 2주 동안 마음 온도가 크게 떨어진 날은 없었어요.</Text>
            ) : (
                <>
                    <Text style={styles.bodyText}>
                        마음 온도가 크게 떨어진 날이 {drop_count}번 있었고, 그중 {recovered_count}번은 다시 올라왔어요.
                    </Text>
                    {avg_recovery_days !== null && (
                        <Text style={styles.subText}>회복까지 평균 {avg_recovery_days}일 걸렸어요.</Text>
                    )}
                    {events.map((event: any, index: number) => (
                        <View key={index} style={styles.listRow}>
                            <Text style={styles.listDate}>{formatDate(event.date)}</Text>
                            <View style={styles.listBody}>
                                <Text style={styles.bodyText}>
                                    {event.from}점 → {event.to}점 ({directionMark('down')} {event.drop}점)
                                </Text>
                                <Text style={styles.subText}>
                                    {event.recovered ? `${event.recovery_days}일 뒤 회복` : '아직 회복 전이에요'}
                                </Text>
                            </View>
                        </View>
                    ))}
                </>
            )}
            <Note text={`최근 2주 중 기록이 있는 ${days_analyzed}일을 봤어요.`} />
        </Card>
    );
};

const KeywordCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data || card.status !== 'ready') return <Card title="주요 상황과 감정" card={card} />;

    const { items, records } = card.data;

    return (
        <Card title="주요 상황과 감정" card={card}>
            {items.map((item: any, index: number) => (
                <View key={index} style={styles.keywordRow}>
                    <Text style={styles.keywordText}># {item.keyword}</Text>
                    <Text style={styles.keywordArrow}>→</Text>
                    <Text style={styles.bodyText}>
                        {item.emoji} {item.label}
                    </Text>
                    <Text style={styles.subText}>{item.count}회</Text>
                </View>
            ))}
            <Note text={`기록 ${records}개에서 함께 나타난 상황과 감정이에요.`} />
        </Card>
    );
};

const BaselineCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data || card.status !== 'ready') return <Card title="평소와 비교" card={card} />;

    const { comparisons, baseline_days } = card.data;

    return (
        <Card title="평소와 비교" card={card}>
            {comparisons.map((item: any) => (
                <View key={item.emotion} style={styles.keywordRow}>
                    <Text style={styles.bodyText}>
                        {item.emoji} {item.label}
                    </Text>
                    <Text style={[styles.trendDelta, { color: directionColor(item.direction, item.emotion === 'joy' || item.emotion === 'trust') }]}>
                        {directionMark(item.direction)} {item.delta}점
                    </Text>
                    <Text style={styles.subText}>평소 {item.baseline} · 이번 주 {item.week}</Text>
                </View>
            ))}
            <Note text={`이전 기록 ${baseline_days}개를 평소 기준으로 삼았어요.`} />
        </Card>
    );
};

/* --- Part 3. 행동과 다음 단계 --- */

const RoutineEffectCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data) return <Card title="루틴과 감정 변화" card={card} />;

    const { items, baseline_average, baseline_days, note } = card.data;

    return (
        <Card title="루틴과 감정 변화" card={card}>
            {items.map((item: any, index: number) => (
                <View key={index} style={styles.routineRow}>
                    <View style={styles.routineHead}>
                        <Text style={styles.routineName}>{item.routine}</Text>
                        <Text style={[styles.routineDelta, { color: directionColor(item.direction) }]}>
                            {directionMark(item.direction)} {item.delta}점
                        </Text>
                    </View>
                    <Text style={styles.subText}>
                        평균 {item.average}점 · 기록 {item.records}회
                        {!item.enough ? ' · 아직 기록이 적어요' : ''}
                    </Text>
                </View>
            ))}
            <Note text={`루틴이 없던 ${baseline_days}일 평균은 ${baseline_average}점이에요. ${note}`} />
        </Card>
    );
};

const NextRoutineCard = ({ card }: { card?: ReportCard }) => {
    if (!card?.data || card.status !== 'ready') return <Card title="다음 주 맞춤 루틴" card={card} />;

    const { reason, items } = card.data;

    return (
        <Card title="다음 주 맞춤 루틴" card={card}>
            <Text style={styles.bodyText}>{reason}</Text>
            {items.map((item: any, index: number) => (
                <View key={index} style={styles.routineSuggestion}>
                    <Text style={styles.routineSuggestionText}>{item.content}</Text>
                </View>
            ))}
        </Card>
    );
};

const SectionTitle = ({ text }: { text: string }) => <Text style={styles.sectionTitle}>{text}</Text>;

const ReportModal = ({ isVisible, data, onClose }: ReportModalProps) => {
    const cards = data?.cards;
    const consistency = data?.consistency;

    return (
        <Modal transparent={true} visible={isVisible} animationType="slide" onRequestClose={onClose}>
            <View style={styles.overlay}>
                <SafeAreaView style={styles.modalContent}>
                    <View style={styles.header}>
                        <Text style={styles.headerTitle}>주간 감성 리포트</Text>
                        <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                            <Text style={styles.closeBtnText}>✕</Text>
                        </TouchableOpacity>
                    </View>

                    {!cards || Object.keys(cards).length === 0 ? (
                        <View style={styles.emptyContainer}>
                            <Text style={styles.emptyText}>
                                {data?.message || '아직 보여드릴 기록이 없어요.\n일기를 쓰면 리포트를 만들어 드릴게요.'}
                            </Text>
                        </View>
                    ) : (
                        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
                            {consistency && (
                                <View style={styles.consistencyBadge}>
                                    <Text style={styles.consistencyText}>
                                        이번 주 {consistency.days_recorded}/{consistency.days_total}일 기록
                                    </Text>
                                </View>
                            )}

                            <SectionTitle text="현재 상태" />
                            <SummaryCard card={cards.summary} />
                            <SpectrumCard card={cards.spectrum} />
                            <TrendCard card={cards.trend} />
                            <SurveyCard card={cards.survey_trend} />

                            <SectionTitle text="상세 감정 분석" />
                            <BaselineCard card={cards.baseline} />
                            <CompositeCard card={cards.composite_days} />
                            <ResilienceCard card={cards.resilience} />
                            <KeywordCard card={cards.keywords} />

                            <SectionTitle text="행동과 다음 단계" />
                            <RoutineEffectCard card={cards.routine_effect} />
                            <NextRoutineCard card={cards.next_routines} />
                        </ScrollView>
                    )}
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
    headerTitle: { fontSize: 18, fontWeight: 'bold', color: '#333' },
    closeBtn: { position: 'absolute', right: 20, padding: 10 },
    closeBtnText: { fontSize: 20, color: '#888', fontWeight: 'bold' },
    scrollContent: { padding: 20, paddingBottom: 50 },

    consistencyBadge: {
        alignSelf: 'flex-start',
        backgroundColor: '#e4f1e9',
        paddingHorizontal: 14,
        paddingVertical: 7,
        borderRadius: 999,
        marginBottom: 18,
    },
    consistencyText: { color: '#2f6b4f', fontWeight: 'bold', fontSize: 13 },

    sectionTitle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#7b8781',
        marginBottom: 10,
        marginTop: 6,
        letterSpacing: 0.5,
    },

    card: {
        backgroundColor: '#ffffff',
        borderRadius: 24,
        padding: 22,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.05,
        shadowRadius: 12,
        elevation: 3,
    },
    cardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    cardTitle: { fontSize: 17, fontWeight: 'bold', color: '#2a3a21' },
    cardBody: { marginTop: 14 },
    cardNotice: { marginTop: 10, fontSize: 14, color: '#8a938d', lineHeight: 21 },
    statusBadge: { backgroundColor: '#f0f2f0', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999 },
    statusBadgeText: { fontSize: 12, color: '#7b8781', fontWeight: 'bold' },

    bodyText: { fontSize: 15, color: '#333', lineHeight: 22 },
    subText: { fontSize: 13, color: '#8a938d', marginTop: 2 },
    note: { fontSize: 12, color: '#9aa39d', marginTop: 12, lineHeight: 18 },

    summaryTop: { flexDirection: 'row', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
    levelPill: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999 },
    levelPillText: { fontWeight: 'bold', fontSize: 13 },
    summaryEmotion: { fontSize: 16, fontWeight: 'bold', color: '#333' },
    summaryRecords: { fontSize: 13, color: '#8a938d', marginLeft: 'auto' },
    summaryMessage: { fontSize: 15, color: '#333', lineHeight: 23, marginTop: 12 },
    evidenceToggle: { marginTop: 14 },
    evidenceToggleText: { fontSize: 14, color: '#2f6b4f', fontWeight: 'bold' },
    evidenceBox: { marginTop: 10, backgroundColor: '#f7f9f7', borderRadius: 14, padding: 14 },
    evidenceItem: { fontSize: 14, color: '#4a544d', lineHeight: 22 },

    chipRow: { flexDirection: 'row', gap: 10, flexWrap: 'wrap' },
    emotionChip: { backgroundColor: '#f2f5f3', borderRadius: 16, paddingHorizontal: 14, paddingVertical: 10, alignItems: 'center' },
    emotionChipTop: { backgroundColor: '#e4f1e9' },
    emotionChipEmoji: { fontSize: 24 },
    emotionChipLabel: { fontSize: 13, color: '#4a544d', marginTop: 4, fontWeight: 'bold' },
    emotionChipScore: { fontSize: 12, color: '#8a938d', marginTop: 2 },

    barList: { marginTop: 16, gap: 8 },
    barRow: { flexDirection: 'row', alignItems: 'center' },
    barLabel: { width: 42, fontSize: 13, color: '#4a544d' },
    barTrack: { flex: 1, height: 8, backgroundColor: '#eef1ef', borderRadius: 4, overflow: 'hidden' },
    barFill: { height: '100%', backgroundColor: '#7fb99a', borderRadius: 4 },
    barValue: { width: 34, textAlign: 'right', fontSize: 12, color: '#8a938d' },

    trendTop: { marginBottom: 6 },
    trendValue: { fontSize: 34, fontWeight: 'bold', color: '#2a3a21' },
    trendDelta: { fontSize: 14, fontWeight: 'bold', marginTop: 4 },
    trendDeltaMuted: { fontSize: 14, color: '#8a938d', marginTop: 4 },

    compareRow: { flexDirection: 'row', gap: 12 },
    compareBox: { flex: 1, backgroundColor: '#f7f9f7', borderRadius: 16, padding: 14, alignItems: 'center' },
    compareCaption: { fontSize: 12, color: '#8a938d' },
    compareValue: { fontSize: 24, fontWeight: 'bold', color: '#2a3a21', marginTop: 6 },

    listRow: { flexDirection: 'row', gap: 12, marginTop: 12 },
    listDate: { width: 48, fontSize: 13, color: '#8a938d', paddingTop: 2 },
    listBody: { flex: 1 },

    keywordRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 10, flexWrap: 'wrap' },
    keywordText: { fontSize: 15, color: '#00796b', fontWeight: 'bold' },
    keywordArrow: { fontSize: 14, color: '#9aa39d' },

    routineRow: { marginTop: 12 },
    routineHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    routineName: { fontSize: 15, fontWeight: 'bold', color: '#333' },
    routineDelta: { fontSize: 14, fontWeight: 'bold' },

    routineSuggestion: { backgroundColor: '#f7f9f7', borderRadius: 14, padding: 14, marginTop: 10 },
    routineSuggestionText: { fontSize: 15, color: '#333', lineHeight: 22 },

    emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 30 },
    emptyText: { fontSize: 15, color: '#888', textAlign: 'center', lineHeight: 24 },
});

export default ReportModal;
