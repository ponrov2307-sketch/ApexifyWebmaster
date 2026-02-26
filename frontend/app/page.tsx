"use client";

import React, { useState, useEffect } from 'react';
import { LineChart as ReLineChart, Line as ReLine, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Activity, Send, Bot, Globe, Edit2, Newspaper, CandlestickChart, PlusCircle, X } from 'lucide-react';
// 🌟 นำเข้า ApexCharts
import Chart from 'react-apexcharts';

const COLORS = {
  accent: "#D0FD3E",
  card: "#161B22",
  bg: "#0B0E14",
  success: "#32D74B",
  danger: "#FF453A",
  chartColors: ["#D0FD3E", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6"]
};

export default function ApexDashboard() {
  const [data, setData] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // UI States
  const [activeTab, setActiveTab] = useState('ALL');
  const [chatOpen, setChatOpen] = useState(false);
  
  // 🌟 Chart Modal States
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [ohlcData, setOhlcData] = useState<any[]>([]);
  const [chartLoading, setChartLoading] = useState(false);

  const API_URL = "http://localhost:8000"; 

  const fetchData = async () => {
    try {
      const [portRes, histRes] = await Promise.all([
        fetch(`${API_URL}/api/portfolio`).then(res => res.json()),
        fetch(`${API_URL}/api/history`).then(res => res.json())
      ]);
      if (portRes.summary) setData(portRes);
      if (Array.isArray(histRes)) setHistory(histRes);
    } catch (error) {
      console.error("Connection Error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-update ทุกๆ 60 วินาที (เหมือน Desktop)
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  // 🌟 ฟังก์ชันเมื่อกดปุ่ม "ดูกราฟ"
  const handleViewChart = async (ticker: str) => {
    setSelectedTicker(ticker);
    setChartLoading(true);
    setOhlcData([]);
    try {
        const res = await fetch(`${API_URL}/api/chart/${ticker}`);
        const data = await res.json();
        setOhlcData(data);
    } catch (error) {
        console.error("Failed to load chart data");
    } finally {
        setChartLoading(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#0B0E14] text-[#D0FD3E]">Loading Apex Live Data...</div>;

  const summary = data?.summary || {};
  const allAssets = data?.assets || [];
  const market = data?.market || [];

  const filteredAssets = activeTab === 'ALL' ? allAssets : allAssets.filter((a: any) => a.group === activeTab);

  return (
    <div className="min-h-screen bg-[#0B0E14] text-white font-sans flex flex-col relative">
      
      {/* 1. Rework Top Market Bar (Bloomberg Style) */}
      <div className="bg-[#11141C] border-b border-gray-800 text-xs py-2 px-6 flex items-center gap-6 overflow-x-auto shadow-md z-10 relative">
        <span className="text-gray-400 font-bold flex items-center gap-2 whitespace-nowrap">
          <Globe size={14} className="text-[#D0FD3E]"/> GLOBAL MARKET WATCH
        </span>
        {market.map((m: any, i: number) => (
          <div key={i} className="flex gap-2 items-center whitespace-nowrap">
            <span className="text-gray-200">{m.name}:</span>
            <span className="font-bold text-white">{m.value}</span>
            <span className={m.change >= 0 ? 'text-[#32D74B]' : 'text-[#FF453A]'}>
              {m.change >= 0 ? '▲' : '▼'}{Math.abs(m.change).toFixed(2)}%
            </span>
          </div>
        ))}
      </div>

      <div className="flex-1 p-4 md:p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* --- Header --- */}
          <div className="flex justify-between items-center bg-[#161B22] p-6 rounded-2xl border border-gray-800 shadow-xl">
            <div>
              <h1 className="text-4xl font-black text-[#D0FD3E]">APEX WEALTH MASTER</h1>
              <p className="text-gray-400 text-sm mt-1">Professional SaaS Portfolio Dashboard (Live yfinance)</p>
            </div>
            <button onClick={() => setChatOpen(!chatOpen)} className="flex items-center gap-2 bg-[#D0FD3E] text-black px-6 py-3 rounded-2xl font-black hover:bg-white transition-all transform hover:scale-105 shadow-lg">
              <Bot size={22} /> Ask AI
            </button>
          </div>

          {/* --- Stats Cards --- */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard title="Total Invested" value={`$${summary.total_cost?.toLocaleString()}`} icon={<DollarSign size={24}/>} />
            <StatCard title="Net Worth" value={`$${summary.total_value?.toLocaleString()}`} icon={<Activity size={24}/>} highlight />
            <StatCard title="Total Profit / Loss" value={`$${summary.profit?.toLocaleString()} (${summary.profit_percent?.toFixed(2)}%)`} icon={summary.profit >= 0 ? <TrendingUp size={24}/> : <TrendingDown size={24}/>} color={summary.profit >= 0 ? COLORS.success : COLORS.danger}/>
          </div>

          {/* --- 2. Rework Main Content Area --- */}
          <div className="bg-[#161B22] rounded-3xl border border-gray-800 shadow-xl overflow-hidden flex flex-col">
            
            {/* Tabs & Add Stock Button */}
            <div className="p-4 border-b border-gray-800 bg-[#11141C] flex justify-between items-center gap-4">
              <div className="flex gap-2">
                {['ALL', 'DCA', 'Auto', 'DIV'].map(tab => (
                    <button 
                    key={tab} 
                    onClick={() => setActiveTab(tab)}
                    className={`px-6 py-2 rounded-xl font-bold text-sm transition-all duration-300 ${activeTab === tab ? 'bg-[#D0FD3E] text-black shadow-inner' : 'bg-[#0B0E14] text-gray-400 hover:text-white border border-gray-800'}`}
                    >
                    {tab === 'ALL' ? 'Overview' : tab}
                    </button>
                ))}
              </div>
              {/* 🌟 ปุ่ม Add Stock ที่มุมขวาบนของตาราง */}
              <button className="flex items-center gap-2 bg-[#0B0E14] border border-gray-800 text-white px-4 py-2 rounded-xl text-sm hover:border-[#D0FD3E] hover:text-[#D0FD3E] transition-colors">
                <PlusCircle size={16} /> Add Stock
              </button>
            </div>

            {/* Assets Table Rework */}
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[#161B22] text-gray-500 text-xs uppercase tracking-wider">
                  <tr>
                    <th className="p-5">Ticker</th>
                    <th className="p-5 text-right">Shares</th>
                    <th className="p-5 text-right">Avg Cost</th>
                    <th className="p-5 text-right">Last Price</th>
                    <th className="p-5 text-center">Trend (7D)</th> {/* 🌟 Sparkline */}
                    <th className="p-5 text-right">Profit</th>
                    <th className="p-5 text-center w-40">Actions</th> {/* 🌟 คอลัมน์ปุ่มคำสั่งใหม่ */}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {filteredAssets.length === 0 ? (
                    <tr><td colSpan={7} className="text-center py-10 text-gray-500">ไม่มีหุ้นในกลุ่ม {activeTab}</td></tr>
                  ) : (
                    filteredAssets.map((asset: any, idx: number) => {
                      const currentPrice = asset.last_price || asset.cost;
                      const profit = (currentPrice - asset.cost) * asset.shares;
                      const isUp = currentPrice >= asset.cost;
                      const isSparkUp = asset.is_spark_up;
                      
                      // Format Sparkline Data
                      const sparkData = asset.sparkline?.map((val: number, i: number) => ({ i, val })) || [];

                      return (
                        <tr key={idx} className="hover:bg-[#1C2128] transition-colors group">
                          <td className="p-5 font-black text-xl text-[#D0FD3E] whitespace-nowrap">{asset.ticker}</td>
                          <td className="p-5 text-right text-lg text-gray-300 font-medium">{asset.shares.toFixed(4)}</td>
                          <td className="p-5 text-right text-lg text-gray-300 font-medium">${asset.cost.toFixed(2)}</td>
                          <td className="p-5 text-right text-lg text-white font-bold">${currentPrice.toFixed(2)}</td>
                          
                          {/* Sparkline จิ๋ว */}
                          <td className="p-5 w-32 h-20">
                            <ResponsiveContainer width="100%" height="100%">
                              <ReLineChart data={sparkData}>
                                <ReLine type="monotone" dataKey="val" stroke={isSparkUp ? COLORS.success : COLORS.danger} strokeWidth={2.5} dot={false} isAnimationActive={true} />
                              </ReLineChart>
                            </ResponsiveContainer>
                          </td>

                          <td className={`p-5 text-right text-lg font-bold ${isUp ? 'text-[#32D74B]' : 'text-[#FF453A]'}`}>
                            {isUp ? '+' : ''}${profit.toFixed(2)}
                          </td>
                          
                          {/* 🌟 ปุ่มคำสั่ง Edit / News / Chart */}
                          <td className="p-5">
                            <div className="flex gap-2 justify-center">
                                <IconButton icon={<Edit2 size={16}/>} title="Edit" />
                                <IconButton icon={<Newspaper size={16}/>} title="News" />
                                <IconButton 
                                    icon={<CandlestickChart size={16} className="text-[#D0FD3E]"/>} 
                                    title="View Candlestick Chart"
                                    onClick={() => handleViewChart(asset.ticker)} // 🌟 กดดูกราฟ
                                />
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* --- 3. 🌟 Candlestick Chart Modal --- */}
      {selectedTicker && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[#161B22] border border-gray-700 rounded-3xl w-full max-w-5xl shadow-2xl relative p-6 space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="text-3xl font-black text-[#D0FD3E]">{selectedTicker} <span className='text-xl text-gray-400 font-bold'>- Live Candlestick (1M / 1D)</span></h2>
                    <button onClick={() => setSelectedTicker(null)} className="text-gray-500 hover:text-white"><X size={28} /></button>
                </div>
                
                <div className="h-[500px] w-full bg-[#0B0E14] rounded-2xl p-4 flex items-center justify-center border border-gray-800">
                    {chartLoading ? (
                        <div className="text-[#D0FD3E] animate-pulse">Loading Chart Data...</div>
                    ) : (
                        ohlcData.length > 0 ? (
                            <div id="chart" className='w-full h-full'>
                            <Chart 
                                options={{
                                    chart: { type: 'candlestick', toolbar: { show: false }, background: 'transparent' },
                                    theme: { mode: 'dark' },
                                    grid: { borderColor: '#333', strokeDashArray: 3 },
                                    xaxis: { type: 'datetime', labels: { style: { colors: '#777' } }, axisBorder: { show: false }, axisTicks: { show: false } },
                                    yaxis: { tooltip: { enabled: true }, labels: { style: { colors: '#777' } } },
                                    plotOptions: { 
                                        candlestick: { 
                                            colors: { upward: COLORS.success, downward: COLORS.danger },
                                            wick: { useFillColor: true }
                                        } 
                                    },
                                    tooltip: { x: { format: 'dd MMM yyyy' } }
                                }}
                                series={[{ name: selectedTicker, data: ohlcData }]}
                                type="candlestick"
                                height="100%"
                                width="100%"
                            />
                            </div>
                        ) : <div className="text-gray-500">No chart data found for {selectedTicker}</div>
                    )}
                </div>
            </div>
        </div>
      )}

    </div>
  );
}

// Component ย่อย: IconButton สำหรับตาราง
function IconButton({ icon, title, onClick }: any) {
    return (
        <button 
            title={title} 
            onClick={onClick}
            className="p-2 bg-[#0B0E14] rounded-lg border border-gray-700 hover:border-[#D0FD3E] hover:bg-[#1C2128] transition-all group"
        >
            <span className='group-hover:scale-110 transition-transform'>
            {icon}
            </span>
        </button>
    )
}

// Component ย่อย: การ์ดแสดงผล
function StatCard({ title, value, icon, highlight, color }: any) {
  return (
    <div className={`p-6 rounded-2xl border bg-[#161B22] border-gray-800 shadow-xl relative overflow-hidden group`}>
      <div className="flex justify-between items-start z-10 relative">
        <div>
          <p className="text-gray-400 text-xs font-bold uppercase tracking-widest mb-1">{title}</p>
          <h3 className={`text-4xl font-black ${highlight ? 'text-[#D0FD3E]' : color || 'text-white'}`}>{value}</h3>
        </div>
        <div className={`p-4 rounded-2xl ${highlight ? 'bg-[#D0FD3E]/10 text-[#D0FD3E]' : 'bg-gray-800/50 text-gray-400'}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}