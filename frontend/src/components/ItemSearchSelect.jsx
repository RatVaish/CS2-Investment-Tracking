import React, { useState, useEffect, useRef } from 'react';
import { itemsAPI } from '../api/items';

function ItemSearchSelect({ value, onChange, error }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const dropdownRef = useRef(null);

  // Load selected item details if value exists
  useEffect(() => {
    if (value && !selectedItem) {
      itemsAPI.getById(value).then(item => {
        setSelectedItem(item);
        setQuery(item.market_hash_name);
      }).catch(err => {
        console.error('Failed to load item:', err);
      });
    }
  }, [value, selectedItem]);

  // Search items when query changes
  useEffect(() => {
    const searchItems = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        const items = await itemsAPI.search(query, 20);
        setResults(items);
      } catch (err) {
        console.error('Search failed:', err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(searchItems, 300);
    return () => clearTimeout(debounce);
  }, [query]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (item) => {
    setSelectedItem(item);
    setQuery(item.market_hash_name);
    setIsOpen(false);
    onChange(item.id);
  };

  const handleClear = () => {
    setSelectedItem(null);
    setQuery('');
    setResults([]);
    onChange(null);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-sm font-medium text-gray-300 mb-2">
        Item <span className="text-red-400">*</span>
      </label>

      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            if (!e.target.value) handleClear();
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="Search for CS2 items..."
          className={`w-full px-4 py-3 pr-10 bg-gray-800 border ${
            error ? 'border-red-500' : 'border-gray-700'
          } rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors`}
        />

        {/* Clear button */}
        {selectedItem && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}

        {/* Loading spinner */}
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin h-5 w-5 border-2 border-cyan-500 border-t-transparent rounded-full"></div>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-1 text-sm text-red-400">{error}</p>
      )}

      {/* Dropdown results */}
      {isOpen && results.length > 0 && (
        <div className="absolute z-10 w-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-80 overflow-y-auto">
          {results.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelect(item)}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-700 transition-colors text-left"
            >
              {/* Item image */}
              <img
                src={item.image_url || `https://via.placeholder.com/60/1f2937/ffffff?text=CS2`}
                alt={item.market_hash_name}
                className="w-12 h-12 object-contain bg-gray-900 rounded border border-gray-700"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/60/1f2937/ffffff?text=CS2';
                }}
              />

              {/* Item details */}
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{item.market_hash_name}</p>
                {item.csfloat_price && (
                  <p className="text-cyan-400 text-sm">£{item.csfloat_price.toFixed(2)}</p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results message */}
      {isOpen && query.length >= 2 && !loading && results.length === 0 && (
        <div className="absolute z-10 w-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-4 text-center text-gray-400">
          No items found
        </div>
      )}

      {/* Selected item preview */}
      {selectedItem && (
        <div className="mt-2 p-3 bg-gray-800 border border-gray-700 rounded-lg flex items-center gap-3">
          <img
            src={selectedItem.image_url || `https://via.placeholder.com/48/1f2937/ffffff?text=CS2`}
            alt={selectedItem.market_hash_name}
            className="w-10 h-10 object-contain bg-gray-900 rounded"
            onError={(e) => {
              e.target.src = 'https://via.placeholder.com/48/1f2937/ffffff?text=CS2';
            }}
          />
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium truncate">{selectedItem.market_hash_name}</p>
            {selectedItem.csfloat_price && (
              <p className="text-cyan-400 text-xs">Current: £{selectedItem.csfloat_price.toFixed(2)}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ItemSearchSelect;