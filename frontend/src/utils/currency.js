import { getCookie, setCookie } from '../api/client';

const FALLBACK_RATES = {
  USD: 1, GBP: 0.79, EUR: 0.92, CNY: 7.24, AUD: 1.53, CAD: 1.36,
};

const CURRENCY_SYMBOLS = {
  USD: '$', GBP: '£', EUR: '€', CNY: '¥', AUD: 'A$', CAD: 'C$',
};

export const getUserCurrency = () => getCookie('currency') || 'USD';
export const getUserTimezone = () => getCookie('timezone') || 'UTC';
export const setUserCurrency = (currency) => setCookie('currency', currency);

export const convertFromUSD = (usdAmount, targetCurrency = null) => {
  const currency = targetCurrency || getUserCurrency();
  const rate = FALLBACK_RATES[currency] || 1;
  return usdAmount * rate;
};

export const formatCurrency = (usdAmount, targetCurrency = null, compact = false) => {
  if (usdAmount === null || usdAmount === undefined) return '—';
  const currency = targetCurrency || getUserCurrency();
  const converted = convertFromUSD(usdAmount, currency);
  const symbol = CURRENCY_SYMBOLS[currency] || '$';
  if (compact && Math.abs(converted) >= 1000) {
    return `${symbol}${(converted / 1000).toFixed(1)}k`;
  }
  return `${symbol}${converted.toFixed(2)}`;
};

export const formatCNY = (cnyAmount) => {
  if (cnyAmount === null || cnyAmount === undefined) return '—';
  return `¥${cnyAmount.toFixed(2)}`;
};

export const getCurrencySymbol = (currency = null) => {
  return CURRENCY_SYMBOLS[currency || getUserCurrency()] || '$';
};

export const SUPPORTED_CURRENCIES = Object.keys(FALLBACK_RATES);
