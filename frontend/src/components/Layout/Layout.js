import React, { useEffect } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import useAppStore from '../../store/useAppStore';
import { apiService } from '../../services/api';
import toast from 'react-hot-toast';
import './Layout.css';

const Layout = ({ children }) => {
  const { 
    sidebarExpanded, 
    setGroupsData, 
    setAllData, 
    setLoading, 
    setError 
  } = useAppStore();

  // 初始化应用数据
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行加载组数据和各组详细数据
      const [groupsResponse, controlData, mciData, adData] = await Promise.all([
        apiService.getGroups(),
        apiService.getGroupData('control').catch(() => ({ data: [] })),
        apiService.getGroupData('mci').catch(() => ({ data: [] })),
        apiService.getGroupData('ad').catch(() => ({ data: [] }))
      ]);

      // 设置组统计数据
      setGroupsData(groupsResponse);

      // 设置详细数据
      setAllData({
        control: controlData.data || [],
        mci: mciData.data || [],
        ad: adData.data || []
      });

      console.log('✅ 初始数据加载完成');
    } catch (error) {
      console.error('❌ 初始数据加载失败:', error);
      setError(error.message);
      toast.error('数据加载失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`app-layout ${sidebarExpanded ? 'sidebar-expanded' : ''}`}>
      <Header />
      <div className="layout-body">
        <Sidebar />
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;