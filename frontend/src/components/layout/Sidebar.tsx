import React from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, UploadCloud, Hexagon } from 'lucide-react';
import { clsx } from 'clsx';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', icon: MessageSquare, label: 'Chat' },
    { to: '/upload', icon: UploadCloud, label: 'Upload' },
  ];

  return (
    <aside className="w-64 bg-surface border-r border-border h-full flex flex-col fixed left-0 top-0 hidden lg:flex">
      <div className="h-16 flex items-center px-6 border-b border-border">
        <Hexagon className="text-primary mr-3" size={24} />
        <h1 className="font-bold text-lg tracking-wide text-text">SupportMind</h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted hover:bg-surface hover:text-text'
              )
            }
          >
            <item.icon size={20} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted/50 text-center">
          SupportMind AI &copy; 2026
        </div>
      </div>
    </aside>
  );
};
