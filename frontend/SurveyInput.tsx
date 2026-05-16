import React from 'react';
import { View , Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';

const SurveyInput = ({title, options, onSelect}: {title: string, options: string[], onSelect: (val: string) => void}) =>{
    return(
        <View style={styles.surveyContainer}>
            <View style={styles.titleContainer}>
                <Text style={styles.titleText}>{title}</Text>
            </View>
            <ScrollView style={styles.itemsContainer} contentContainerStyle={styles.itemsContent}>
                {options.map((option, index) => (
                    <TouchableOpacity 
                        key={index} 
                        onPress={() => onSelect(option)}
                        style={styles.optionButton}
                        activeOpacity={0.7}
                    >
                        <Text style={styles.itemText}>{option}</Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    surveyContainer: {
        backgroundColor: '#ffffff',
        borderTopLeftRadius: 24,
        borderTopRightRadius: 24,
        paddingHorizontal: 20,
        paddingTop: 24,
        paddingBottom: 40,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.05,
        shadowRadius: 10,
        elevation: 10,
        maxHeight: 400,
    },
    titleContainer: {
        marginBottom: 16,
        paddingHorizontal: 8,
    },
    titleText: {
        color: '#2a3a21',
        fontSize: 18,
        fontFamily: 'NanumSquareRoundB',
        lineHeight: 26,
    },
    itemsContainer: {
        maxHeight: 280,
    },
    itemsContent: {
        gap: 12,
        paddingBottom: 20,
        paddingHorizontal: 4,
    },
    optionButton: {
        backgroundColor: '#f9fbf7',
        borderWidth: 1,
        borderColor: '#e2ebd9',
        borderRadius: 16,
        paddingVertical: 16,
        paddingHorizontal: 20,
        justifyContent: 'center',
        shadowColor: '#9ee779',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 2,
    },
    itemText: {
        color: '#597d48',
        fontSize: 16,
        fontFamily: 'NanumSquareRoundR',
        lineHeight: 22,
    }
});

export default SurveyInput;