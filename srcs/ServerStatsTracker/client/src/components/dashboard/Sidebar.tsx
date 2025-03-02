import { Link, useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { ServerSummary } from "@/types/server";
import { cn } from "@/lib/utils";

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export default function Sidebar({ isOpen, setIsOpen }: SidebarProps) {
  const [location] = useLocation();
  
  const { data: servers = [] } = useQuery<ServerSummary[]>({
    queryKey: ['/api/servers'],
  });

  return (
    <div 
      className={cn(
        "fixed md:relative z-30 bg-white shadow-lg md:shadow-md w-64 transition-transform duration-300 ease-in-out h-screen overflow-y-auto",
        isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}
    >
      {/* Logo & Title */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <svg className="w-8 h-8 text-primary" fill="currentColor" viewBox="0 0 24 24">
            <path d="M4 5v14h16V5H4zm14 12H6V7h12v10zm-7-7h4v2h-4v-2zm0 3h4v2h-4v-2zm-5-3h3v5H6v-5z"></path>
          </svg>
          <h1 className="text-lg font-semibold">Server Monitor</h1>
        </div>
        <button onClick={() => setIsOpen(false)} className="md:hidden text-slate-500 hover:text-slate-700">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      {/* Navigation */}
      <nav className="p-4">
        <div className="mb-4">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Overview</h2>
          <Link href="/" 
            className={cn(
              "flex items-center px-3 py-2 rounded-md mb-1 transition-colors", 
              location === "/" ? "bg-primary-50 text-primary-700" : "text-slate-600 hover:bg-slate-50"
            )}>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
            </svg>
            Dashboard
          </Link>
          <Link href="/comparison" 
            className={cn(
              "flex items-center px-3 py-2 rounded-md transition-colors",
              location === "/comparison" ? "bg-primary-50 text-primary-700" : "text-slate-600 hover:bg-slate-50"
            )}>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            Comparison
          </Link>
        </div>
        
        {/* Servers List */}
        <div className="mb-4">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex justify-between items-center">
            <span>Servers</span>
            <span className="text-primary-600 bg-primary-50 rounded-full px-2 py-0.5 text-xs">
              {servers.length}
            </span>
          </h2>
          
          {servers.map((server) => (
            <Link 
              key={server.server_name}
              href={`/server/${encodeURIComponent(server.server_name)}`}
              className={cn(
                "flex items-center justify-between px-3 py-2 rounded-md mb-1 transition-colors",
                location === `/server/${encodeURIComponent(server.server_name)}` 
                  ? "bg-primary-50 text-primary-700" 
                  : "text-slate-600 hover:bg-slate-50"
              )}
            >
              <div className="flex items-center">
                <div className={cn(
                  "h-2 w-2 rounded-full mr-2",
                  server.status === 'online' ? "bg-success" : 
                  server.status === 'warning' ? "bg-warning" : "bg-error"
                )}></div>
                <span>{server.server_name}</span>
              </div>
              <span className="text-xs text-slate-500">{server.ip_address}</span>
            </Link>
          ))}
        </div>
        
        {/* Settings Section */}
        <div>
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Settings</h2>
          <button className="flex items-center px-3 py-2 rounded-md mb-1 text-slate-600 hover:bg-slate-50 transition-colors w-full text-left">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            Preferences
          </button>
          <button className="flex items-center px-3 py-2 rounded-md mb-1 text-slate-600 hover:bg-slate-50 transition-colors w-full text-left">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
            </svg>
            Server Management
          </button>
        </div>
      </nav>
    </div>
  );
}
