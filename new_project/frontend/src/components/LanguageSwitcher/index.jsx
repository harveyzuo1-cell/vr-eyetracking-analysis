import React from 'react';
import { Select } from 'antd';
import { useTranslation } from 'react-i18next';
import { GlobalOutlined } from '@ant-design/icons';

const { Option } = Select;

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();

  const languages = [
    { code: 'zh-CN', label: '中文', flag: '🇨🇳' },
    { code: 'en-US', label: 'English', flag: '🇺🇸' },
    { code: 'ms-MY', label: 'Bahasa Melayu', flag: '🇲🇾' },
  ];

  const handleLanguageChange = (languageCode) => {
    i18n.changeLanguage(languageCode);
  };

  return (
    <Select
      value={i18n.language}
      onChange={handleLanguageChange}
      style={{ width: 180 }}
      suffixIcon={<GlobalOutlined />}
    >
      {languages.map((lang) => (
        <Option key={lang.code} value={lang.code}>
          <span style={{ marginRight: 8 }}>{lang.flag}</span>
          {lang.label}
        </Option>
      ))}
    </Select>
  );
};

export default LanguageSwitcher;
