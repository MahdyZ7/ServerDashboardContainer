import { ServerUser } from "@/types/server";

interface ResourceUsersTableProps {
  users: ServerUser[];
}

export default function ResourceUsersTable({ users }: ResourceUsersTableProps) {
  const getInitials = (username: string) => {
    return username.substring(0, 2).toUpperCase();
  };
  
  const getBgColorClass = (username: string) => {
    // Generate a deterministic color based on the username
    const hash = username.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const colors = [
      'bg-primary-100 text-primary-700',
      'bg-amber-100 text-amber-700',
      'bg-emerald-100 text-emerald-700',
      'bg-violet-100 text-violet-700',
      'bg-red-100 text-red-700',
      'bg-blue-100 text-blue-700',
      'bg-green-100 text-green-700',
      'bg-purple-100 text-purple-700',
    ];
    
    return colors[hash % colors.length];
  };
  
  // Format disk usage to GB
  const formatDiskUsage = (sizeInGB: number) => {
    return `${sizeInGB.toFixed(2)} GB`;
  };
  
  // Get description based on username
  const getUserDescription = (username: string) => {
    const descriptions: Record<string, string> = {
      'jenkins': 'CI/CD Service',
      'postgres': 'Database Service',
      'nginx': 'Web Server',
      'apache': 'Web Service',
      'root': 'System Administrator',
      'mysql': 'Database Service',
      'www-data': 'Web Service',
      'tomcat': 'Application Server',
    };
    
    return descriptions[username] || 'User';
  };
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
              User
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
              Server
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
              CPU Usage
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
              Memory Usage
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
              Disk Usage
            </th>
            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-200">
          {users.map((user, index) => (
            <tr key={index} className="hover:bg-slate-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center mr-3 ${getBgColorClass(user.user)}`}>
                    <span className="font-medium">{getInitials(user.user)}</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-slate-900">{user.user}</div>
                    <div className="text-sm text-slate-500">{getUserDescription(user.user)}</div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="text-sm text-slate-900">{user.server_name}</span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="text-sm font-mono font-medium text-slate-900 mr-2">{user.cpu.toFixed(1)}%</div>
                  <div className="w-16 bg-slate-200 rounded-full h-1.5">
                    <div 
                      className="bg-primary-500 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(user.cpu, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="text-sm font-mono font-medium text-slate-900 mr-2">{user.mem.toFixed(1)}%</div>
                  <div className="w-16 bg-slate-200 rounded-full h-1.5">
                    <div 
                      className="bg-emerald-500 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(user.mem, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="text-sm font-mono font-medium text-slate-900">{formatDiskUsage(user.disk)}</span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button className="text-primary-600 hover:text-primary-900">Details</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
