import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: (isOpen: boolean) => void;
}

export default function Header({ sidebarOpen, setSidebarOpen }: HeaderProps) {
  const [timeRange, setTimeRange] = useState<string>("24h");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const { toast } = useToast();
  
  const handleRefresh = () => {
    toast({
      title: "Refreshing Data",
      description: "Fetching latest server metrics...",
      duration: 2000,
    });
    
    // Invalidate queries to refetch data
    // queryClient.invalidateQueries({ queryKey: ['/api/servers'] });
    // queryClient.invalidateQueries({ queryKey: ['/api/metrics'] });
  };

  return (
    <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-20">
      <div className="flex justify-between items-center px-4 py-3">
        {/* Mobile Menu Button */}
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)} 
          className="md:hidden text-slate-500 hover:text-slate-700"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
          </svg>
        </button>
        
        {/* Search */}
        <div className="relative flex-1 mx-4 max-w-lg hidden sm:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
          <input 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            type="search" 
            className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-md text-sm placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Search servers, metrics, or users..."
          />
        </div>
        
        {/* Actions */}
        <div className="flex items-center space-x-4">
          {/* Time Range Selector */}
          <div className="relative hidden sm:block">
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="appearance-none bg-slate-50 border border-slate-200 text-slate-700 py-1 px-3 pr-8 rounded text-sm leading-tight focus:outline-none focus:bg-white focus:border-primary-500"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-600">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </div>
          </div>
          
          {/* Refresh Button */}
          <button 
            onClick={handleRefresh}
            className="p-1 rounded-full text-slate-500 hover:text-primary-500 hover:bg-slate-100" 
            title="Refresh Data"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
          </button>
          
          {/* Notifications */}
          <button 
            className="p-1 rounded-full text-slate-500 hover:text-primary-500 hover:bg-slate-100 relative" 
            title="Notifications"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
            </svg>
            <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-error"></span>
          </button>
          
          {/* User Menu */}
          <div className="relative">
            <button className="flex items-center focus:outline-none">
              <div className="h-8 w-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center overflow-hidden">
                <span className="font-medium">A</span>
              </div>
              <span className="hidden md:block ml-2 text-sm font-medium">Admin</span>
              <svg className="hidden md:block ml-1 h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
