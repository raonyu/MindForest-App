import React, { createContext, useContext } from 'react';

// 보관함의 설계도
const MainContext = createContext<any>(null);

// 다른 파일에서 편하게 꺼내 쓰기 위한 도구
export const useMainContext = () => useContext(MainContext);

export default MainContext;