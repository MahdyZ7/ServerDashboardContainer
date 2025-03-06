import { useQuery } from "@tanstack/react-query";
import { ServerMetric, TimeSeriesDataPoint } from "@/types/server";
import { Skeleton } from "@/components/ui/skeleton";
import MetricsChart from "@/components/dashboard/MetricsChart";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useEffect, useState } from "react";

export default function ServerComparison() {
  const [selectedServers, setSelectedServers] = useState<string[]>([]);

  // Fetch all servers
  const { data: serversMetrics = [], isLoading: isLoadingServers } = useQuery<ServerMetric[]>({
    queryKey: ['/api/metrics/latest'],
  });
  
  // Get unique server names
  const serverNames = ["KSRC1", "KSRC2", "KSRC3", "KSRC4", "KSRC5", "KSRC7"];	
  
  // Select all servers by default
  useEffect(() => {
    if (serverNames.length > 0 && selectedServers.length === 0) {
      setSelectedServers(serverNames);
    }
  }, [serverNames, selectedServers]);
  
  // Fetch comparison data for CPU
  const { data: cpuComparison = [], isLoading: isLoadingCpuComparison } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: ['/api/metrics/comparison/cpu'],
  });
  
  // Fetch comparison data for Memory
  const { data: memoryComparison = [], isLoading: isLoadingMemoryComparison } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: ['/api/metrics/comparison/memory'],
  });
  
  // Fetch comparison data for Disk
  const { data: diskComparison = [], isLoading: isLoadingDiskComparison } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: ['/api/metrics/comparison/disk'],
  });
  
  // Filter data by selected servers
  const filterDataBySelectedServers = (data: TimeSeriesDataPoint[]) => {
    return data.filter(point => point.server && selectedServers.includes(point.server));
  };
  
  // Toggle server selection
  const toggleServer = (serverName: string) => {
    setSelectedServers(prev => 
      prev.includes(serverName) 
        ? prev.filter(name => name !== serverName) 
        : [...prev, serverName]
    );
  };
  
  // Select/deselect all servers
  const toggleAllServers = () => {
    if (selectedServers.length === serverNames.length) {
      setSelectedServers([]);
    } else {
      setSelectedServers([...serverNames]);
    }
  };
  
  return (
    <div>
      {/* Page Title */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Server Comparison</h1>
        <p className="text-slate-500">Compare performance metrics across multiple servers</p>
      </div>
      
      {/* Server Selection */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-slate-800">Select Servers to Compare</h2>
          <Button 
            variant="outline" 
            size="sm"
            onClick={toggleAllServers}
          >
            {selectedServers.length === serverNames.length ? 'Deselect All' : 'Select All'}
          </Button>
        </div>
        
        {isLoadingServers ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {serverNames.map(serverName => (
              <div key={serverName} className="flex items-center space-x-2">
                <Checkbox 
                  id={`server-${serverName}`}
                  checked={selectedServers.includes(serverName)}
                  onCheckedChange={() => toggleServer(serverName)}
                />
                <label 
                  htmlFor={`server-${serverName}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {serverName}
                </label>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Comparison Charts */}
      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* CPU Load Comparison */}
        {isLoadingCpuComparison ? (
          <div className="bg-white rounded-lg shadow p-4">
            <Skeleton className="h-4 w-48 mb-4" />
            <Skeleton className="h-72 w-full" />
          </div>
        ) : (
          <MetricsChart 
            title="CPU Load Comparison"
            data={filterDataBySelectedServers(cpuComparison)}
            type="line"
            multiSeries={true}
            yAxisLabel="Load"
            height={300}
          />
        )}
        
        {/* Memory Usage Comparison */}
        {isLoadingMemoryComparison ? (
          <div className="bg-white rounded-lg shadow p-4">
            <Skeleton className="h-4 w-48 mb-4" />
            <Skeleton className="h-72 w-full" />
          </div>
        ) : (
          <MetricsChart 
            title="Memory Usage Comparison"
            data={filterDataBySelectedServers(memoryComparison)}
            type="line"
            multiSeries={true}
            yAxisLabel="Usage %"
            height={300}
          />
        )}
        
        {/* Disk Usage Comparison */}
        {isLoadingDiskComparison ? (
          <div className="bg-white rounded-lg shadow p-4">
            <Skeleton className="h-4 w-48 mb-4" />
            <Skeleton className="h-72 w-full" />
          </div>
        ) : (
          <MetricsChart 
            title="Disk Usage Comparison"
            data={filterDataBySelectedServers(diskComparison)}
            type="line"
            multiSeries={true}
            yAxisLabel="Usage %"
            height={300}
          />
        )}
      </div>
      
      {/* Comparison Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto mb-6">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Server
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Avg CPU (1min)
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Memory Usage
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Disk Usage
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Active Users
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Last Boot
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {isLoadingServers ? (
              [...Array(3)].map((_, i) => (
                <tr key={i}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Skeleton className="h-4 w-24" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Skeleton className="h-4 w-16" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Skeleton className="h-4 w-16" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Skeleton className="h-4 w-16" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Skeleton className="h-4 w-16" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Skeleton className="h-4 w-24" />
                  </td>
                </tr>
              ))
            ) : (
              serversMetrics
                .filter((server: ServerMetric) => selectedServers.includes(server.server_name))
                .map((server: ServerMetric) => (
                  <tr key={server.server_name} className="hover:bg-slate-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-slate-900">{server.server_name}</div>
                      <div className="text-sm text-slate-500">{server.operating_system}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-slate-900">{server.cpu_load_1min.toFixed(2)}</div>
                      <div className="text-xs text-slate-500">Load</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-slate-900">{server.ram_percentage}%</div>
                      <div className="text-xs text-slate-500">{server.ram_used}/{server.ram_total}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-slate-900">{server.disk_percentage}%</div>
                      <div className="text-xs text-slate-500">{server.disk_used}/{server.disk_total}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-slate-900">{server.logged_users}</div>
                      <div className="text-xs text-slate-500">
                        {server.active_ssh_users} SSH, {server.active_vnc_users} VNC
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                      {server.last_boot}
                    </td>
                  </tr>
                ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
