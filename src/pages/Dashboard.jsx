import React from 'react';
import { 
  ArrowUpRight, 
  ArrowDownRight, 
  Users, 
  Activity, 
  ShieldAlert, 
  Server
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from 'recharts';

const areaData = [
  { name: 'Mon', active: 4000, blocked: 2400 },
  { name: 'Tue', active: 3000, blocked: 1398 },
  { name: 'Wed', active: 2000, blocked: 9800 },
  { name: 'Thu', active: 2780, blocked: 3908 },
  { name: 'Fri', active: 1890, blocked: 4800 },
  { name: 'Sat', active: 2390, blocked: 3800 },
  { name: 'Sun', active: 3490, blocked: 4300 },
];

const barData = [
  { name: 'US East', traffic: 4000 },
  { name: 'US West', traffic: 3000 },
  { name: 'EU Central', traffic: 2000 },
  { name: 'AP South', traffic: 2780 },
];

const StatCard = ({ title, value, change, isPositive, icon: Icon, timeFrame }) => (
  <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
        <h3 className="text-2xl font-bold text-slate-800">{value}</h3>
      </div>
      <div className={`p-3 rounded-lg ${isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
        <Icon className="w-6 h-6" />
      </div>
    </div>
    <div className="mt-4 flex items-center">
      <span className={`flex items-center text-sm font-medium ${isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
        {isPositive ? <ArrowUpRight className="w-4 h-4 mr-1" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
        {change}%
      </span>
      <span className="text-sm text-slate-500 ml-2">vs {timeFrame}</span>
    </div>
  </div>
);

const Dashboard = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard Overview</h1>
          <p className="text-slate-500 mt-1">Welcome back! Here's what's happening with your system today.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 font-medium transition-colors">
            Download Report
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-sm transition-colors">
            Generate Key
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Active Users" 
          value="24,592" 
          change="12.5" 
          isPositive={true} 
          icon={Users}
          timeFrame="last week"
        />
        <StatCard 
          title="System Events" 
          value="142.3k" 
          change="8.2" 
          isPositive={true} 
          icon={Activity}
          timeFrame="last week"
        />
        <StatCard 
          title="Threats Blocked" 
          value="4,291" 
          change="2.4" 
          isPositive={false} 
          icon={ShieldAlert}
          timeFrame="yesterday"
        />
        <StatCard 
          title="Server Load" 
          value="42%" 
          change="5.1" 
          isPositive={true} 
          icon={Server}
          timeFrame="yesterday"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-slate-800">Network Traffic Analysis</h2>
            <select className="bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2">
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>This Year</option>
            </select>
          </div>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={areaData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorActive" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value / 1000}k`} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  labelStyle={{ fontWeight: 'bold', color: '#1e293b', marginBottom: '4px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                <Area type="monotone" dataKey="active" name="Active Connections" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorActive)" />
                <Area type="monotone" dataKey="blocked" name="Blocked Requests" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorBlocked)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 mb-6">Regional Distribution</h2>
          <div className="h-64 w-full mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} width={80} />
                <Tooltip cursor={{fill: 'transparent'}} />
                <Bar dataKey="traffic" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          <div className="space-y-4">
            <h3 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">Recent Alerts</h3>
            <div className="flex items-start gap-3 p-3 bg-rose-50 rounded-lg border border-rose-100">
              <ShieldAlert className="w-5 h-5 text-rose-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-rose-800">Multiple login failures</p>
                <p className="text-xs text-rose-600 mt-1">IP: 192.168.1.42 • 2 mins ago</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
              <Activity className="w-5 h-5 text-amber-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800">High CPU usage detected</p>
                <p className="text-xs text-amber-600 mt-1">Node: eu-central-1 • 15 mins ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
