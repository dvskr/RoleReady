import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface TrendsData {
  t: string;
  score: number;
  coverage: number;
  mode: string;
}

interface TrendsProps {
  data: TrendsData[];
}

export function Trends({ data }: TrendsProps) {
  if (!data || data.length === 0) {
    return (
      <div className="border rounded p-3">
        <div className="font-medium mb-2">Score Trend</div>
        <div className="text-sm text-gray-500 text-center py-8">
          No analytics data yet. Run some analyses to see trends!
        </div>
      </div>
    );
  }

  return (
    <div className="border rounded p-3">
      <div className="font-medium mb-2">Score Trend</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <XAxis 
            dataKey="t" 
            hide 
            tick={{ fontSize: 10 }}
          />
          <YAxis 
            domain={[0, 100]} 
            tick={{ fontSize: 10 }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip 
            formatter={(value: number, name: string) => [
              `${value.toFixed(1)}%`, 
              name === 'score' ? 'Score' : 'Coverage'
            ]}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="score" 
            stroke="#6366f1" 
            strokeWidth={2}
            dot={{ fill: '#6366f1', strokeWidth: 2, r: 4 }}
            name="Score"
          />
          <Line 
            type="monotone" 
            dataKey="coverage" 
            stroke="#10b981" 
            strokeWidth={2}
            dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
            name="Coverage"
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="mt-2 text-xs text-gray-600">
        <div>📈 Score: How well your resume matches job descriptions</div>
        <div>🎯 Coverage: Percentage of job keywords covered</div>
      </div>
    </div>
  );
}
