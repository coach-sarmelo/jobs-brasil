import React, { useState, useMemo } from 'react';
import jobsData from './data/jobs_br.json';
import HeaderKPICards from './components/HeaderKPICards';
import SearchFilterBar from './components/SearchFilterBar';
import ScatterPlot from './components/ScatterPlot';
import AISimulatorDrawer from './components/AISimulatorDrawer';
import DetailModal from './components/DetailModal';
import { calculateAISimulation } from './utils/aiEngine';
import { Briefcase } from 'lucide-react';

export default function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSection, setSelectedSection] = useState('ALL');
  const [minIncome, setMinIncome] = useState(0);
  const [penetrationPct, setPenetrationPct] = useState(0);
  const [simMode, setSimMode] = useState('automation');
  const [selectedItem, setSelectedItem] = useState(null);

  // Compute AI Simulation
  const simulatedItems = useMemo(() => {
    return calculateAISimulation(jobsData.items, penetrationPct, simMode);
  }, [penetrationPct, simMode]);

  // Apply Search and Section Filters
  const filteredItems = useMemo(() => {
    return simulatedItems.filter((item) => {
      const matchesSearch = !searchQuery || item.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesSection = selectedSection === 'ALL' || item.section === selectedSection;
      const matchesIncome = item.avg_income >= minIncome;
      return matchesSearch && matchesSection && matchesIncome;
    });
  }, [simulatedItems, searchQuery, selectedSection, minIncome]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedSection('ALL');
    setMinIncome(0);
    setPenetrationPct(0);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 max-w-7xl mx-auto">
      {/* Header Title */}
      <header className="mb-8 flex flex-wrap justify-between items-center border-b border-slate-800 pb-6 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
              <Briefcase className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">Jobs BR</h1>
              <p className="text-xs md:text-sm text-slate-400">
                Panorama do Mercado de Trabalho Brasileiro & Simulador de Impacto de IA (PNAD/IBGE 2022)
              </p>
            </div>
          </div>
        </div>

        <a
          href="https://github.com/karpathy/jobs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white px-3 py-2 rounded-lg transition-colors"
        >
          Inspirado em Karpathy/jobs ↗
        </a>
      </header>

      {/* KPI Cards */}
      <HeaderKPICards
        totals={jobsData.totals}
        simActive={penetrationPct > 0}
        penetrationPct={penetrationPct}
      />

      {/* Search & Filter Bar */}
      <SearchFilterBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        selectedSection={selectedSection}
        setSelectedSection={setSelectedSection}
        sections={jobsData.sections}
        minIncome={minIncome}
        setMinIncome={setMinIncome}
        onReset={handleResetFilters}
      />

      {/* AI Simulator Engine */}
      <AISimulatorDrawer
        penetrationPct={penetrationPct}
        setPenetrationPct={setPenetrationPct}
        simMode={simMode}
        setSimMode={setSimMode}
        items={filteredItems}
      />

      {/* Main D3 ScatterPlot */}
      <ScatterPlot
        items={filteredItems}
        onSelectItem={setSelectedItem}
        searchQuery={searchQuery}
      />

      {/* Detail Modal */}
      {selectedItem && (
        <DetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          totals={jobsData.totals}
        />
      )}
    </div>
  );
}

