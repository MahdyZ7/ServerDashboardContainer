import { cn } from "@/lib/utils";
import { ServerMetric } from "@/types/server";
import { Link } from "wouter";

interface ServerCardProps {
  server: ServerMetric;
  lastUpdated: string;
  ipAddress?: string;
  status: 'online' | 'warning' | 'offline';
}

export default function ServerCard({ server, lastUpdated, ipAddress, status }: ServerCardProps) {
  const formatSize = (size: string) => {
    return size;
  };
  
  if (status === 'offline') {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-start">
          <div>
            <div className="flex items-center">
              <div className="h-2 w-2 rounded-full bg-error mr-2"></div>
              <h3 className="text-lg font-semibold text-slate-800">{server.server_name}</h3>
            </div>
            <p className="text-slate-500 text-sm">{ipAddress} • Last updated: {lastUpdated}</p>
          </div>
          <div className="flex space-x-2">
            <Link href={`/server/${encodeURIComponent(server.server_name)}`} className="p-1 rounded text-slate-400 hover:text-primary-500 hover:bg-slate-50">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
            </Link>
          </div>
        </div>
        
        <div className="p-6">
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <svg className="h-12 w-12 text-slate-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <h3 className="text-lg font-medium text-slate-700 mb-1">Server Offline</h3>
              <p className="text-slate-500 mb-4">Unable to connect to this server.</p>
              <button className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors">
                Retry Connection
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-start">
        <div>
          <div className="flex items-center">
            <div className={cn(
              "h-2 w-2 rounded-full mr-2",
              status === 'online' ? 'bg-success' : 'bg-warning'
            )}></div>
            <h3 className="text-lg font-semibold text-slate-800">{server.server_name}</h3>
          </div>
          <p className="text-slate-500 text-sm">{ipAddress} • Last updated: {lastUpdated}</p>
        </div>
        <div className="flex space-x-2">
          <Link href={`/server/${encodeURIComponent(server.server_name)}`} className="p-1 rounded text-slate-400 hover:text-primary-500 hover:bg-slate-50">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
          </Link>
        </div>
      </div>
      
      <div className="p-6">
        <div className="grid grid-cols-3 gap-4 mb-4">
          {/* CPU */}
          <div>
            <h4 className="text-sm font-medium text-slate-500 mb-1">CPU Load</h4>
            <div className="flex items-end">
              <span className="text-2xl font-semibold font-mono text-slate-800">{server.cpu_load_1min}</span>
              <span className="text-xs text-slate-500 ml-1 mb-1">/{server.virtual_cpus} vCPUs</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
              <div 
                className={cn(
                  "h-2 rounded-full", 
                  server.cpu_load_1min / server.virtual_cpus > 0.7 ? "bg-error" : 
                  server.cpu_load_1min / server.virtual_cpus > 0.5 ? "bg-warning" : "bg-primary-500"
                )} 
                style={{ width: `${Math.min(server.cpu_load_1min / server.virtual_cpus * 100, 100)}%` }}
              ></div>
            </div>
          </div>
          
          {/* Memory */}
          <div>
            <h4 className="text-sm font-medium text-slate-500 mb-1">Memory</h4>
            <div className="flex items-end">
              <span className="text-2xl font-semibold font-mono text-slate-800">{server.ram_percentage}%</span>
              <span className="text-xs text-slate-500 ml-1 mb-1">{server.ram_used}/{server.ram_total}</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
              <div 
                className={cn(
                  "h-2 rounded-full", 
                  server.ram_percentage > 80 ? "bg-error" : 
                  server.ram_percentage > 60 ? "bg-warning" : "bg-emerald-500"
                )} 
                style={{ width: `${server.ram_percentage}%` }}
              ></div>
            </div>
          </div>
          
          {/* Disk */}
          <div>
            <h4 className="text-sm font-medium text-slate-500 mb-1">Disk</h4>
            <div className="flex items-end">
              <span className="text-2xl font-semibold font-mono text-slate-800">{server.disk_percentage}%</span>
              <span className="text-xs text-slate-500 ml-1 mb-1">{formatSize(server.disk_used)}/{formatSize(server.disk_total)}</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
              <div 
                className={cn(
                  "h-2 rounded-full", 
                  server.disk_percentage > 85 ? "bg-error" : 
                  server.disk_percentage > 70 ? "bg-warning" : "bg-violet-500"
                )} 
                style={{ width: `${server.disk_percentage}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-xs font-medium text-slate-500">Operating System</p>
            <p className="text-sm font-medium mt-1">{server.operating_system}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">TCP Connections</p>
            <p className="text-sm font-medium mt-1">{server.tcp_connections}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Active Users</p>
            <p className="text-sm font-medium mt-1">
              {server.logged_users} ({server.active_ssh_users} SSH, {server.active_vnc_users} VNC)
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Last Boot</p>
            <p className="text-sm font-medium mt-1">{server.last_boot}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
