import React, { createContext, useState, useContext } from 'react';
//컨텍스트 객체 생성
const BottomBarContext = createContext({
	//하단바 내용물 생성(초기값 null)
	BottomBar: null as React.ReactNode,
	//하단바 바꾸는 함수 설정
	setBottomBarContent: (content: React.ReactNode) => {},
});

export const BottomBarProvider = ({children}: {children: React.ReactNode}) => {
	const [bottomBarContext, setBottomBarContext] = useState<React.ReactNode>(null);
	return(
		<BottomBarContext.Provider
		value={{BottomBar: bottomBarContext, setBottomBarContent: setBottomBarContext}}>
			{children}
		</BottomBarContext.Provider>	
	);
};
export const useBottomBar = () => useContext(BottomBarContext);