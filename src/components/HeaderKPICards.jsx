import React from 'react';
import { Users, DollarSign, TrendingUp, Cpu } from 'lucide-react';
import { formatBRL, formatNumber, formatAbbreviated } from '../utils/formatters';

export default function HeaderKPICards({ totals, simActive, penetrationPct }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center gap-4 shadow-lg backdrop-blur">
        <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
          <Users className="w-6 h-6" />
        </div>
        <div>
          <p className="text-xs text-slate-400 font-medium">Força de Trabalho Total</p>
          <h3 className="text-xl font-bold text-white">{formatNumber(totals.total_workers)}</h3>
          <p className="text-[11px] text-slate-500">Pessoas Ocupadas (2022)</p>
        </div>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center gap-4 shadow-lg backdrop-blur">
        <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
          <DollarSign className="w-6 h-6" />
        </div>
        <div>
          <p className="text-xs text-slate-400 font-medium">Rendimento Médio Mensal</p>
          <h3 className="text-xl font-bold text-white">{formatBRL(totals.avg_income)}</h3>
          <p className="text-[11px] text-slate-500">Média Nacional por Ocupação</p>
        </div>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center gap-4 shadow-lg backdrop-blur">
        <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
          <TrendingUp className="w-6 h-6" />
        </div>
        <div>
          <p className="text-xs text-slate-400 font-medium">Massa Salarial Total</p>
          <h3 className="text-xl font-bold text-white">R$ {formatAbbreviated(totals.total_wage_bill)}</h3>
          <p className="text-[11px] text-slate-500">Volume Econômico Mensal</p>
        </div>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center gap-4 shadow-lg backdrop-blur border-amber-500/20">
        <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg">
          <Cpu className="w-6 h-6" />
        </div>
        <div>
          <p className="text-xs text-slate-400 font-medium">Simulador de IA</p>
          <h3 className="text-xl font-bold text-amber-400">{penetrationPct}% Penetração</h3>
          <p className="text-[11px] text-slate-500">{simActive ? 'Simulação Ativa' : 'Ajuste no Painel'}</p>
        </div>
      </div>
    </div>
  );
}
