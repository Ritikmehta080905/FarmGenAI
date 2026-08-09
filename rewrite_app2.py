import sys

try:
    with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add isLoading state
    content = content.replace(
        "const [isLogin, setIsLogin] = useState(true);", 
        "const [isLogin, setIsLogin] = useState(true);\n  const [isLoading, setIsLoading] = useState(false);"
    )

    # 2. Update handleLogin
    old_login = '''const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await fetch(${BASE_URL}/api/v1/auth/login, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
      } else {
        const data = await res.json();
        setAuthError(data.detail || 'Login failed. Please check credentials.');
      }
    } catch (e) {
      setAuthError('Unable to connect to backend server.');
    }
  };'''
    
    new_login = '''const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await fetch(${BASE_URL}/api/v1/auth/login, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
      } else {
        const data = await res.json();
        setAuthError(data.detail || 'Login failed. Please check credentials.');
      }
    } catch (e) {
      setAuthError('Unable to connect to backend server.');
    } finally {
      setIsLoading(false);
    }
  };'''
    if old_login in content:
        content = content.replace(old_login, new_login)
    else:
        print("Could not find old_login")

    # 3. Update handleSignup
    old_signup = '''const handleSignup = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    try {
      const res = await fetch(${BASE_URL}/api/v1/auth/register, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role, full_name: fullname })
      });

      if (res.ok) {
        setAuthSuccess('Registration successful! Please log in.');
        setIsLogin(true);
      } else {
        const data = await res.json();
        setAuthError(data.detail || 'Registration failed.');
      }
    } catch (e) {
      setAuthError('Connection error.');
    }
  };'''
  
    new_signup = '''const handleSignup = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    setIsLoading(true);
    try {
      const res = await fetch(${BASE_URL}/api/v1/auth/register, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role, full_name: fullname })
      });

      if (res.ok) {
        setAuthSuccess('Registration successful! Please log in.');
        setIsLogin(true);
      } else {
        const data = await res.json();
        setAuthError(data.detail || 'Registration failed.');
      }
    } catch (e) {
      setAuthError('Connection error.');
    } finally {
      setIsLoading(false);
    }
  };'''
    if old_signup in content:
        content = content.replace(old_signup, new_signup)
    else:
        print("Could not find old_signup")

    # 4. Imports
    content = content.replace(
        "RotateCcw\n} from 'lucide-react';", 
        "RotateCcw,\n  Loader2\n} from 'lucide-react';"
    )
    content = content.replace(
        "import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';",
        "import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';"
    )

    # 5. Buttons
    old_btn_login = '''<button 
                type="submit" 
                className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 hover:from-emerald-500 hover:to-emerald-400 transition-all active:scale-95"
              >
                Launch Stakeholder Node <ArrowRight size={16} />
              </button>'''
    new_btn_login = '''<button 
                type="submit" 
                disabled={isLoading}
                className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 hover:from-emerald-500 hover:to-emerald-400 transition-all active:scale-95 disabled:opacity-70"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin" /> : <>Launch Stakeholder Node <ArrowRight size={16} /></>}
              </button>'''
    content = content.replace(old_btn_login, new_btn_login)

    old_btn_signup = '''<button 
                type="submit" 
                className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 hover:from-emerald-500 hover:to-emerald-400 transition-all active:scale-95"
              >
                Register & Verify Node <UserCheck size={16} />
              </button>'''
    new_btn_signup = '''<button 
                type="submit" 
                disabled={isLoading}
                className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 hover:from-emerald-500 hover:to-emerald-400 transition-all active:scale-95 disabled:opacity-70"
              >
                {isLoading ? <Loader2 size={16} className="animate-spin" /> : <>Register & Verify Node <UserCheck size={16} /></>}
              </button>'''
    content = content.replace(old_btn_signup, new_btn_signup)

    # 6. Layout updates
    old_bottom_section = '''{/* Bottom Section: Graph, Logs, Nodes in a grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">'''
    new_bottom_section = '''{/* Bottom Section: Graph & Logs (Full Width) */}
            <div className="grid grid-cols-1 gap-6">'''
    content = content.replace(old_bottom_section, new_bottom_section)

    old_chart_container = '<div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl flex flex-col h-[400px]">'
    new_chart_container = '<div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-6 backdrop-blur-2xl shadow-2xl shadow-emerald-900/5 ring-1 ring-white/5 flex flex-col h-[500px]">'
    content = content.replace(old_chart_container, new_chart_container)

    old_nodes_container = '<div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-xl h-[400px] flex flex-col">'
    new_nodes_container = '<div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-6 backdrop-blur-2xl shadow-2xl shadow-emerald-900/5 ring-1 ring-white/5 flex flex-col h-auto">'
    content = content.replace(old_nodes_container, new_nodes_container)

    old_nodes_list = '<div className="space-y-3 overflow-y-auto pr-2 flex-1">'
    new_nodes_list = '<div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pr-2 flex-1">'
    content = content.replace(old_nodes_list, new_nodes_list)

    old_card_class = 'className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 transition-all hover:border-slate-700/60"'
    new_card_class = 'className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-5 transition-all hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-900/20 group"'
    content = content.replace(old_card_class, new_card_class)

    # 7. Add AreaChart
    old_chart = '''<LineChart data={priceSeries} margin={{ top: 20, right: 30, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="round" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => ?} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #1e293b', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }} 
                              itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                            />
                            <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: '#0f172a', stroke: '#10b981', strokeWidth: 2 }} activeDot={{ r: 6, fill: '#10b981', stroke: '#0f172a', strokeWidth: 2 }} />
                          </LineChart>'''
                          
    new_chart = '''<AreaChart data={priceSeries} margin={{ top: 20, right: 30, left: -20, bottom: 0 }}>
                            <defs>
                              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="round" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => ?} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #1e293b', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }} 
                              itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                            />
                            <Area type="monotone" dataKey="price" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorPrice)" activeDot={{ r: 6, fill: '#10b981', stroke: '#0f172a', strokeWidth: 2 }} />
                          </AreaChart>'''
    if old_chart in content:
        content = content.replace(old_chart, new_chart)
    else:
        print("Could not find old_chart")

    with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully modified App.jsx")

except Exception as e:
    print(f"Error: {e}")
