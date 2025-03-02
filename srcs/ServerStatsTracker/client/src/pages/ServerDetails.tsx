import { useQuery } from "@tanstack/react-query";
import { useParams } from "wouter";
import { ServerMetric, ServerUser, TimeSeriesDataPoint } from "@/types/server";
import { Skeleton } from "@/components/ui/skeleton";
import ServerCard from "@/components/dashboard/ServerCard";
import ResourceUsersTable from "@/components/dashboard/ResourceUsersTable";
import MetricsChart from "@/components/dashboard/MetricsChart";

export default function ServerDetails() {
  const { id } = useParams<{ id: string }>();
  const decodedId = decodeURIComponent(id);
  
  // Fetch server metrics
  const { data: serverMetrics, isLoading: isLoadingServer } = useQuery<ServerMetric[]>({
    queryKey: [`/api/metrics/server/${decodedId}`],
  });
  
  // Fetch users for this server
  const { data: serverUsers = [], isLoading: isLoadingUsers } = useQuery<ServerUser[]>({
    queryKey: [`/api/users/server/${decodedId}`],
  });
  
  // Fetch historical CPU data for this server
  const { data: cpuHistory = [], isLoading: isLoadingCpuHistory } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: [`/api/metrics/history/cpu/${decodedId}`],
  });
  
  // Fetch historical Memory data for this server
  const { data: memoryHistory = [], isLoading: isLoadingMemoryHistory } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: [`/api/metrics/history/memory/${decodedId}`],
  });
  
  // Fetch historical Disk data for this server
  const { data: diskHistory = [], isLoading: isLoadingDiskHistory } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: [`/api/metrics/history/disk/${decodedId}`],
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
  
  const latestMetric = serverMetrics?.[0];
  
  return (
    <div>
      {/* Server Title */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Server Details: {decodedId}</h1>
        <p className="text-slate-500">Detailed performance metrics and resource usage</p>
      </div>
      
      {/* Server Overview */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Current Status</h2>
      {isLoadingServer ? (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
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
      ) : latestMetric ? (
        <div className="mb-6">
          <ServerCard 
            server={latestMetric}
            lastUpdated={formatRelativeTime(latestMetric.timestamp)}
            ipAddress={`192.168.1.${Math.floor(Math.random() * 254) + 1}`} // Placeholder IP address
            status={
              latestMetric.ram_percentage > 85 || latestMetric.disk_percentage > 85 || latestMetric.cpu_load_1min / latestMetric.virtual_cpus > 0.8
                ? 'warning'
                : 'online'
            }
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 mb-6 text-center">
          <p className="text-slate-500">No data available for this server.</p>
        </div>
      )}
      
      {/* Resource Users */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Top Resource Users</h2>
      <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
        {isLoadingUsers ? (
          <div className="p-4">
            <Skeleton className="h-6 w-full mb-4" />
            <Skeleton className="h-12 w-full mb-2" />
            <Skeleton className="h-12 w-full mb-2" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : serverUsers.length > 0 ? (
          <ResourceUsersTable users={serverUsers} />
        ) : (
          <div className="p-6 text-center">
            <p className="text-slate-500">No user data available for this server.</p>
          </div>
        )}
      </div>
      
      {/* Historical Metrics */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Historical Metrics</h2>
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
      
      {/* Additional Metrics */}
      <div className="grid grid-cols-1 mb-6">
        {/* Disk Usage History */}
        {isLoadingDiskHistory ? (
          <div className="bg-white rounded-lg shadow p-4">
            <Skeleton className="h-4 w-48 mb-4" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : (
          <MetricsChart 
            title="Disk Usage (Last 24h)"
            data={diskHistory}
            type="line"
            color="var(--chart-3)"
            yAxisLabel="Usage %"
          />
        )}
      </div>
    </div>
  );
}
