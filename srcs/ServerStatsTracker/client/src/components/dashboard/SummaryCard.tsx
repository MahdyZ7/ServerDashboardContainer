import { cn } from "@/lib/utils";

interface SummaryCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  iconBgColor: string;
  iconColor: string;
  subValues?: { label: string; value: string | number; color?: string }[];
  progressValue?: number;
  progressColor?: string;
  change?: {
    value: string | number;
    trend: 'up' | 'down';
  };
}

export default function SummaryCard({
  title,
  value,
  icon,
  iconBgColor,
  iconColor,
  subValues,
  progressValue,
  progressColor = 'bg-emerald-500',
  change
}: SummaryCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4 flex items-center">
      <div className={cn("p-3 rounded-full mr-4", iconBgColor, iconColor)}>
        {icon}
      </div>
      <div className="w-full">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <p className="text-xl font-semibold">{value}</p>
        
        {subValues && (
          <div className="flex items-center mt-1">
            {subValues.map((subValue, index) => (
              <div key={index} className="flex items-center mr-3">
                {subValue.color && (
                  <div className={cn("h-2 w-2 rounded-full mr-1", subValue.color)}></div>
                )}
                <span className="text-xs text-slate-500">{subValue.label}: {subValue.value}</span>
              </div>
            ))}
          </div>
        )}
        
        {progressValue !== undefined && (
          <div className="w-full bg-slate-200 rounded-full h-1.5 mt-1">
            <div 
              className={cn("h-1.5 rounded-full", progressColor)} 
              style={{ width: `${progressValue}%` }}
            ></div>
          </div>
        )}
        
        {change && (
          <p className={cn(
            "text-xs flex items-center mt-1",
            change.trend === 'up' ? 'text-green-600' : 'text-red-600'
          )}>
            <svg className="h-3 w-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d={change.trend === 'up' ? "M5 10l7-7m0 0l7 7m-7-7v18" : "M19 14l-7 7m0 0l-7-7m7 7V3"}
              ></path>
            </svg>
            {change.value} from yesterday
          </p>
        )}
      </div>
    </div>
  );
}
