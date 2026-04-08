import React, { useState, useEffect, useRef } from 'react';
import { predictionAPI } from '../../api/investments';

const MONTHS = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December'
];

const currentYear = new Date().getFullYear();
const YEARS = Array.from({ length: currentYear - 2012 }, (_, i) => currentYear - i);

// Confidence pill styling
const CONFIDENCE = {
  high:   { label: 'High confidence', color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' },
  medium: { label: 'Medium confidence', color: 'text-amber-400 bg-amber-400/10 border-amber-400/20' },
  low:    { label: 'Low confidence', color: 'text-red-400 bg-red-400/10 border-red-400/20' },
  none:   { label: 'No data — estimate', color: 'text-gray-500 bg-gray-800 border-gray-700' },
};

/**
 * PurchaseDatePicker
 *
 * Props:
 *   value        — ISO date string (the current purchase_date in parent form)
 *   onChange     — called with ISO string when date is confirmed
 *   itemId       — needed for prediction API call
 *   purchasePrice — needed for prediction API call
 */
export default function PurchaseDatePicker({ value, onChange, itemId, purchasePrice }) {
  // Parse current value into parts
  const parsed = value ? new Date(value) : new Date();
  const isToday = Math.abs(new Date() - parsed) < 1000 * 60 * 60 * 24;

  const [mode, setMode] = useState('exact'); // 'exact' | 'approx'
  const [day, setDay]     = useState(isToday ? '' : String(parsed.getDate()));
  const [month, setMonth] = useState(parsed.getMonth() + 1);  // 1-based
  const [year, setYear]   = useState(parsed.getFullYear());
  const [prediction, setPrediction] = useState(null); // API result
  const [predicting, setPredicting]  = useState(false);
  const debounceRef = useRef(null);

  // When month/year/purchasePrice changes in approx mode, run prediction
  useEffect(() => {
    if (mode !== 'approx' || !itemId || !purchasePrice || purchasePrice <= 0) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setPredicting(true);
      setPrediction(null);
      try {
        const result = await predictionAPI.predictEntryDate(itemId, month, year, purchasePrice);
        setPrediction(result);
        // Auto-apply the predicted date
        onChange(result.predicted_date);
      } catch {
        // Silently fall back — don't block the user
        const fallback = new Date(year, month - 1, 15).toISOString();
        onChange(fallback);
      } finally {
        setPredicting(false);
      }
    }, 600);
    return () => clearTimeout(debounceRef.current);
  }, [mode, month, year, purchasePrice, itemId]);

  // When day changes in exact mode, rebuild and emit ISO
  useEffect(() => {
    if (mode !== 'exact') return;
    const d = day ? parseInt(day) : 1;
    const clamped = Math.min(Math.max(d, 1), daysInMonth(month, year));
    const date = new Date(year, month - 1, clamped, 12, 0, 0);
    onChange(date.toISOString());
  }, [day, month, year, mode]);

  function daysInMonth(m, y) {
    return new Date(y, m, 0).getDate();
  }

  // Holding period display
  const held = (() => {
    if (!value) return null;
    const d = new Date(value);
    const days = Math.floor((new Date() - d) / 86400000);
    if (days < 1) return null;
    if (days < 30) return `${days}d`;
    const mo = Math.floor(days / 30);
    const yr = Math.floor(mo / 12);
    const rem = mo % 12;
    if (yr === 0) return `${mo}mo`;
    return rem === 0 ? `${yr}yr` : `${yr}yr ${rem}mo`;
  })();

  return (
    <div className="space-y-3">
      {/* Label row */}
      <div className="flex items-center justify-between">
        <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">
          Purchase Date
        </label>
        <div className="flex items-center gap-2">
          {held && (
            <span className="text-xs text-cyan-500/70 font-mono bg-cyan-500/10 px-2 py-0.5 rounded-full">
              {held} ago
            </span>
          )}
          {/* Mode toggle */}
          <div className="flex bg-gray-800 rounded-lg p-0.5 gap-0.5">
            {[['exact','Exact'],['approx','Approx']].map(([m, label]) => (
              <button key={m} type="button" onClick={() => setMode(m)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  mode === m ? 'bg-gray-700 text-white' : 'text-gray-600 hover:text-gray-400'
                }`}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Inputs */}
      <div className={`grid gap-2 ${mode === 'exact' ? 'grid-cols-3' : 'grid-cols-2'}`}>
        {/* Month */}
        <select value={month} onChange={e => setMonth(parseInt(e.target.value))}
          className="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-gray-300 text-sm focus:outline-none focus:border-cyan-500/50 transition-colors">
          {MONTHS.map((name, i) => (
            <option key={i+1} value={i+1}>{name}</option>
          ))}
        </select>

        {/* Year */}
        <select value={year} onChange={e => setYear(parseInt(e.target.value))}
          className="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-gray-300 text-sm focus:outline-none focus:border-cyan-500/50 transition-colors">
          {YEARS.map(y => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>

        {/* Day — exact mode only */}
        {mode === 'exact' && (
          <input
            type="number"
            min={1}
            max={daysInMonth(month, year)}
            value={day}
            onChange={e => setDay(e.target.value)}
            placeholder="Day"
            className="bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-gray-300 text-sm focus:outline-none focus:border-cyan-500/50 transition-colors placeholder-gray-600"
          />
        )}
      </div>

      {/* Approx mode — prediction feedback */}
      {mode === 'approx' && (
        <div className="rounded-xl border border-gray-800 bg-gray-800/40 px-3.5 py-2.5">
          {predicting ? (
            <div className="flex items-center gap-2 text-gray-500 text-xs">
              <span className="w-3 h-3 border border-gray-500 border-t-transparent rounded-full animate-spin" />
              Finding most likely entry date...
            </div>
          ) : prediction ? (
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-white text-sm font-medium">
                  {prediction.predicted_date_display}
                </p>
                <p className="text-gray-500 text-xs mt-0.5">
                  {prediction.fallback
                    ? 'No price data — mid-month estimate'
                    : `Market close was $${prediction.candle_close?.toFixed(2)} · ${prediction.price_delta_pct?.toFixed(1)}% from your entry`}
                </p>
              </div>
              {prediction.confidence && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium shrink-0 ${CONFIDENCE[prediction.confidence]?.color}`}>
                  {CONFIDENCE[prediction.confidence]?.label}
                </span>
              )}
            </div>
          ) : (
            <p className="text-gray-600 text-xs">
              {!purchasePrice || purchasePrice <= 0
                ? 'Enter a purchase price to get a predicted date'
                : !itemId
                ? 'Select an item first'
                : 'Select a month and year'}
            </p>
          )}
        </div>
      )}

      <p className="text-xs text-gray-700">
        {mode === 'exact'
          ? 'Day is optional — if unsure, switch to Approx mode.'
          : 'We find the most likely entry day using Steam price history for that month.'}
      </p>
    </div>
  );
}
