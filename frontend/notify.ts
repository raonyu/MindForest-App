import { Alert, Platform, type AlertButton } from 'react-native';

/** React Native Web does not implement Alert.alert's button callbacks. */
export function notify(title: string, message?: string, buttons?: AlertButton[]) {
  if (Platform.OS !== 'web') {
    Alert.alert(title, message, buttons);
    return;
  }
  const browser = globalThis as unknown as {
    alert(message: string): void;
    confirm(message: string): boolean;
  };
  const text = [title, message].filter(Boolean).join('\n\n');
  const cancel = buttons?.find(button => button.style === 'cancel');
  const action = buttons?.find(button => button.style !== 'cancel');
  if (cancel) {
    if (browser.confirm(text)) action?.onPress?.();
    else cancel.onPress?.();
  } else {
    browser.alert(text);
    action?.onPress?.();
  }
}
