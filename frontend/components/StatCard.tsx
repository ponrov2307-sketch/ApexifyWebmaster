import React from 'react';

export default function StatCard({ title, value, icon, highlight, color }: any) {
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