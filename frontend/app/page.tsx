"use client";

import React, { useState, useEffect } from 'react';
import { LineChart as ReLineChart, Line as ReLine, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Activity, Bot, Globe, Edit2, Newspaper, CandlestickChart, PlusCircle, X } from 'lucide-react';
import Chart from 'react-apexcharts';

// นำเข้า Component ที่เราแยกไฟล์ไว้
import StatCard from '../components/StatCard';
import AssetModal from '../components/AssetModal';

const COLORS = { success: "#32D74B", danger: "#FF453A" };

export default function ApexDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ALL');
  
  // Modal States
  const [isAssetModalOpen, setAssetModalOpen] = useState(false);
  const [selectedAssetForEdit, setSelectedAssetForEdit] = useState<any>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [ohlcData, setOhlcData] = useState<any[]>([]);

  const API_URL = "http://localhost:8000"; 

  const fetchData = async () => {
    try {
      const res = await fetch(`${API_URL}/api/portfolio`);
      const result = await res.json();
      if (result.summary) setData(result);
    } catch (error) {
      console.error("Connection Error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  // --- API Handlers ---
  const handleSaveAsset = async (payload: any) => {
    try {
      await fetch(`${API_URL}/api/asset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      setAssetModalOpen(false);
      fetchData();
    } catch (err) { alert("Failed to save asset"); }
  };

  const handleDeleteAsset = async (ticker: string) => {
    if (confirm(`Delete ${ticker}?`)) {
      try {
        await fetch(`${API_URL}/api/asset/${ticker}`, { method: 'DELETE' });
        setAssetModalOpen(false);
        fetchData();
      } catch (err) { alert("Failed to delete asset"); }
    }
  };

  const handleViewChart = async (ticker: string) => {
    setSelectedTicker(ticker);
    setOhlcData([]);
    try {
      const res = await fetch(`${API_URL}/api/chart/${ticker}`);
      const data = await res.json();
      setOhlcData(data);
    } catch (error) { console.error("Failed to load chart data"); }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#0B0E14] text-[#D0FD3E]">Loading Apex Live Data...</div>;

  const summary = data?.summary || {};
  const allAssets = data?.assets || [];
  const market = data?.market || [];
  const filteredAssets = activeTab === 'ALL' ? allAssets : allAssets.filter((a: any) => a.group === activeTab);

  return (
    <div className="min-h-screen bg-[#0B0E14] text-white font-sans flex flex-col relative">
      
      {/* Global Market Bar */}
      <div className="bg-[#11141C] border-b border-gray-800 text-xs py-2 px-6 flex items-center gap-6 overflow-x-auto shadow-md">
        <span className="text-gray-400 font-bold flex items-center gap-2 whitespace-nowrap"><Globe size={14} className="text-[#D0FD3E]"/> GLOBAL MARKET</span>
        {market.map((m: any, i: number) => (
          <div key={i} className="flex gap-2 items-center whitespace-nowrap">
            <span className="text-gray-200">{m.name}:</span><span className="font-bold text-white">{m.value}</span>
            <span className={m.change >= 0 ? 'text-[#32D74B]' : 'text-[#FF453A]'}>{m.change >= 0 ? '▲' : '▼'}{Math.abs(m.change).toFixed(2)}%</span>
          </div>
        ))}
      </div>

      <div className="flex-1 p-4 md:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          
          <div className="flex justify-between items-center bg-[#161B22] p-6 rounded-2xl border border-gray-800 shadow-xl">
            <div>
              <h1 className="text-4xl font-black text-[#D0FD3E]">APEX WEALTH MASTER</h1>
              <p className="text-gray-400 text-sm mt-1">Professional SaaS Portfolio Dashboard</p>
            </div>
            <button className="flex items-center gap-2 bg-[#D0FD3E] text-black px-6 py-3 rounded-2xl font-black hover:bg-white transition-all transform hover:scale-105">
              <Bot size={22} /> Ask AI
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard title="Total Invested" value={`$${summary.total_cost?.toLocaleString(undefined, {minimumFractionDigits: 2})}`} icon={<DollarSign size={24}/>} />
            <StatCard title="Net Worth" value={`$${summary.total_value?.toLocaleString(undefined, {minimumFractionDigits: 2})}`} icon={<Activity size={24}/>} highlight />
            <StatCard title="Total Profit / Loss" value={`$${summary.profit?.toLocaleString(undefined, {minimumFractionDigits: 2})} (${summary.profit_percent?.toFixed(2)}%)`} icon={summary.profit >= 0 ? <TrendingUp size={24}/> : <TrendingDown size={24}/>} color={summary.profit >= 0 ? COLORS.success : COLORS.danger}/>
          </div>

          <div className="bg-[#161B22] rounded-3xl border border-gray-800 shadow-xl overflow-hidden">
            <div className="p-4 border-b border-gray-800 bg-[#11141C] flex justify-between items-center">
              <div className="flex gap-2">
                {['ALL', 'DCA', 'Auto', 'DIV'].map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)} className={`px-6 py-2 rounded-xl font-bold text-sm transition-all ${activeTab === tab ? 'bg-[#D0FD3E] text-black shadow-inner' : 'bg-[#0B0E14] text-gray-400 hover:text-white border border-gray-800'}`}>
                      {tab === 'ALL' ? 'Overview' : tab}
                    </button>
                ))}
              </div>
              <button onClick={() => { setSelectedAssetForEdit(null); setAssetModalOpen(true); }} className="flex items-center gap-2 bg-[#D0FD3E] text-black font-bold px-4 py-2 rounded-xl text-sm hover:bg-white transition-colors">
                <PlusCircle size={16} /> Add Stock
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[#161B22] text-gray-500 text-xs uppercase tracking-wider">
                  <tr>
                    <th className="p-5">Ticker</th><th className="p-5 text-right">Shares</th><th className="p-5 text-right">Avg Cost</th><th className="p-5 text-right">Last Price</th>
                    <th className="p-5 text-center">Trend (7D)</th><th className="p-5 text-right">Profit</th><th className="p-5 text-center w-40">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {filteredAssets.map((asset: any, idx: number) => {
                    const sparkData = asset.sparkline?.map((val: number, i: number) => ({ i, val })) || [];
                    return (
                      <tr key={idx} className="hover:bg-[#1C2128] transition-colors">
                        <td className="p-5 font-black text-xl text-[#D0FD3E]">{asset.ticker}</td>
                        <td className="p-5 text-right text-lg text-gray-300 font-medium">{asset.shares.toFixed(4)}</td>
                        <td className="p-5 text-right text-lg text-gray-300 font-medium">${asset.cost.toFixed(2)}</td>
                        <td className="p-5 text-right text-lg text-white font-bold">${asset.last_price.toFixed(2)}</td>
                        <td className="p-5 w-32 h-20">
                          <ResponsiveContainer width="100%" height="100%">
                            <ReLineChart data={sparkData}>
                              <ReLine type="monotone" dataKey="val" stroke={asset.is_spark_up ? COLORS.success : COLORS.danger} strokeWidth={2.5} dot={false} />
                            </ReLineChart>
                          </ResponsiveContainer>
                        </td>
                        <td className={`p-5 text-right text-lg font-bold ${asset.profit >= 0 ? 'text-[#32D74B]' : 'text-[#FF453A]'}`}>
                          {asset.profit >= 0 ? '+' : ''}${asset.profit.toFixed(2)}
                        </td>
                        <td className="p-5">
                          <div className="flex gap-2 justify-center">
                              <button onClick={() => { setSelectedAssetForEdit(asset); setAssetModalOpen(true); }} className="p-2 bg-[#0B0E14] rounded-lg border border-gray-700 hover:border-[#D0FD3E] transition-all" title="Edit"><Edit2 size={16}/></button>
                              <button onClick={() => handleViewChart(asset.ticker)} className="p-2 bg-[#0B0E14] rounded-lg border border-gray-700 hover:border-[#D0FD3E] transition-all" title="Candlestick Chart"><CandlestickChart size={16} className="text-[#D0FD3E]"/></button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* --- Modals --- */}
      <AssetModal 
        isOpen={isAssetModalOpen} 
        onClose={() => setAssetModalOpen(false)} 
        initialData={selectedAssetForEdit} 
        onSave={handleSaveAsset} 
        onDelete={handleDeleteAsset} 
      />

      {/* Chart Modal */}
      {selectedTicker && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[#161B22] border border-gray-700 rounded-3xl w-full max-w-5xl shadow-2xl p-6 space-y-4 relative">
                <div className="flex justify-between items-center">
                    <h2 className="text-3xl font-black text-[#D0FD3E]">{selectedTicker} <span className='text-xl text-gray-400'>- Candlestick (1M / 1D)</span></h2>
                    <button onClick={() => setSelectedTicker(null)} className="text-gray-500 hover:text-white"><X size={28} /></button>
                </div>
                <div className="h-[500px] w-full bg-[#0B0E14] rounded-2xl p-4 flex items-center justify-center border border-gray-800">
                    {ohlcData.length > 0 ? (
                        <Chart options={{ chart: { type: 'candlestick', toolbar: { show: false }, background: 'transparent' }, theme: { mode: 'dark' }, grid: { borderColor: '#333' }, xaxis: { type: 'datetime' }, plotOptions: { candlestick: { colors: { upward: COLORS.success, downward: COLORS.danger }, wick: { useFillColor: true } } } }} series={[{ data: ohlcData }]} type="candlestick" height="100%" width="100%" />
                    ) : <div className="text-[#D0FD3E] animate-pulse">Loading Chart...</div>}
                </div>
            </div>
        </div>
      )}
    </div>
  );
}