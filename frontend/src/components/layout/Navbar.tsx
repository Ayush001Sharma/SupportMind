import React from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, UploadCloud, Hexagon } from 'lucide-react';
import { clsx } from 'clsx';

export const Navbar: React.FC = () => {
  return (
    <header className="lg:hidden bg-surface border-b border-border h-16 flex items-center justify-between px-4 sticky top-0 z-50">
      <div className="flex items-center">
        <Hexagon className="text-primary mr-2" size={20} />
        <h1 className="font-bold text-base text-text">SupportMind</h1>
      </div>
      <nav className="flex items-center space-x-2">
        <NavLink
          to="/"
          className={({ isActive }) =>
            clsx(
              'p-2 rounded-lg transition-colors',
              isActive ? 'bg-primary/10 text-primary' : 'text-muted'
            )
          }
        >
          <MessageSquare size={20} />
        </NavLink>
        <NavLink
          to="/upload"
          className={({ isActive }) =>
            clsx(
              'p-2 rounded-lg transition-colors',
              isActive ? 'bg-primary/10 text-primary' : 'text-muted'
            )
          }
        >
          <UploadCloud size={20} />
        </NavLink>
      </nav>
    </header>
  );
};
