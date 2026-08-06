import React from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';

export default function SearchFilterBar({
  searchQuery,
  setSearchQuery,
  selectedSection,
  setSelectedSection,
  sections,
  minIncome,
  setMinIncome,
  onReset
}) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 mb-6 backdrop-blur flex flex-wrap gap-4 items-center justify-between">
      <div className="flex-1 min-w-[260px] relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Pesquisar por profissão ou atividade (ex: Soja, TI, Educação)..."
          className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-sm text-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">Todas as Seções CNAE</option>
            {sections.map((sec) => (
              <option key={sec} value={sec}>
                {sec.length > 40 ? sec.slice(0, 40) + '...' : sec}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onReset}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-2 rounded-lg transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Limpar Filtros
        </button>
      </div>
    </div>
  );
}
