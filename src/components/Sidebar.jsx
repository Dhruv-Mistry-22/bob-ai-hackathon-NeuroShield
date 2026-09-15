import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BarChart2, 
  Users, 
  Settings, 
  ShieldAlert,
  Activity,
  LogOut,
  Bell
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Analytics', path: '/analytics', icon: BarChart2 },
  { name: 'Users', path: '/users', icon: Users },
  { name: 'Events', path: '/events', icon: Activity },
];

const Sidebar = ({ isOpen }) => {
  return (
    <aside 
      className={cn(
        "flex flex-col h-full bg-white border-r border-slate-200 transition-all duration-300 ease-in-out",
        isOpen ? "w-64" : "w-20"
      )}
    >
      <div className="flex items-center h-16 px-6 border-b border-slate-200">
        <ShieldAlert className="w-8 h-8 text-blue-600 flex-shrink-0" />
        <span 
          className={cn(
            "ml-3 font-bold text-lg text-slate-800 whitespace-nowrap overflow-hidden transition-all duration-300",
            isOpen ? "opacity-100 w-auto" : "opacity-0 w-0"
          )}
        >
          NeuroShield
        </span>
      </div>

      <div className="flex-1 overflow-y-auto py-4 px-3">
        <div className="space-y-1 mb-8">
          <p className={cn(
            "px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2",
            !isOpen && "text-center text-[10px]"
          )}>
            {isOpen ? 'Main Menu' : 'Main'}
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => cn(
                  "flex items-center px-3 py-2.5 rounded-lg transition-colors group relative",
                  isActive 
                    ? "bg-blue-50 text-blue-600" 
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )}
                title={!isOpen ? item.name : undefined}
              >
                <Icon className={cn(
                  "flex-shrink-0 w-5 h-5",
                  !isOpen && "mx-auto"
                )} />
                <span className={cn(
                  "ml-3 font-medium whitespace-nowrap transition-all duration-300",
                  isOpen ? "opacity-100 block" : "opacity-0 hidden"
                )}>
                  {item.name}
                </span>
                
                {/* Tooltip for collapsed state */}
                {!isOpen && (
                  <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible whitespace-nowrap z-50 transition-all">
                    {item.name}
                  </div>
                )}
              </NavLink>
            );
          })}
        </div>

        <div className="space-y-1">
          <p className={cn(
            "px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2",
            !isOpen && "text-center text-[10px]"
          )}>
            {isOpen ? 'Preferences' : 'Pref'}
          </p>
          <NavLink
            to="/settings"
            className={({ isActive }) => cn(
              "flex items-center px-3 py-2.5 rounded-lg transition-colors group relative",
              isActive 
                ? "bg-blue-50 text-blue-600" 
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
            )}
          >
            <Settings className={cn(
              "flex-shrink-0 w-5 h-5",
              !isOpen && "mx-auto"
            )} />
            <span className={cn(
              "ml-3 font-medium whitespace-nowrap transition-all duration-300",
              isOpen ? "opacity-100 block" : "opacity-0 hidden"
            )}>
              Settings
            </span>
          </NavLink>
        </div>
      </div>

      <div className="p-4 border-t border-slate-200">
        <button className={cn(
          "flex items-center w-full px-3 py-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors group relative",
          !isOpen && "justify-center"
        )}>
          <LogOut className="flex-shrink-0 w-5 h-5" />
          <span className={cn(
            "ml-3 font-medium whitespace-nowrap transition-all duration-300",
            isOpen ? "opacity-100 block" : "opacity-0 hidden"
          )}>
            Log out
          </span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
