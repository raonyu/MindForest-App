/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */
import React from 'react';
import { StatusBar, StyleSheet, useColorScheme, View,Text, Pressable, TouchableOpacity } from 'react-native';

//버튼 선언
const CustomButton = () =>(
  <TouchableOpacity style = {styles.baseButton}><Text>버튼임</Text></TouchableOpacity>


);

function App(){
  const isDarkMode = useColorScheme() === 'dark';

  return (
    <View>
      <Text style={styles.bigfont}>마음의 숲 프로젝트</Text>
      <CustomButton></CustomButton>
      <CustomButton></CustomButton>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  bigfont: {
    fontSize: 32,
    fontWeight: 'bold'
  },
  baseButton: {
    backgroundColor: "gray",
  }
});




export default App;
