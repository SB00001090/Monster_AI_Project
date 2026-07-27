/**
 * Capacitor — Monster AI 公測訪客版
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * appId / applicationId：com.monster_ai_hk.monsterai
 * appName：Monster AI 公測
 */
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.monster_ai_hk.monsterai',
  appName: 'Monster AI 公測',
  // Vite 輸出目錄（見 vite.config.ts build.outDir）
  webDir: 'dist/public',
  server: {
    androidScheme: 'https',
    iosScheme: 'https',
    // 開發時可改為本機：
    // url: 'http://10.0.2.2:5173',
    // cleartext: true,
  },
  plugins: {
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_icon_config_sample',
      iconColor: '#00E5FF',
      sound: 'beep.wav',
    },
    SplashScreen: {
      launchShowDuration: 2500,
      launchAutoHide: true,
      backgroundColor: '#0B0F1A',
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },
    Preferences: {},
  },
  ios: {
    contentInset: 'automatic',
    backgroundColor: '#0B0F1A',
  },
  android: {
    backgroundColor: '#0B0F1A',
    allowMixedContent: true,
    captureInput: true,
    // 公測可開 WebView 除錯；release 建置腳本會覆寫為 false
    webContentsDebuggingEnabled: true,
    buildOptions: {
      keystorePath: undefined,
      keystorePassword: undefined,
      keystoreAlias: undefined,
      keystoreAliasPassword: undefined,
      releaseType: 'APK',
    },
  },
};

export default config;
