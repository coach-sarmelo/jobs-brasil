export function formatBRL(value) {
  if (value === undefined || value === null) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(num) {
  if (num === undefined || num === null) return '0';
  return new Intl.NumberFormat('pt-BR').format(num);
}

export function formatAbbreviated(num) {
  if (!num) return '0';
  if (num >= 1e9) {
    const val = (num / 1e9).toFixed(1).replace('.', ',');
    return val.endsWith(',0') ? val.slice(0, -2) + ' Bi' : val + ' Bi';
  }
  if (num >= 1e6) {
    const val = (num / 1e6).toFixed(1).replace('.', ',');
    return val.endsWith(',0') ? val.slice(0, -2) + ' Mi' : val + ' Mi';
  }
  if (num >= 1e3) {
    return (num / 1e3).toFixed(0) + ' Mil';
  }
  return num.toString();
}
