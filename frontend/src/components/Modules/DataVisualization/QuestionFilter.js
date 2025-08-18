import React from 'react';
import useAppStore from '../../../store/useAppStore';
import { languageTexts } from '../../../utils/languages';
import './QuestionFilter.css';

const QuestionFilter = () => {
  const { 
    currentQuestion, 
    setCurrentQuestion, 
    currentLanguage 
  } = useAppStore();
  
  const texts = languageTexts[currentLanguage];

  const questionOptions = [
    {
      value: 'all',
      label: texts.all,
      icon: 'fas fa-th'
    },
    {
      value: '1',
      label: texts.task1,
      icon: 'fas fa-1',
      color: '#ef4444'
    },
    {
      value: '2',
      label: texts.task2,
      icon: 'fas fa-2',
      color: '#f97316'
    },
    {
      value: '3',
      label: texts.task3,
      icon: 'fas fa-3',
      color: '#eab308'
    },
    {
      value: '4',
      label: texts.task4,
      icon: 'fas fa-4',
      color: '#22c55e'
    },
    {
      value: '5',
      label: texts.task5,
      icon: 'fas fa-5',
      color: '#3b82f6'
    }
  ];

  return (
    <div className="question-filter">
      <div className="filter-title">
        <i className="fas fa-tasks"></i>
        {texts.taskFilter}
      </div>
      
      <div className="question-options">
        {questionOptions.map((option) => (
          <button
            key={option.value}
            className={`question-option ${currentQuestion === option.value ? 'active' : ''}`}
            onClick={() => setCurrentQuestion(option.value)}
            style={{ '--question-color': option.color || '#6b7280' }}
            title={option.label}
          >
            <i className={option.icon}></i>
            <span className="question-label">{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuestionFilter;