import React from 'react';
import { X, Users, DollarSign, Cpu, PieChart } from 'lucide-react';
import { formatBRL, formatNumber, formatAbbreviated } from '../utils/formatters';

export default function DetailModal({ item, onClose, totals }) {
  if (!item) return null;

  const exposure = item.adjustedExposure !== undefined ? item.adjustedExposure : item.ai_exposure_score;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 p-2 text-slate-400 hover:text-white rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        <h2 className="text-xl font-bold text-white mb-1 pr-8">{item.name}</h2>
        <p className="text-xs text-emerald-400 font-medium mb-6">{item.section}</p>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
              <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                <Users className="w-3.5 h-3.5 text-blue-400" />
                <span>Trabalhadores</span>
              </div>
              <p className="text-lg font-bold text-white">{formatNumber(item.simWorkers || item.total_workers)}</p>
              <span className="text-[10px] text-slate-500">{item.share_of_workforce}% do Brasil</span>
            </div>

            <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3">
              <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                <span>Rendimento Médio</span>
              </div>
              <p className="text-lg font-bold text-white">{formatBRL(item.simIncome || item.avg_income)}</p>
              <span className="text-[10px] text-slate-500">Média Brasil: {formatBRL(totals?.avg_income)}</span>
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-slate-400 text-xs">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                <span>Índice de Exposição à IA</span>
              </div>
              <span className="text-sm font-bold text-amber-400">
                {Math.round(exposure * 100)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-amber-500 to-red-500 h-full transition-all duration-300"
                style={{ width: `${Math.round(exposure * 100)}%` }}
              ></div>
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400 text-xs">
              <PieChart className="w-3.5 h-3.5 text-purple-400" />
              <span>Massa Salarial Mensal</span>
            </div>
            <span className="text-base font-bold text-white">
              R$ {formatAbbreviated(item.simWageBill || item.wage_bill)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
