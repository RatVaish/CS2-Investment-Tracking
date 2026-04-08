import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import Navbar from '../components/Navbar';
import PaywallModal from '../components/PaywallModal';
import { importAPI } from '../api/investments';
import { useAuth } from '../contexts/AuthContext';
import { formatCurrency } from '../utils/currency';

// ─── Steam Import ─────────────────────────────────────────────────────────────

function SteamImport({ isPro }) {
  const [step, setStep] = useState('idle'); // idle | loading | preview | importing | done
  const [inventory, setInventory] = useState(null);
  const [selected, setSelected] = useState({});
  const [prices, setPrices] = useState({});
  const [importing, setImporting] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);

  const fetchInventory = async () => {
    if (!isPro) { setShowPaywall(true); return; }
    setStep('loading');
    try {
      const data = await importAPI.getSteamInventory();
      setInventory(data);
      // Pre-select items that are in our DB and not already imported
      const sel = {};
      data.items.forEach(item => {
        if (item.in_our_db && !item.already_imported) sel[item.asset_id] = true;
      });
      setSelected(sel);
      setStep('preview');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to fetch inventory');
      setStep('idle');
    }
  };

  const toggleSelect = (assetId) => {
    setSelected(prev => ({ ...prev, [assetId]: !prev[assetId] }));
  };

  const selectAll = () => {
    const sel = {};
    inventory.items.filter(i => i.in_our_db && !i.already_imported).forEach(i => { sel[i.asset_id] = true; });
    setSelected(sel);
  };

  const clearAll = () => setSelected({});

  const handleImport = async () => {
    const toImport = inventory.items
      .filter(i => selected[i.asset_id] && i.in_our_db && !i.already_imported)
      .map(i => ({
        asset_id: i.asset_id,
        item_id: i.item_id,
        purchase_price: parseFloat(prices[i.asset_id] || 0),
        quantity: 1,
      }));

    if (!toImport.length) { toast.error('Select at least one item'); return; }

    const missingPrices = toImport.filter(i => !i.purchase_price || i.purchase_price <= 0);
    if (missingPrices.length) {
      toast.error(`Set purchase prices for all selected items (${missingPrices.length} missing)`);
      return;
    }

    setImporting(true);
    try {
      const result = await importAPI.importSteamItems(toImport);
      toast.success(`Imported ${result.imported} investment${result.imported !== 1 ? 's' : ''}`);
      if (result.errors?.length) toast.error(`${result.errors.length} items failed`);
      setStep('done');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const selectedCount = Object.values(selected).filter(Boolean).length;
  const importableItems = inventory?.items.filter(i => i.in_our_db && !i.already_imported) || [];

  return (
    <>
      {showPaywall && <PaywallModal onClose={() => setShowPaywall(false)} />}

      {step === 'idle' && (
        <div className="text-center py-10">
          <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-gray-700">
            <svg className="w-8 h-8 text-cyan-400" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
            </svg>
          </div>
          <h3 className="text-white font-semibold mb-2">Steam Inventory Import</h3>
          <p className="text-gray-500 text-sm mb-1 max-w-sm mx-auto">
            Fetch your CS2 inventory directly from Steam and import items as investments.
          </p>
          <p className="text-gray-600 text-xs mb-6">Your Steam inventory must be set to <span className="text-gray-400">Public</span></p>
          {!isPro && (
            <div className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-2 text-amber-400 text-xs mb-5">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3l14 9-14 9V3z" /></svg>
              Pro feature — upgrade to import from Steam
            </div>
          )}
          <div>
            <button onClick={fetchInventory}
              className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl font-semibold text-sm transition-colors">
              Fetch My Inventory
            </button>
          </div>
        </div>
      )}

      {step === 'loading' && (
        <div className="text-center py-16">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-sm">Fetching your Steam inventory...</p>
        </div>
      )}

      {step === 'done' && (
        <div className="text-center py-10">
          <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-white font-semibold mb-2">Import Complete</h3>
          <p className="text-gray-500 text-sm mb-6">Your investments have been added to your portfolio.</p>
          <button onClick={() => setStep('idle')} className="px-5 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm">
            Import More
          </button>
        </div>
      )}

      {step === 'preview' && inventory && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              { label: 'Total Items', value: inventory.total_assets },
              { label: 'Matched in DB', value: inventory.matched },
              { label: 'Already Imported', value: inventory.items.filter(i => i.already_imported).length },
            ].map(s => (
              <div key={s.label} className="bg-gray-800 rounded-xl py-3">
                <div className="text-lg font-bold text-white font-mono">{s.value}</div>
                <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <button onClick={selectAll} className="text-xs text-cyan-400 hover:text-cyan-300">Select all</button>
              <span className="text-gray-700">·</span>
              <button onClick={clearAll} className="text-xs text-gray-500 hover:text-gray-400">Clear</button>
            </div>
            <span className="text-xs text-gray-500">{selectedCount} selected</span>
          </div>

          {/* Item list */}
          {importableItems.length === 0 ? (
            <p className="text-center text-gray-600 text-sm py-8">All items already imported or not in our database.</p>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              {importableItems.map(item => (
                <div key={item.asset_id}
                  onClick={() => toggleSelect(item.asset_id)}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                    selected[item.asset_id]
                      ? 'border-cyan-500/40 bg-cyan-500/5'
                      : 'border-gray-800 bg-gray-800/40 hover:border-gray-700'
                  }`}>
                  <div className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center transition-all ${
                    selected[item.asset_id] ? 'bg-cyan-500 border-cyan-500' : 'border-gray-600'
                  }`}>
                    {selected[item.asset_id] && (
                      <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <img src={item.image_url} alt="" className="w-10 h-10 object-contain bg-gray-800 rounded-lg flex-shrink-0"
                    onError={e => { e.target.style.display='none'; }} />
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm truncate">{item.market_hash_name}</div>
                    <div className="flex gap-2 mt-0.5">
                      {item.rarity && <span className="text-xs text-gray-500">{item.rarity}</span>}
                      {item.wear && <span className="text-xs text-gray-600">{item.wear}</span>}
                    </div>
                  </div>
                  {selected[item.asset_id] && (
                    <div onClick={e => e.stopPropagation()}>
                      <input
                        type="number" step="0.01" min="0.01"
                        placeholder="Buy price"
                        value={prices[item.asset_id] || ''}
                        onChange={e => setPrices(prev => ({ ...prev, [item.asset_id]: e.target.value }))}
                        className="w-28 bg-gray-900 border border-gray-600 rounded-lg px-2.5 py-1.5 text-white text-xs font-mono focus:outline-none focus:border-cyan-500 placeholder-gray-600"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {importableItems.length > 0 && (
            <button onClick={handleImport} disabled={importing || selectedCount === 0}
              className="w-full py-3 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl font-semibold text-sm transition-colors">
              {importing ? 'Importing...' : `Import ${selectedCount} Item${selectedCount !== 1 ? 's' : ''}`}
            </button>
          )}
        </div>
      )}
    </>
  );
}

// ─── CSV Import ───────────────────────────────────────────────────────────────

function CSVImport({ isPro }) {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [importing, setImporting] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);
  const fileRef = useRef();

  const downloadTemplate = async () => {
    try {
      const blob = await importAPI.getCSVTemplate();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'floatbase_import_template.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download template');
    }
  };

  const handleImport = async () => {
    if (!isPro) { setShowPaywall(true); return; }
    if (!file) { toast.error('Select a CSV file first'); return; }
    setImporting(true);
    try {
      const data = await importAPI.importCSV(file);
      setResult(data);
      if (data.imported > 0) toast.success(`Imported ${data.imported} investment${data.imported !== 1 ? 's' : ''}`);
      if (data.errors?.length) toast.error(`${data.errors.length} rows had errors`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      {showPaywall && <PaywallModal onClose={() => setShowPaywall(false)} />}

      <div className="space-y-5">
        {/* Template download */}
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 flex items-start gap-3">
          <svg className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1 min-w-0">
            <p className="text-gray-300 text-sm font-medium">CSV format</p>
            <p className="text-gray-500 text-xs mt-1">
              Required columns: <code className="text-gray-400">market_hash_name, purchase_price, quantity</code><br />
              Optional: <code className="text-gray-400">purchase_date (YYYY-MM-DD), notes</code>
            </p>
          </div>
          <button onClick={downloadTemplate}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs transition-colors flex-shrink-0">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Template
          </button>
        </div>

        {/* File picker */}
        <div
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
            file ? 'border-cyan-500/40 bg-cyan-500/5' : 'border-gray-700 hover:border-gray-600 bg-gray-800/20'
          }`}>
          <input ref={fileRef} type="file" accept=".csv" className="hidden"
            onChange={e => { setFile(e.target.files[0]); setResult(null); }} />
          <svg className={`w-8 h-8 mx-auto mb-3 ${file ? 'text-cyan-400' : 'text-gray-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {file ? (
            <p className="text-cyan-300 text-sm font-medium">{file.name}</p>
          ) : (
            <>
              <p className="text-gray-400 text-sm">Click to select a CSV file</p>
              <p className="text-gray-600 text-xs mt-1">or drag and drop</p>
            </>
          )}
        </div>

        {!isPro && (
          <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-2.5 text-amber-400 text-xs">
            <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3l14 9-14 9V3z" /></svg>
            CSV import is a Pro feature — upgrade to import your data
          </div>
        )}

        <button onClick={handleImport} disabled={importing || !file}
          className="w-full py-3 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl font-semibold text-sm transition-colors">
          {importing ? 'Importing...' : 'Import CSV'}
        </button>

        {/* Results */}
        {result && (
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
              <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-emerald-300 text-sm">{result.imported} investment{result.imported !== 1 ? 's' : ''} imported successfully</span>
            </div>
            {result.errors?.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                <p className="text-red-400 text-xs font-medium mb-2">{result.errors.length} rows failed:</p>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {result.errors.map((e, i) => (
                    <p key={i} className="text-red-500/80 text-xs">Row {e.row}: {e.name || '—'} — {e.error}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Import() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [tab, setTab] = useState('steam');
  const isPro = user?.tier === 'pro';

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-2xl mx-auto px-6 pt-24 pb-12 space-y-5">
        {/* Back */}
        <button onClick={() => navigate('/app/portfolio')}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-300 transition-colors text-sm">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Portfolio
        </button>

        <div>
          <h1 className="text-2xl font-bold text-white">Import Investments</h1>
          <p className="text-gray-500 text-sm mt-1">Add multiple investments from Steam or a spreadsheet</p>
        </div>

        {/* Tabs */}
        <div className="flex bg-gray-900 border border-gray-800 rounded-2xl p-1 gap-1">
          {[
            { id: 'steam', label: 'Steam Inventory', icon: <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V8.91c0-2.495 2.028-4.524 4.524-4.524 2.494 0 4.524 2.031 4.524 4.527s-2.03 4.525-4.524 4.525h-.105l-4.076 2.911c0 .052.004.105.004.159 0 1.875-1.515 3.396-3.39 3.396-1.635 0-3.016-1.173-3.331-2.727L.436 15.27C1.862 20.307 6.486 24 11.979 24c6.627 0 11.999-5.373 11.999-12S18.605 0 11.979 0zM7.54 18.21l-1.473-.61c.262.543.714.999 1.314 1.25 1.297.539 2.793-.076 3.332-1.375.263-.63.264-1.319.005-1.949s-.75-1.121-1.377-1.383c-.624-.26-1.29-.249-1.878-.03l1.523.63c.956.4 1.409 1.5 1.009 2.455-.397.957-1.497 1.41-2.455 1.012H7.54zm11.415-9.303c0-1.662-1.353-3.015-3.015-3.015-1.665 0-3.015 1.353-3.015 3.015 0 1.665 1.35 3.015 3.015 3.015 1.663 0 3.015-1.35 3.015-3.015zm-5.273-.005c0-1.252 1.013-2.266 2.265-2.266 1.249 0 2.266 1.014 2.266 2.266 0 1.251-1.017 2.265-2.266 2.265-1.252 0-2.265-1.014-2.265-2.265z"/></svg> },
            { id: 'csv', label: 'CSV Import', icon: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg> },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all ${
                tab === t.id ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-400'
              }`}>
              {t.icon}
              {t.label}
              {!isPro && <span className="text-amber-400 text-xs">✦</span>}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          {tab === 'steam' ? <SteamImport isPro={isPro} /> : <CSVImport isPro={isPro} />}
        </div>
      </main>
    </div>
  );
}
