import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, Button,Text, StyleSheet } from 'react-native';

const ChatInput = ({onSend}: {onSend: (text: string) => void}) =>{
	const [localText, setLocalText] = useState('');
	const handleSend = () => {
		onSend(localText);
		setLocalText('');
	};
	return(
		<View>
			<TextInput
			value={localText}
			onChangeText={setLocalText}
			placeholder="채팅메세지"
			/>
			<TouchableOpacity onPress={handleSend}>
				<Text>전송</Text>
			</TouchableOpacity>
		</View>
	);
};
export default ChatInput;