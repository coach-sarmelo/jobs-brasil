import React from 'react';
import { Cpu, Sliders, AlertTriangle } from 'lucide-react';
import { formatBRL, formatNumber } from '../utils/formatters';

export default function AISimulatorDrawer({
  penetrationPct,
  setPenetrationPct,
  simMode,
  setSimMode,
  items
}) {
  const sortedImpacted = [...items]
    .sort((a, b) => (b.adjustedExposure || 0) - (a.adjustedExposure || 0))
    .slice(0, 5);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-xl mb-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-bold text-white">Simulador de Disrupção por IA</h2>
        </div>
        <span className="text-xs text-slate-400">Modelo de Exposição de Tarefas</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="text-xs text-slate-300 font-medium block mb-2">
            Taxa de Penetração da IA na Economia: <span className="text-amber-400 font-bold">{penetrationPct}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={penetrationPct}
            onChange={(e) => setPenetrationPct(Number(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
          />

          <div className="mt-4">
            <label className="text-xs text-slate-300 font-medium block mb-2">Cenário de Impacto:</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setSimMode('automation')}
                className={`py-2 px-3 text-xs font-semibold rounded-lg border transition-all ${
                  simMode === 'automation'
                    ? 'bg-red-500/20 border-red-500 text-red-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                Automação (Substituição)
              </button>
              <button
                onClick={() => setSimMode('productivity')}
                className={`py-2 px-3 text-xs font-semibold rounded-lg border transition-all ${
                  simMode === 'productivity'
                    ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                Produtividade (Complementar)
              </button>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-slate-300 mb-3 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Top 5 Setores Mais Expostos
          </h3>
          <div className="space-y-2">
            {sortedImpacted.map((item) => (
              <div key={item.id} className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-2.5 flex items-center justify-between text-xs">
                <div className="truncate max-w-[200px]">
                  <p className="font-semibold text-white truncate">{item.name}</p>
                  <p className="text-[10px] text-slate-400 truncate">{item.section}</p>
                </div>
                <div className="text-right">
                  <span className="font-bold text-amber-400">
                    {Math.round((item.adjustedExposure || item.ai_exposure_score) * 100)}% Exp.
                  </span>
                  <p className="text-[10px] text-slate-400">
                    {simMode === 'automation'
                      ? `-${formatNumber(item.deltaWorkers || 0)} vagas`
                      : `+${formatBRL(item.deltaIncome || 0)}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
