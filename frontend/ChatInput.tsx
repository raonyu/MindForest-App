import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, Button,Text, StyleSheet } from 'react-native';

const ChatInput = ({onSend}: {onSend: (text: string) => void}) =>{
	const [localText, setLocalText] = useState('');
	const handleSend = () => {
		onSend(localText);
		setLocalText('');
	};
	return(
		<View style={{ flexDirection: 'row' }}>
			<View style={styles.bottomTitleContainer}>
				<TextInput
					style = {styles.textInput}
					value={localText}
					onChangeText={setLocalText}
					placeholder="채팅메세지"
				/>
			</View>
			<TouchableOpacity onPress={handleSend} style={styles.sendButton}>
				<Text style={styles.sendButtonText}>전송</Text>
			</TouchableOpacity>
		</View>
	);


};
const styles = StyleSheet.create({
    bottomTitleContainer: {
        backgroundColor: '#00000030',
        height: 50,
        marginVertical: 16,
        borderRadius: 25,
        justifyContent: 'center',
        paddingLeft: 20
    },
	textInput: {
        color: 'white',
        fontSize: 20,
        fontWeight: 'bold'
	},
	sendButton: {
		height: 50,
		marginVertical: 16,
		marginLeft: 8,
		paddingHorizontal: 20,
		backgroundColor: '#FFFFFF20',
		borderRadius: 25,
	},
	sendButtonText: {
		color: 'white',
		fontSize: 20,
		padding: 10

	}
})


export default ChatInput;