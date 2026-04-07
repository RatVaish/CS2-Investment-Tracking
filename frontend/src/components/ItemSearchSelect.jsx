import React, { useState, useEffect, useRef, useCallback } from 'react';
import { itemsAPI } from '../api/items';
import { formatCurrency } from '../utils/currency';

function HighlightedText({ text, query }) {
  if (!query || !text) return <span className="text-gray-300">{text}</span>;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
  return (
    <span>
      {parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase()
          ? <span key={i} className="text-white font-semibold">{part}</span>
          : <span key={i} className="text-gray-500">{part}</span>
      )}
    </span>
  );
}

const RARITY_COLORS = {
  'Consumer Grade':   '#b0c3d9',
  'Industrial Grade': '#5e98d9',
  'Mil-Spec Grade':   '#4b69ff',
  'Restricted':       '#8847ff',
  'Classified':       '#d32ce6',
  'Covert':           '#eb4b4b',
  'Contraband':       '#e4ae39',
  'Extraordinary':    '#e4ae39',
};

function RarityBar({ rarity }) {
  const color = RARITY_COLORS[rarity];
  if (!color) return null;
  return (
    <div className="w-0.5 h-8 rounded-full shrink-0" style={{ backgroundColor: color }} />
  );
}

export default function ItemSearchSelect({ value, onChange, error }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (value && !selectedItem) {
      itemsAPI.getById(value).then(item => {
        setSelectedItem(item);
        setQuery(item.market_hash_name);
      }).catch(() => {});
    }
    if (!value) { setSelectedItem(null); setQuery(''); }
  }, [value]);

  useEffect(() => {
    if (query.length < 2 || selectedItem) { setResults([]); return; }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const items = await itemsAPI.search(query, 20);
        setResults(items);
        setActiveIndex(-1);
      } catch { setResults([]); }
      finally { setLoading(false); }
    }, 250);
    return () => clearTimeout(timer);
  }, [query, selectedItem]);

  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target))
        setIsOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = useCallback((item) => {
    setSelectedItem(item);
    setQuery(item.market_hash_name);
    setIsOpen(false);
    setResults([]);
    onChange(item.id, item);
  }, [onChange]);

  const handleClear = useCallback(() => {
    setSelectedItem(null);
    setQuery('');
    setResults([]);
    setIsOpen(false);
    onChange(null, null);
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [onChange]);

  const handleKeyDown = (e) => {
    if (!isOpen || !results.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIndex(i => Math.min(i + 1, results.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIndex(i => Math.max(i - 1, 0)); }
    else if (e.key === 'Enter' && activeIndex >= 0) { e.preventDefault(); handleSelect(results[activeIndex]); }
    else if (e.key === 'Escape') setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      {/* Input */}
      <div className="relative">
        <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            if (selectedItem && e.target.value !== selectedItem.market_hash_name) {
              setSelectedItem(null);
              onChange(null, null);
            }
          }}
          onFocus={() => results.length && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search items — e.g. AK-47 Redline"
          className={`w-full pl-10 pr-10 py-3 rounded-xl text-sm text-white placeholder-gray-600
            bg-gray-800 border transition-all focus:outline-none
            ${error ? 'border-red-500/50' : 'border-gray-700 focus:border-cyan-500/50'}`}
        />
        <div className="absolute right-3.5 top-1/2 -translate-y-1/2">
          {loading
            ? <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            : selectedItem
              ? <button type="button" onClick={handleClear} className="text-gray-600 hover:text-gray-300 transition-colors">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              : null}
        </div>
      </div>

      {error && <p className="mt-1.5 text-xs text-red-400">{error}</p>}

      {/* Dropdown */}
      {isOpen && (results.length > 0 || (query.length >= 2 && !loading)) && (
        <div className="absolute z-40 w-full mt-1 rounded-xl border border-gray-700/60 shadow-2xl overflow-hidden"
          style={{ background: '#0f1923', maxHeight: 340, overflowY: 'auto' }}>
          {results.length === 0
            ? <div className="px-4 py-8 text-center text-gray-600 text-sm">No items found for "{query}"</div>
            : results.map((item, i) => {
                const price = item.steam_price || item.csfloat_price;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSelect(item)}
                    onMouseEnter={() => setActiveIndex(i)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors
                      border-b border-gray-800/40 last:border-0
                      ${i === activeIndex ? 'bg-gray-800/80' : 'hover:bg-gray-800/40'}`}
                  >
                    <RarityBar rarity={item.rarity} />
                    <div className="w-10 h-10 rounded-lg overflow-hidden shrink-0 flex items-center justify-center"
                      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                      {item.image_url
                        ? <img src={item.image_url} alt="" className="w-full h-full object-contain p-0.5"
                            onError={e => e.target.style.display = 'none'} />
                        : <svg className="w-4 h-4 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                          </svg>
                      }
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm leading-tight truncate">
                        <HighlightedText text={item.market_hash_name} query={query} />
                      </p>
                      {item.rarity && (
                        <p className="text-xs text-gray-600 mt-0.5">{item.rarity}</p>
                      )}
                    </div>
                    {price && (
                      <span className="text-gray-300 text-sm font-mono shrink-0 tabular-nums">
                        {formatCurrency(price)}
                      </span>
                    )}
                  </button>
                );
              })
          }
        </div>
      )}

      {/* Selected item preview */}
      {selectedItem && (
        <div className="mt-2 flex items-center gap-3 px-3 py-2.5 rounded-xl border border-cyan-500/15"
          style={{ background: 'rgba(6,182,212,0.04)' }}>
          <RarityBar rarity={selectedItem.rarity} />
          <div className="w-10 h-10 rounded-lg overflow-hidden shrink-0"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
            {selectedItem.image_url && (
              <img src={selectedItem.image_url} alt="" className="w-full h-full object-contain p-0.5"
                onError={e => e.target.style.display = 'none'} />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium truncate">{selectedItem.market_hash_name}</p>
            <div className="flex items-center gap-3 mt-0.5 flex-wrap">
              {selectedItem.steam_price && <span className="text-cyan-400 text-xs font-mono">Steam {formatCurrency(selectedItem.steam_price)}</span>}
              {selectedItem.csfloat_price && <span className="text-blue-400 text-xs font-mono">CF {formatCurrency(selectedItem.csfloat_price)}</span>}
              {selectedItem.buff_price && <span className="text-orange-400 text-xs font-mono">Buff {formatCurrency(selectedItem.buff_price)}</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
