import { AppRegistry } from 'react-native';
import App from './App';
import { name as appName } from './app.json';

// App 컴포넌트를 웹의 'root' div에 연결합니다.
AppRegistry.registerComponent(appName, () => App);
AppRegistry.runApplication(appName, {
  initialProps: {},
  rootTag: document.getElementById('root'),
});