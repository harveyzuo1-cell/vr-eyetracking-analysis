import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// 应用全局状态管理
const useAppStore = create(
  devtools(
    (set, get) => ({
      // 应用状态
      currentView: 'visualization',
      currentLanguage: 'zh',
      sidebarExpanded: false,
      
      // 数据状态
      allData: {},
      currentGroup: 'all',
      currentQuestion: 'all',
      currentVisualization: null,
      groupsData: null,
      
      // 加载状态
      isLoading: false,
      error: null,
      
      // Actions
      setCurrentView: (view) => set({ currentView: view }),
      
      setCurrentLanguage: (language) => set({ currentLanguage: language }),
      
      setSidebarExpanded: (expanded) => set({ sidebarExpanded: expanded }),
      
      toggleSidebar: () => set((state) => ({ 
        sidebarExpanded: !state.sidebarExpanded 
      })),
      
      setCurrentGroup: (group) => set({ currentGroup: group }),
      
      setCurrentQuestion: (question) => set({ currentQuestion: question }),
      
      setCurrentVisualization: (visualization) => set({ 
        currentVisualization: visualization 
      }),
      
      setAllData: (data) => set({ allData: data }),
      
      updateGroupData: (groupType, data) => set((state) => ({
        allData: {
          ...state.allData,
          [groupType]: data
        }
      })),
      
      setGroupsData: (data) => set({ groupsData: data }),
      
      setLoading: (loading) => set({ isLoading: loading }),
      
      setError: (error) => set({ error }),
      
      clearError: () => set({ error: null }),
      
      // 重置所有状态
      resetState: () => set({
        allData: {},
        currentGroup: 'all',
        currentQuestion: 'all',
        currentVisualization: null,
        groupsData: null,
        isLoading: false,
        error: null,
      }),
      
      // 获取过滤后的数据
      getFilteredData: () => {
        const state = get();
        let filteredData = [];
        
        if (state.currentGroup === 'all') {
          Object.values(state.allData).forEach(groupData => {
            filteredData = filteredData.concat(groupData);
          });
        } else {
          filteredData = state.allData[state.currentGroup] || [];
        }
        
        if (state.currentQuestion !== 'all') {
          filteredData = filteredData.filter(
            item => item.question_num == state.currentQuestion
          );
        }
        
        return filteredData;
      },
      
      // 获取组统计信息
      getGroupStats: () => {
        const state = get();
        if (!state.groupsData) return null;
        
        return {
          control: state.groupsData.control?.data_count || 0,
          mci: state.groupsData.mci?.data_count || 0,
          ad: state.groupsData.ad?.data_count || 0,
          total: (state.groupsData.control?.data_count || 0) + 
                 (state.groupsData.mci?.data_count || 0) + 
                 (state.groupsData.ad?.data_count || 0)
        };
      }
    }),
    {
      name: 'vr-eyetracking-store',
    }
  )
);

export default useAppStore;