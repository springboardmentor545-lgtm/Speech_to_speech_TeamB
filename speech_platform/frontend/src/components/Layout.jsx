import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Mic, Settings, BarChart3, Globe } from 'lucide-react';

const Layout = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/milestone1', label: 'Milestone 1', icon: Mic },
    { path: '/milestone2', label: 'Milestone 2', icon: Settings },
    { path: '/milestone3', label: 'Milestone 3', icon: BarChart3 },
    { path: '/milestone4', label: 'Milestone 4', icon: Globe },
  ];

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800/80 backdrop-blur-lg border-r border-gray-700 flex flex-col">
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <div className="bg-gradient-to-r from-primary-500 to-primary-700 p-2 rounded-lg">
              <Mic size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Speech Platform</h1>
              <p className="text-sm text-gray-400">Real-Time Translation</p>
            </div>
          </div>
        </div>
        
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (location.pathname === '/' && item.path === '/milestone1');
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                      isActive
                        ? 'bg-primary-600 shadow-primary-500/30 text-white shadow-lg'
                        : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                    }`}
                  >
                    <Icon size={20} />
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        
        <div className="p-4 border-t border-gray-700 text-center">
          <p className="text-xs text-gray-500">AI-Powered Translation v1.0</p>
        </div>
      </div>
      
      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
