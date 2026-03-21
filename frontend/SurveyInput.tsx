import React from 'react';
import { View , Text, TouchableOpacity} from 'react-native';

const SurveyInput = ({title, options, onSelect}: {title: string, options: string[], onSelect: (val: string) => void}) =>{
    return(
        <View>
            <Text>{title}</Text>
            {options.map((option, index) => (
                <TouchableOpacity key={index} onPress={() => onSelect(option)}>
                    <Text>{option}</Text>
                </TouchableOpacity>
            ))}
        </View>
    );
}
export default SurveyInput;