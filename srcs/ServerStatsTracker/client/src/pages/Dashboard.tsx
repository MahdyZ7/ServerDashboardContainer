import { useQuery } from "@tanstack/react-query";
import { ServerMetric, ServerStats, ServerUser, TimeSeriesDataPoint } from "@/types/server";
import SummaryCard from "@/components/dashboard/SummaryCard";
import ServerCard from "@/components/dashboard/ServerCard";
import ResourceUsersTable from "@/components/dashboard/ResourceUsersTable";
import MetricsChart from "@/components/dashboard/MetricsChart";
import { Skeleton } from "@/components/ui/skeleton";

export default function Dashboard() {
  // Fetch servers data
  const { data: servers = [], isLoading: isLoadingServers } = useQuery<ServerMetric[]>({
    queryKey: ['/api/metrics/latest'],
  });
  
  // Fetch top users data
  const { data: topUsers = [], isLoading: isLoadingUsers } = useQuery<ServerUser[]>({
    queryKey: ['/api/users/top'],
  });
  
  // Fetch stats summary
  const { data: stats, isLoading: isLoadingStats } = useQuery<ServerStats>({
    queryKey: ['/api/stats'],
  });
  
  // Fetch historical CPU data
  const { data: cpuHistory = [], isLoading: isLoadingCpuHistory } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: ['/api/metrics/history/cpu'],
  });
  
  // Fetch historical Memory data
  const { data: memoryHistory = [], isLoading: isLoadingMemoryHistory } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: ['/api/metrics/history/memory'],
  });
  
  // Format relative time
  const formatRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.round(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins === 1) return '1 minute ago';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return '1 day ago';
    return `${diffDays} days ago`;
  };
  
  return (
    <div>
      {/* Dashboard Title */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">All Servers Overview</h1>
        <p className="text-slate-500">Monitoring system health and performance metrics</p>
      </div>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {isLoadingStats ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-4 flex items-center">
                <Skeleton className="h-12 w-12 rounded-full mr-4" />
                <div className="w-full">
                  <Skeleton className="h-4 w-1/2 mb-2" />
                  <Skeleton className="h-6 w-1/3 mb-2" />
                  <Skeleton className="h-2 w-full" />
                </div>
              </div>
            ))}
          </>
        ) : (
          <>
            <SummaryCard 
              title="Total Servers"
              value={stats?.totalServers || 0}
              icon={
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"></path>
                </svg>
              }
              iconBgColor="bg-primary-100"
              iconColor="text-primary-600"
              subValues={[
                { label: "Online", value: stats?.onlineServers || 0, color: "bg-success" },
                { label: "Offline", value: stats?.offlineServers || 0, color: "bg-error" }
              ]}
            />
            
            <SummaryCard 
              title="CPU Load Average"
              value={(stats?.averageCpuLoad || 0).toFixed(2)}
              icon={
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
              }
              iconBgColor="bg-amber-100"
              iconColor="text-amber-600"
              change={{ value: "0.3", trend: "up" }}
            />
            
            <SummaryCard 
              title="Memory Usage"
              value={`${Math.round(stats?.averageMemoryUsage || 0)}%`}
              icon={
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              }
              iconBgColor="bg-emerald-100"
              iconColor="text-emerald-600"
              progressValue={stats?.averageMemoryUsage || 0}
            />
            
            <SummaryCard 
              title="Active Users"
              value={
                servers.reduce((sum, server) => sum + server.logged_users, 0)
              }
              icon={
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>
                </svg>
              }
              iconBgColor="bg-violet-100"
              iconColor="text-violet-600"
              subValues={[
                { 
                  label: "", 
                  value: `${servers.reduce((sum, server) => sum + server.active_ssh_users, 0)} SSH, ${servers.reduce((sum, server) => sum + server.active_vnc_users, 0)} VNC` 
                }
              ]}
            />
          </>
        )}
      </div>
      
      {/* Server Status Cards */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Server Status</h2>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-6">
        {isLoadingServers ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-4">
                <div className="flex justify-between mb-4">
                  <Skeleton className="h-6 w-1/3" />
                  <Skeleton className="h-6 w-10" />
                </div>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  {[...Array(3)].map((_, j) => (
                    <div key={j}>
                      <Skeleton className="h-4 w-16 mb-2" />
                      <Skeleton className="h-6 w-24 mb-2" />
                      <Skeleton className="h-2 w-full" />
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {[...Array(4)].map((_, j) => (
                    <div key={j}>
                      <Skeleton className="h-3 w-16 mb-1" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </>
        ) : (
          <>
            {servers.map((server) => (
              <ServerCard 
                key={server.server_name}
                server={server}
                lastUpdated={formatRelativeTime(server.timestamp)}
                ipAddress={`192.168.1.${Math.floor(Math.random() * 254) + 1}`} // Placeholder IP address
                status={
                  server.ram_percentage > 85 || server.disk_percentage > 85 || server.cpu_load_1min / server.virtual_cpus > 0.8
                    ? 'warning'
                    : 'online'
                }
              />
            ))}
          </>
        )}
      </div>
      
      {/* Active Users */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3 mt-8">Top Resource Users</h2>
      <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
        {isLoadingUsers ? (
          <div className="p-4">
            <Skeleton className="h-6 w-full mb-4" />
            <Skeleton className="h-12 w-full mb-2" />
            <Skeleton className="h-12 w-full mb-2" />
            <Skeleton className="h-12 w-full mb-2" />
            <Skeleton className="h-12 w-full mb-2" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : (
          <ResourceUsersTable users={topUsers} />
        )}
      </div>
      
      {/* Historical Data */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3 mt-8">Historical Trends</h2>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-6">
        {/* CPU Load History */}
        {isLoadingCpuHistory ? (
          <div className="bg-white rounded-lg shadow p-4">
            <Skeleton className="h-4 w-48 mb-4" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : (
          <MetricsChart 
            title="CPU Load Average (Last 24h)"
            data={cpuHistory}
            type="line"
            color="var(--chart-1)"
            yAxisLabel="Load"
          />
        )}
        
        {/* Memory Usage History */}
        {isLoadingMemoryHistory ? (
          <div className="bg-white rounded-lg shadow p-4">
            <Skeleton className="h-4 w-48 mb-4" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : (
          <MetricsChart 
            title="Memory Usage (Last 24h)"
            data={memoryHistory}
            type="line"
            color="var(--chart-2)"
            yAxisLabel="Usage %"
          />
        )}
      </div>
    </div>
  );
}
