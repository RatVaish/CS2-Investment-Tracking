import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import Navbar from '../components/Navbar';
import PaywallModal from '../components/PaywallModal';
import { importAPI } from '../api/investments';
import { useAuth } from '../contexts/AuthContext';
import { formatCurrency } from '../utils/currency';

// ─── Field definitions ────────────────────────────────────────────────────────

const FIELDS = [
  { key: 'market_hash_name', label: 'Item Name',      required: true,  hint: 'e.g. AK-47 | Redline (Field-Tested)' },
  { key: 'purchase_price',   label: 'Purchase Price', required: true,  hint: 'e.g. 12.50' },
  { key: 'quantity',         label: 'Quantity',       required: false, hint: 'e.g. 2 (default: 1)' },
  { key: 'purchase_date',    label: 'Purchase Date',  required: false, hint: 'e.g. 2024-01-15' },
  { key: 'notes',            label: 'Notes',          required: false, hint: 'Optional notes' },
  { key: 'tags',             label: 'Tags',           required: false, hint: 'e.g. flip,long-hold' },
  { key: '__ignore__',       label: 'Ignore column',  required: false, hint: '' },
];

// ─── Auto-detect column → field mapping ──────────────────────────────────────

const AUTO_MAP_RULES = [
  { field: 'market_hash_name', patterns: ['market_hash_name','item','name','skin','item name','market name','hash','description'] },
  { field: 'purchase_price',   patterns: ['purchase_price','price','buy price','bought','cost','paid','amount','buy'] },
  { field: 'quantity',         patterns: ['quantity','qty','count','amount','units','num'] },
  { field: 'purchase_date',    patterns: ['purchase_date','date','bought','buy date','date bought','purchased'] },
  { field: 'notes',            patterns: ['notes','note','comment','comments','memo','description'] },
  { field: 'tags',             patterns: ['tags','tag','category','strategy','type','label'] },
];

function autoDetectMapping(headers) {
  const mapping = {};
  headers.forEach(h => {
    const norm = h.toLowerCase().trim();
    for (const rule of AUTO_MAP_RULES) {
      if (rule.patterns.some(p => norm.includes(p) || p.includes(norm))) {
        if (!Object.values(mapping).includes(rule.field)) {
          mapping[h] = rule.field;
          break;
        }
      }
    }
    if (!mapping[h]) mapping[h] = '__ignore__';
  });
  return mapping;
}

// ─── Parse file client-side ───────────────────────────────────────────────────

async function parseFile(file) {
  const name = file.name.toLowerCase();

  if (name.endsWith('.csv') || name.endsWith('.tsv')) {
    return parseDelimited(file, name.endsWith('.tsv') ? '\t' : ',');
  }

  if (name.endsWith('.xlsx') || name.endsWith('.xls') || name.endsWith('.ods')) {
    return parseExcel(file);
  }

  throw new Error('Unsupported file type. Please upload CSV, TSV, XLSX, XLS, or ODS.');
}

function parseDelimited(file, delimiter) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const text = e.target.result;
        const lines = text.split('\n').filter(l => l.trim());
        if (lines.length < 2) throw new Error('File appears empty or has no data rows.');

        const parseRow = line => {
          // Handle quoted fields
          const result = [];
          let current = '';
          let inQuotes = false;
          for (let i = 0; i < line.length; i++) {
            if (line[i] === '"') { inQuotes = !inQuotes; }
            else if (line[i] === delimiter && !inQuotes) { result.push(current.trim()); current = ''; }
            else { current += line[i]; }
          }
          result.push(current.trim());
          return result;
        };

        const headers = parseRow(lines[0]).map(h => h.replace(/^"|"$/g, '').trim());
        const rows = lines.slice(1).map(line => {
          const vals = parseRow(line).map(v => v.replace(/^"|"$/g, '').trim());
          const obj = {};
          headers.forEach((h, i) => { obj[h] = vals[i] || ''; });
          return obj;
        }).filter(row => Object.values(row).some(v => v));

        resolve({ headers, rows });
      } catch (err) { reject(err); }
    };
    reader.onerror = () => reject(new Error('Failed to read file.'));
    reader.readAsText(file, 'UTF-8');
  });
}

async function parseExcel(file) {
  // Dynamically import SheetJS
  const XLSX = await import('https://cdn.jsdelivr.net/npm/xlsx@0.18.5/+esm');
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: 'array', dateNF: 'yyyy-mm-dd' });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const raw = XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, dateNF: 'yyyy-mm-dd' });

  if (raw.length < 2) throw new Error('Spreadsheet appears empty or has no data rows.');

  const headers = (raw[0] || []).map(h => String(h).trim());
  const rows = raw.slice(1)
    .filter(row => row.some(v => v !== '' && v !== null && v !== undefined))
    .map(row => {
      const obj = {};
      headers.forEach((h, i) => { obj[h] = String(row[i] ?? '').trim(); });
      return obj;
    });

  return { headers, rows };
}

// ─── Validate mapped rows ─────────────────────────────────────────────────────

function validateRows(rows, mapping) {
  return rows.map((raw, i) => {
    const mapped = {};
    Object.entries(mapping).forEach(([col, field]) => {
      if (field !== '__ignore__') mapped[field] = raw[col] || '';
    });

    const errors = [];
    if (!mapped.market_hash_name?.trim()) errors.push('Missing item name');
    const price = parseFloat(mapped.purchase_price);
    if (isNaN(price) || price <= 0) errors.push('Invalid price');
    const qty = parseInt(mapped.quantity || '1');
    if (isNaN(qty) || qty < 1) errors.push('Invalid quantity');

    return { ...mapped, quantity: mapped.quantity || '1', _row: i + 2, _errors: errors, _valid: errors.length === 0 };
  });
}

// ─── Step components ──────────────────────────────────────────────────────────

function UploadStep({ onParsed }) {
  const [dragging, setDragging] = useState(false);
  const [parsing, setParsing] = useState(false);
  const inputRef = useRef();

  const handle = async file => {
    if (!file) return;
    setParsing(true);
    try {
      const result = await parseFile(file);
      onParsed(result, file.name);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setParsing(false);
    }
  };

  const onDrop = e => {
    e.preventDefault();
    setDragging(false);
    handle(e.dataTransfer.files[0]);
  };

  return (
    <div className="space-y-6">
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current.click()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
          dragging ? 'border-cyan-500 bg-cyan-500/5' : 'border-gray-700 hover:border-gray-600 hover:bg-gray-800/30'
        }`}
      >
        <input ref={inputRef} type="file"
          accept=".csv,.tsv,.xlsx,.xls,.ods"
          className="hidden"
          onChange={e => handle(e.target.files[0])} />

        {parsing ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-400 text-sm">Parsing file...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gray-800 border border-gray-700 flex items-center justify-center">
              <svg className="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <p className="text-white font-medium">Drop your spreadsheet here</p>
              <p className="text-gray-500 text-sm mt-1">or click to browse</p>
            </div>
            <div className="flex gap-2 flex-wrap justify-center">
              {['CSV', 'TSV', 'XLSX', 'XLS', 'ODS'].map(fmt => (
                <span key={fmt} className="px-2 py-0.5 rounded text-[10px] font-medium bg-gray-800 text-gray-500 border border-gray-700">{fmt}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2">Tips</p>
        <ul className="space-y-1 text-xs text-gray-600">
          <li>• Any column order works — you'll map them in the next step</li>
          <li>• Supported date formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY</li>
          <li>• Quantity defaults to 1 if not mapped</li>
          <li>• Tags column: comma-separated values (e.g. <span className="text-gray-500">flip,long-hold</span>)</li>
          <li>• Maximum 500 rows per import</li>
        </ul>
      </div>
    </div>
  );
}

function MapStep({ headers, rows, fileName, onMapped, onBack }) {
  const [mapping, setMapping] = useState(() => autoDetectMapping(headers));
  const autoDetected = autoDetectMapping(headers);

  const preview = rows.slice(0, 3);
  const validated = validateRows(rows, mapping);
  const validCount = validated.filter(r => r._valid).length;

  const setField = (col, field) => setMapping(prev => ({ ...prev, [col]: field }));

  const requiredMapped = FIELDS.filter(f => f.required).every(f =>
    Object.values(mapping).includes(f.key)
  );

  return (
    <div className="space-y-5">
      {/* File info */}
      <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-xl">
        <svg className="w-5 h-5 text-cyan-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <div className="flex-1 min-w-0">
          <p className="text-white text-sm font-medium truncate">{fileName}</p>
          <p className="text-gray-500 text-xs">{rows.length} rows · {headers.length} columns</p>
        </div>
        <button onClick={onBack} className="text-xs text-gray-600 hover:text-gray-400 transition-colors">Change file</button>
      </div>

      {/* Column mapper */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h3 className="text-white font-medium text-sm">Map Columns</h3>
            <p className="text-gray-500 text-xs mt-0.5">Tell us what each column in your file represents</p>
          </div>
          <button
            onClick={() => setMapping(autoDetectMapping(headers))}
            className="text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-all border border-gray-700"
          >
            ✦ Auto-detect
          </button>
        </div>

        <div className="divide-y divide-gray-800/50">
          {headers.map(col => {
            const wasAutoDetected = autoDetected[col] !== '__ignore__' && autoDetected[col] === mapping[col];
            const sampleVals = preview.map(r => r[col]).filter(Boolean);
            return (
              <div key={col} className="px-5 py-3 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-gray-300 text-sm font-medium truncate">{col}</p>
                  <p className="text-gray-700 text-xs truncate mt-0.5">
                    {sampleVals.slice(0, 2).join(' · ') || '—'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {wasAutoDetected && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-500 border border-cyan-500/20">auto</span>
                  )}
                  <select
                    value={mapping[col] || '__ignore__'}
                    onChange={e => setField(col, e.target.value)}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-cyan-500/50 transition-colors"
                  >
                    {FIELDS.map(f => (
                      <option key={f.key} value={f.key}>{f.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Validation summary */}
      <div className={`rounded-xl p-4 border text-sm flex items-center gap-3 ${
        !requiredMapped
          ? 'border-amber-500/20 bg-amber-500/5'
          : validCount === rows.length
            ? 'border-emerald-500/20 bg-emerald-500/5'
            : 'border-amber-500/20 bg-amber-500/5'
      }`}>
        <div className={`w-2 h-2 rounded-full shrink-0 ${
          !requiredMapped ? 'bg-amber-500' : validCount === rows.length ? 'bg-emerald-500' : 'bg-amber-500'
        }`} />
        {!requiredMapped ? (
          <p className="text-amber-400">Map <strong>Item Name</strong> and <strong>Purchase Price</strong> to continue</p>
        ) : (
          <p className={validCount === rows.length ? 'text-emerald-400' : 'text-amber-400'}>
            <strong>{validCount}</strong> of <strong>{rows.length}</strong> rows valid
            {validCount < rows.length && ` · ${rows.length - validCount} will be skipped`}
          </p>
        )}
      </div>

      <button
        disabled={!requiredMapped || validCount === 0}
        onClick={() => onMapped(validateRows(rows, mapping))}
        className="w-full py-3 rounded-xl font-semibold text-sm transition-all
          bg-gradient-to-r from-cyan-500 to-blue-600
          hover:from-cyan-400 hover:to-blue-500
          disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed
          text-white"
      >
        Preview {validCount} rows →
      </button>
    </div>
  );
}

function PreviewStep({ rows, onImport, onBack, importing }) {
  const valid = rows.filter(r => r._valid);
  const invalid = rows.filter(r => !r._valid);

  return (
    <div className="space-y-5">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold font-mono text-white">{rows.length}</p>
          <p className="text-xs text-gray-500 mt-1">Total rows</p>
        </div>
        <div className="bg-gray-900 border border-emerald-500/20 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold font-mono text-emerald-400">{valid.length}</p>
          <p className="text-xs text-gray-500 mt-1">Will import</p>
        </div>
        <div className={`bg-gray-900 border rounded-xl p-4 text-center ${invalid.length ? 'border-amber-500/20' : 'border-gray-800'}`}>
          <p className={`text-2xl font-bold font-mono ${invalid.length ? 'text-amber-400' : 'text-gray-600'}`}>{invalid.length}</p>
          <p className="text-xs text-gray-500 mt-1">Will skip</p>
        </div>
      </div>

      {/* Valid rows preview */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800">
          <h3 className="text-white text-sm font-medium">Rows to import</h3>
        </div>
        <div className="max-h-64 overflow-y-auto">
          {valid.slice(0, 50).map((row, i) => (
            <div key={i} className="px-5 py-3 border-b border-gray-800/50 last:border-0 flex items-center gap-3">
              <span className="text-gray-700 text-xs font-mono w-8 shrink-0">#{row._row}</span>
              <div className="flex-1 min-w-0">
                <p className="text-gray-300 text-sm truncate">{row.market_hash_name}</p>
                <p className="text-gray-600 text-xs mt-0.5 font-mono">
                  {formatCurrency(parseFloat(row.purchase_price))}
                  {parseInt(row.quantity) > 1 && ` × ${row.quantity}`}
                  {row.purchase_date && ` · ${row.purchase_date}`}
                  {row.tags && ` · ${row.tags}`}
                </p>
              </div>
            </div>
          ))}
          {valid.length > 50 && (
            <div className="px-5 py-3 text-center text-gray-600 text-xs">
              +{valid.length - 50} more rows
            </div>
          )}
        </div>
      </div>

      {/* Invalid rows */}
      {invalid.length > 0 && (
        <div className="bg-gray-900 border border-amber-500/20 rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-amber-500/10">
            <h3 className="text-amber-400 text-sm font-medium">Rows that will be skipped</h3>
          </div>
          <div className="max-h-40 overflow-y-auto">
            {invalid.map((row, i) => (
              <div key={i} className="px-5 py-2.5 border-b border-gray-800/30 last:border-0 flex items-center gap-3">
                <span className="text-gray-700 text-xs font-mono w-8 shrink-0">#{row._row}</span>
                <p className="text-gray-500 text-xs flex-1 truncate">{row.market_hash_name || '—'}</p>
                <p className="text-amber-600 text-xs shrink-0">{row._errors.join(', ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button onClick={onBack}
          className="px-5 py-3 rounded-xl text-sm text-gray-400 hover:text-white border border-gray-700 hover:border-gray-600 transition-all">
          ← Back
        </button>
        <button
          onClick={() => onImport(valid)}
          disabled={importing || valid.length === 0}
          className="flex-1 py-3 rounded-xl font-semibold text-sm transition-all
            bg-gradient-to-r from-cyan-500 to-blue-600
            hover:from-cyan-400 hover:to-blue-500
            disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed
            text-white"
        >
          {importing ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
              Importing...
            </span>
          ) : `Import ${valid.length} investment${valid.length !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
}

function ResultStep({ result, onDone }) {
  return (
    <div className="space-y-5 text-center py-6">
      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto border ${
        result.imported > 0 ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-amber-500/10 border-amber-500/30'
      }`}>
        {result.imported > 0 ? (
          <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M12 3a9 9 0 100 18A9 9 0 0012 3z" />
          </svg>
        )}
      </div>

      <div>
        <p className="text-white font-semibold text-lg">
          {result.imported > 0 ? `${result.imported} investment${result.imported !== 1 ? 's' : ''} imported` : 'Nothing imported'}
        </p>
        {result.errors?.length > 0 && (
          <p className="text-gray-500 text-sm mt-1">{result.errors.length} rows skipped (not found in Floatbase database)</p>
        )}
      </div>

      {result.errors?.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-left max-h-48 overflow-y-auto">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2">Skipped items</p>
          {result.errors.map((e, i) => (
            <div key={i} className="flex items-start gap-2 py-1.5 border-b border-gray-800/50 last:border-0">
              <span className="text-gray-700 text-xs font-mono w-8 shrink-0">#{e.row}</span>
              <p className="text-gray-500 text-xs flex-1 truncate">{e.name || '—'}</p>
              <p className="text-amber-600 text-xs shrink-0">{e.error}</p>
            </div>
          ))}
        </div>
      )}

      <button onClick={onDone}
        className="w-full py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white transition-all">
        Go to Portfolio
      </button>
    </div>
  );
}

// ─── Main Import page ─────────────────────────────────────────────────────────

export default function Import() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isPro = user?.tier === 'pro';
  const [showPaywall, setShowPaywall] = useState(false);

  const [step, setStep] = useState('upload'); // upload | map | preview | result
  const [parsedData, setParsedData] = useState(null);
  const [fileName, setFileName] = useState('');
  const [mappedRows, setMappedRows] = useState([]);
  const [result, setResult] = useState(null);
  const [importing, setImporting] = useState(false);

  const handleParsed = useCallback((data, name) => {
    if (!isPro) { setShowPaywall(true); return; }
    setParsedData(data);
    setFileName(name);
    setStep('map');
  }, [isPro]);

  const handleMapped = useCallback((rows) => {
    setMappedRows(rows);
    setStep('preview');
  }, []);

  const handleImport = useCallback(async (validRows) => {
    setImporting(true);
    try {
      const payload = validRows.map(row => ({
        market_hash_name: row.market_hash_name,
        purchase_price: parseFloat(row.purchase_price),
        quantity: parseInt(row.quantity || '1'),
        purchase_date: row.purchase_date || null,
        notes: row.notes || null,
        tags: row.tags ? row.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
      }));

      const res = await fetch(`${import.meta.env.VITE_API_URL}/import/spreadsheet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ rows: payload }),
      }).then(r => r.json());

      if (res.detail) throw new Error(res.detail);
      setResult(res);
      setStep('result');
      if (res.imported > 0) toast.success(`${res.imported} investments imported`);
    } catch (err) {
      toast.error(err.message || 'Import failed');
    } finally {
      setImporting(false);
    }
  }, []);

  const STEPS = [
    { key: 'upload',  label: 'Upload' },
    { key: 'map',     label: 'Map columns' },
    { key: 'preview', label: 'Preview' },
    { key: 'result',  label: 'Done' },
  ];
  const stepIdx = STEPS.findIndex(s => s.key === step);

  return (
    <div className="min-h-screen bg-gray-950">
      {showPaywall && <PaywallModal onClose={() => setShowPaywall(false)} />}
      <Navbar />

      <main className="max-w-2xl mx-auto px-6 pt-28 pb-16">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Import Spreadsheet</h1>
          <p className="text-gray-500 text-sm mt-1">
            Import investments from CSV, Excel, or any spreadsheet format
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((s, i) => (
            <React.Fragment key={s.key}>
              <div className={`flex items-center gap-2 ${i <= stepIdx ? 'text-cyan-400' : 'text-gray-700'}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border transition-all ${
                  i < stepIdx ? 'bg-cyan-500 border-cyan-500 text-white'
                  : i === stepIdx ? 'border-cyan-500 text-cyan-400'
                  : 'border-gray-700 text-gray-700'
                }`}>
                  {i < stepIdx ? '✓' : i + 1}
                </div>
                <span className="text-xs font-medium hidden sm:block">{s.label}</span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`flex-1 h-px ${i < stepIdx ? 'bg-cyan-500/30' : 'bg-gray-800'}`} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Step content */}
        {step === 'upload' && <UploadStep onParsed={handleParsed} />}
        {step === 'map' && parsedData && (
          <MapStep
            headers={parsedData.headers}
            rows={parsedData.rows}
            fileName={fileName}
            onMapped={handleMapped}
            onBack={() => setStep('upload')}
          />
        )}
        {step === 'preview' && (
          <PreviewStep
            rows={mappedRows}
            onImport={handleImport}
            onBack={() => setStep('map')}
            importing={importing}
          />
        )}
        {step === 'result' && result && (
          <ResultStep result={result} onDone={() => navigate('/app/portfolio')} />
        )}


      </main>
    </div>
  );
}
