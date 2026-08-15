import React, { useState, useEffect } from 'react';
import { Search, Command, ArrowRight, User, Settings, Database, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const mockActions = [
  { id: 1, title: 'Go to Dashboard', route: '/', icon: <Activity size={16}/>, category: 'Navigation' },
  { id: 2, title: 'Manage Users', route: '/dashboard/admin', icon: <User size={16}/>, category: 'Admin' },
  { id: 3, title: 'AI Operations Center', route: '/dashboard/ai-ops', icon: <Database size={16}/>, category: 'Admin' },
  { id: 4, title: 'Enterprise Settings', route: '/dashboard/settings', icon: <Settings size={16}/>, category: 'Admin' },
];

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const navigate = useNavigate();

  // Handle Ctrl+K shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const filteredActions = mockActions.filter(action => 
    action.title.toLowerCase().includes(query.toLowerCase()) || 
    action.category.toLowerCase().includes(query.toLowerCase())
  );

  // Keyboard navigation within the palette
  useEffect(() => {
    const handleNavigation = (e) => {
      if (!isOpen) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex(prev => (prev + 1) % filteredActions.length);
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex(prev => (prev - 1 + filteredActions.length) % filteredActions.length);
      }
      if (e.key === 'Enter' && filteredActions[activeIndex]) {
        e.preventDefault();
        navigate(filteredActions[activeIndex].route);
        setIsOpen(false);
        setQuery('');
      }
    };
    window.addEventListener('keydown', handleNavigation);
    return () => window.removeEventListener('keydown', handleNavigation);
  }, [isOpen, activeIndex, filteredActions, navigate]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-slate-200" onClick={(e) => e.stopPropagation()}>
        
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-slate-100">
          <Search className="text-slate-400" size={20} />
          <input 
            autoFocus
            type="text"
            className="flex-1 bg-transparent border-none outline-none text-slate-800 text-lg placeholder-slate-400"
            placeholder="Type a command or search... (Esc to close)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIndex(0); // Reset index on new search
            }}
          />
          <div className="flex items-center gap-1 bg-slate-100 px-2 py-1 rounded text-xs font-bold text-slate-500 border border-slate-200">
             <Command size={12}/> <span>K</span>
          </div>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2">
          {filteredActions.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              No results found for "{query}".
            </div>
          ) : (
            filteredActions.map((action, index) => (
              <div 
                key={action.id}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => {
                  navigate(action.route);
                  setIsOpen(false);
                  setQuery('');
                }}
                className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition ${
                  index === activeIndex ? 'bg-blue-600 text-white shadow-md' : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${index === activeIndex ? 'bg-blue-500' : 'bg-slate-100 text-slate-500'}`}>
                    {action.icon}
                  </div>
                  <div>
                    <h4 className="font-bold">{action.title}</h4>
                    <p className={`text-xs ${index === activeIndex ? 'text-blue-200' : 'text-slate-400'}`}>{action.category}</p>
                  </div>
                </div>
                {index === activeIndex && <ArrowRight size={18} className="text-blue-200 animate-in slide-in-from-left-2" />}
              </div>
            ))
          )}
        </div>
        
      </div>
      
      {/* Click outside overlay to close */}
      <div className="absolute inset-0 z-[-1]" onClick={() => setIsOpen(false)}></div>
    </div>
  );
}
