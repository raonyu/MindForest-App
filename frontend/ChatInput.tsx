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
			<TextInput
			style = {styles.textInput}
			value={localText}
			onChangeText={setLocalText}
			placeholder="채팅메세지"
			/>
			<TouchableOpacity onPress={handleSend} style={styles.sendButton}>
				<Text style={styles.sendButtonText}>전송</Text>
			</TouchableOpacity>
		</View>
	);


};
const styles = StyleSheet.create({
	textInput: {
		color: 'white',
		fontSize: 16
	},
	sendButton: {
		backgroundColor: 'white',

	},
	sendButtonText: {
		color: 'black',
		fontSize: 16,
		padding: 10

	}
})


export default ChatInput;