import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// 语言包
import zhCN from './locales/zh-CN.json';
import zhTW from './locales/zh-TW.json';
import enUS from './locales/en-US.json';

const resources = {
  'zh-CN': {
    translation: zhCN
  },
  'zh-TW': {
    translation: zhTW
  },
  'en-US': {
    translation: enUS
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('language') || 'zh-CN', // 默认语言
    fallbackLng: 'en-US',
    
    interpolation: {
      escapeValue: false, // React已经防止XSS
    },
    
    debug: process.env.NODE_ENV === 'development',
  });

export default i18n;
