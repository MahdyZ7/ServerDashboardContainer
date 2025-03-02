import { TimeSeriesDataPoint } from "@/types/server";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, AreaChart, Area } from "recharts";
import { useState } from "react";

interface MetricsChartProps {
  title: string;
  data: TimeSeriesDataPoint[];
  type: 'line' | 'area';
  color?: string;
  yAxisLabel?: string;
  multiSeries?: boolean;
  height?: number;
}

export default function MetricsChart({
  title,
  data,
  type = 'line',
  color = "var(--chart-1)",
  yAxisLabel,
  multiSeries = false,
  height = 250
}: MetricsChartProps) {
  const [timeRange, setTimeRange] = useState<string>("1D");
  
  // Group the data by server if multiSeries is true
  const serverGroups = multiSeries 
    ? data.reduce<Record<string, TimeSeriesDataPoint[]>>((acc, point) => {
        if (point.server) {
          if (!acc[point.server]) {
            acc[point.server] = [];
          }
          acc[point.server].push(point);
        }
        return acc;
      }, {})
    : { default: data };
  
  // Get unique colors for each server
  const colors = [
    "var(--chart-1)",
    "var(--chart-2)",
    "var(--chart-3)",
    "var(--chart-4)",
    "var(--chart-5)",
  ];
  
  // Format timestamp for display
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={formatTime}
          tick={{ fontSize: 12, fill: "#4b5563" }}
          axisLine={{ stroke: "#9ca3af" }}
        />
        <YAxis 
          label={{ value: yAxisLabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: "#4b5563", fontWeight: 500 } }}
          tick={{ fontSize: 12, fill: "#4b5563" }}
          axisLine={{ stroke: "#9ca3af" }}
        />
        <Tooltip 
          formatter={(value: number) => [value.toFixed(2), yAxisLabel || 'Value']}
          labelFormatter={(label) => {
            const date = new Date(label);
            return date.toLocaleString();
          }}
          contentStyle={{ backgroundColor: "white", borderColor: "#e5e7eb", borderRadius: "4px" }}
        />
        {multiSeries ? (
          <>
            <Legend wrapperStyle={{ paddingTop: '10px' }} />
            {Object.entries(serverGroups).map(([server, points], index) => (
              <Line 
                key={server}
                type="monotone" 
                data={points}
                dataKey="value" 
                name={server}
                stroke={colors[index % colors.length]} 
                strokeWidth={2}
                activeDot={{ r: 8 }} 
              />
            ))}
          </>
        ) : (
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke={color} 
            strokeWidth={2}
            activeDot={{ r: 8 }} 
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
  
  const renderAreaChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={formatTime}
          tick={{ fontSize: 12, fill: "#4b5563" }}
          axisLine={{ stroke: "#9ca3af" }}
        />
        <YAxis 
          label={{ value: yAxisLabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: "#4b5563", fontWeight: 500 } }}
          tick={{ fontSize: 12, fill: "#4b5563" }}
          axisLine={{ stroke: "#9ca3af" }}
        />
        <Tooltip 
          formatter={(value: number) => [value.toFixed(2), yAxisLabel || 'Value']}
          labelFormatter={(label) => {
            const date = new Date(label);
            return date.toLocaleString();
          }}
          contentStyle={{ backgroundColor: "white", borderColor: "#e5e7eb", borderRadius: "4px" }}
        />
        {multiSeries ? (
          <>
            <Legend wrapperStyle={{ paddingTop: '10px' }} />
            {Object.entries(serverGroups).map(([server, points], index) => (
              <Area 
                key={server}
                type="monotone" 
                data={points}
                dataKey="value" 
                name={server}
                stroke={colors[index % colors.length]} 
                strokeWidth={2}
                fill={colors[index % colors.length]} 
                fillOpacity={0.4}
              />
            ))}
          </>
        ) : (
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke={color} 
            strokeWidth={2}
            fill={color} 
            fillOpacity={0.4}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
  
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 flex justify-between items-center">
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        <div className="flex items-center space-x-2">
          <button 
            className={`text-xs px-2 py-1 rounded ${timeRange === '1D' ? 'bg-slate-100 text-slate-600' : 'text-slate-600 hover:bg-slate-100'}`}
            onClick={() => setTimeRange('1D')}
          >
            1D
          </button>
          <button 
            className={`text-xs px-2 py-1 rounded ${timeRange === '7D' ? 'bg-slate-100 text-slate-600' : 'text-slate-600 hover:bg-slate-100'}`}
            onClick={() => setTimeRange('7D')}
          >
            7D
          </button>
          <button 
            className={`text-xs px-2 py-1 rounded ${timeRange === '30D' ? 'bg-slate-100 text-slate-600' : 'text-slate-600 hover:bg-slate-100'}`}
            onClick={() => setTimeRange('30D')}
          >
            30D
          </button>
        </div>
      </div>
      <div className="p-4">
        {type === 'line' ? renderLineChart() : renderAreaChart()}
      </div>
    </div>
  );
}
