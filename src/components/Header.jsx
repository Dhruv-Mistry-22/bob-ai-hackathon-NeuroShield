import React from 'react';
import { Menu, Search, Bell, ChevronDown } from 'lucide-react';

const Header = ({ toggleSidebar, user }) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sm:px-6 z-10">
      <div className="flex items-center flex-1 gap-4">
        <button 
          onClick={toggleSidebar}
          className="p-2 -ml-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Toggle Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
        
        <div className="max-w-md w-full hidden sm:block relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg leading-5 bg-slate-50 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm transition-colors"
            placeholder="Search across your dashboard..."
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 block h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white"></span>
        </button>

        <div className="h-8 w-px bg-slate-200 hidden sm:block"></div>

        <div className="flex items-center gap-3 cursor-pointer p-1 pr-2 rounded-full hover:bg-slate-50 transition-colors">
          <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold overflow-hidden">
            {user ? (
              <img 
                src={`https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=eff6ff&color=1d4ed8`} 
                alt="User avatar" 
                className="h-full w-full object-cover"
              />
            ) : (
              <span>?</span>
            )}
          </div>
          <div className="hidden md:flex flex-col">
            <span className="text-sm font-semibold text-slate-700 leading-tight">
              {user ? user.name : 'Loading...'}
            </span>
            <span className="text-xs text-slate-500">
              {user ? user.role : ''}
            </span>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400 hidden md:block" />
        </div>
      </div>
    </header>
  );
};

export default Header;
