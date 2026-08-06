export function calculateAISimulation(items, penetrationPct = 0, mode = 'automation') {
  const penetrationFactor = penetrationPct / 100;
  
  return items.map((item) => {
    const adjustedExposure = item.ai_exposure_score * penetrationFactor;
    
    let simWorkers = item.total_workers;
    let simIncome = item.avg_income;
    let deltaWorkers = 0;
    let deltaIncome = 0;
    
    if (mode === 'automation') {
      // Automation scenario: workforce reduction / displacement
      deltaWorkers = Math.round(item.total_workers * adjustedExposure * 0.4);
      simWorkers = Math.max(1, item.total_workers - deltaWorkers);
    } else {
      // Productivity scenario: income/productivity enhancement
      deltaIncome = item.avg_income * (adjustedExposure * 0.35);
      simIncome = item.avg_income + deltaIncome;
    }
    
    const simWageBill = Math.round(simWorkers * simIncome);
    const origWageBill = item.wage_bill || (item.total_workers * item.avg_income);
    const deltaWageBill = simWageBill - origWageBill;
    
    return {
      ...item,
      simWorkers,
      simIncome,
      simWageBill,
      deltaWorkers,
      deltaIncome,
      deltaWageBill,
      adjustedExposure
    };
  });
}
