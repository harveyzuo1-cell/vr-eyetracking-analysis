import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 导入翻译文件
import zhCN_common from '../locales/zh-CN/common.json';
import zhCN_module00 from '../locales/zh-CN/module00.json';
import zhCN_module02 from '../locales/zh-CN/module02.json';

import enUS_common from '../locales/en-US/common.json';
import enUS_module00 from '../locales/en-US/module00.json';
import enUS_module02 from '../locales/en-US/module02.json';

import msMY_common from '../locales/ms-MY/common.json';
import msMY_module00 from '../locales/ms-MY/module00.json';
import msMY_module02 from '../locales/ms-MY/module02.json';

const resources = {
  'zh-CN': {
    common: zhCN_common,
    module00: zhCN_module00,
    module02: zhCN_module02,
  },
  'en-US': {
    common: enUS_common,
    module00: enUS_module00,
    module02: enUS_module02,
  },
  'ms-MY': {
    common: msMY_common,
    module00: msMY_module00,
    module02: msMY_module02,
  },
};

i18n
  .use(LanguageDetector) // 自动检测用户语言
  .use(initReactI18next) // 集成React
  .init({
    resources,
    fallbackLng: 'zh-CN', // 默认语言
    defaultNS: 'common', // 默认命名空间
    interpolation: {
      escapeValue: false, // React已经进行了转义
    },
    detection: {
      // 语言检测顺序
      order: ['localStorage', 'navigator'],
      // 缓存语言选择
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
  });

export default i18n;
