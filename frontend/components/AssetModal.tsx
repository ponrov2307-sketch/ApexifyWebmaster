import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export default function AssetModal({ isOpen, onClose, onSave, onDelete, initialData }: any) {
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [cost, setCost] = useState('');
  const [alertPrice, setAlertPrice] = useState('0');
  const [group, setGroup] = useState('Auto');

  useEffect(() => {
    if (initialData) {
      setTicker(initialData.ticker || '');
      setShares(initialData.shares || '');
      setCost(initialData.cost || '');
      setAlertPrice(initialData.alert_price || '0');
      setGroup(initialData.group || 'Auto');
    } else {
      setTicker(''); setShares(''); setCost(''); setAlertPrice('0'); setGroup('Auto');
    }
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (!ticker) return alert('Please enter a Ticker');
    onSave({
      ticker: ticker.toUpperCase(),
      shares: Number(shares),
      cost: Number(cost),
      alert_price: Number(alertPrice),
      group
    });
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#161B22] border border-gray-700 rounded-2xl w-full max-w-md shadow-2xl p-6 relative">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-black text-[#D0FD3E]">{initialData ? `Edit Asset: ${ticker}` : 'Add New Asset'}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={24} /></button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-gray-400 text-xs font-bold mb-1 uppercase">Ticker</label>
            <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value)} readOnly={!!initialData} className={`w-full bg-[#0B0E14] border border-gray-800 rounded-lg px-4 py-3 text-white uppercase focus:border-[#D0FD3E] outline-none ${initialData ? 'opacity-50' : ''}`} placeholder="AAPL" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-400 text-xs font-bold mb-1 uppercase">Shares</label>
              <input type="number" value={shares} onChange={(e) => setShares(e.target.value)} className="w-full bg-[#0B0E14] border border-gray-800 rounded-lg px-4 py-3 text-white focus:border-[#D0FD3E] outline-none" placeholder="0.0" />
            </div>
            <div>
              <label className="block text-gray-400 text-xs font-bold mb-1 uppercase">Avg Cost</label>
              <input type="number" value={cost} onChange={(e) => setCost(e.target.value)} className="w-full bg-[#0B0E14] border border-gray-800 rounded-lg px-4 py-3 text-white focus:border-[#D0FD3E] outline-none" placeholder="0.0" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[#D0FD3E] text-xs font-bold mb-1 uppercase">Telegram Alert Price</label>
              <input type="number" value={alertPrice} onChange={(e) => setAlertPrice(e.target.value)} className="w-full bg-[#0B0E14] border border-[#D0FD3E] rounded-lg px-4 py-3 text-[#D0FD3E] font-bold outline-none" />
            </div>
            <div>
              <label className="block text-gray-400 text-xs font-bold mb-1 uppercase">Group</label>
              <select value={group} onChange={(e) => setGroup(e.target.value)} className="w-full bg-[#0B0E14] border border-gray-800 rounded-lg px-4 py-3 text-white focus:border-[#D0FD3E] outline-none">
                <option value="Auto">Auto</option><option value="DCA">DCA</option><option value="DIV">DIV</option>
              </select>
            </div>
          </div>
        </div>

        <div className="mt-8 flex justify-between">
          {initialData ? (
            <button onClick={() => onDelete(ticker)} className="text-[#FF453A] font-bold text-sm hover:underline">Delete Asset</button>
          ) : <div></div>}
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-gray-400 font-bold hover:text-white">Cancel</button>
            <button onClick={handleSubmit} className="bg-[#D0FD3E] text-black px-6 py-2 rounded-xl font-black hover:bg-white transition-colors">Save</button>
          </div>
        </div>
      </div>
    </div>
  );
}