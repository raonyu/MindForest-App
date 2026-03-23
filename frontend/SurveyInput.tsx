import React from 'react';
import { View , Text, TouchableOpacity, StyleSheet} from 'react-native';
import { COLORS } from './assets/Maincolors';

const SurveyInput = ({title, options, onSelect}: {title: string, options: string[], onSelect: (val: string) => void}) =>{
    return(
        <View style={styles.surveyContainer}>
            <View style={styles.bottomTitleContainer}>
                <Text style={styles.bottomBarText}>{title}</Text>
            </View>
            <View style={styles.itemsContainer}>
                {options.map((option, index) => (
                    <TouchableOpacity key={index} onPress={() => onSelect(option)}
                        style={styles.optionItems}>
                        <Text style = {styles.itemText}>{option}</Text>
                    </TouchableOpacity>
                ))}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    surveyContainer: {
        backgroundColor: COLORS.bar,
        borderRadius: 8,
    },

    bottomTitleContainer: {
        backgroundColor: '#00000030',
        height: 50,
        marginVertical: 16,
        borderRadius: 25,
        justifyContent: 'center',
        paddingLeft: 20
    },
    bottomBarText: {
        color: 'white',
        fontSize: 20,
        fontWeight: 'bold'
    },
    itemsContainer:{
        backgroundColor: '#00000030',
        height: 256,
        borderRadius: 16,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
    },
    optionItems: {
        flex: 1,
    },
    itemText:{
        color: 'white',
        fontSize: 24,
        fontWeight: 300
    }
});

export default SurveyInput;