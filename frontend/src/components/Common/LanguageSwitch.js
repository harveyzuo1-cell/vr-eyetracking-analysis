import React from 'react';
import useAppStore from '../../store/useAppStore';
import { languageTexts } from '../../utils/languages';
import './LanguageSwitch.css';

const LanguageSwitch = () => {
  const { currentLanguage, setCurrentLanguage } = useAppStore();
  
  const handleLanguageChange = (e) => {
    const newLanguage = e.target.checked ? 'en' : 'zh';
    setCurrentLanguage(newLanguage);
  };

  return (
    <div className="lang-switch">
      <div className="lang-labels">
        <span className={currentLanguage === 'zh' ? 'active' : ''}>中</span>
        <label className="switch">
          <input 
            type="checkbox" 
            checked={currentLanguage === 'en'}
            onChange={handleLanguageChange}
          />
          <span className="slider"></span>
        </label>
        <span className={currentLanguage === 'en' ? 'active' : ''}>EN</span>
      </div>
    </div>
  );
};

export default LanguageSwitch;