import { formatBRL, formatNumber, formatAbbreviated } from '../src/utils/formatters.js';
import { calculateAISimulation } from '../src/utils/aiEngine.js';

// Test formatBRL
console.assert(formatBRL(2850.64).includes('2.850,64'), 'formatBRL failed for 2850.64');
console.assert(formatBRL(0).includes('0,00'), 'formatBRL failed for 0');
console.assert(formatBRL(null) === 'R$ 0,00', 'formatBRL failed for null');
console.assert(formatBRL(undefined) === 'R$ 0,00', 'formatBRL failed for undefined');

// Test formatNumber
console.assert(formatNumber(87830899).includes('87.830.899'), 'formatNumber failed for 87830899');
console.assert(formatNumber(0) === '0', 'formatNumber failed for 0');
console.assert(formatNumber(null) === '0', 'formatNumber failed for null');
console.assert(formatNumber(undefined) === '0', 'formatNumber failed for undefined');

// Test formatAbbreviated
console.assert(formatAbbreviated(250000000000) === '250 Bi', 'formatAbbreviated failed for 250 Bi');
console.assert(formatAbbreviated(2500000000) === '2,5 Bi', 'formatAbbreviated failed for 2,5 Bi');
console.assert(formatAbbreviated(2500000) === '2,5 Mi', 'formatAbbreviated failed for 2,5 Mi');
console.assert(formatAbbreviated(2850) === '3 Mil', 'formatAbbreviated failed for 2850');
console.assert(formatAbbreviated(500) === '500', 'formatAbbreviated failed for 500');
console.assert(formatAbbreviated(0) === '0', 'formatAbbreviated failed for 0');

// Test calculateAISimulation
const sampleItems = [{
  id: '1',
  name: 'Software Developer',
  total_workers: 1000,
  avg_income: 5000,
  wage_bill: 5000000,
  ai_exposure_score: 0.8
}];

// Automation mode
const simAuto = calculateAISimulation(sampleItems, 50, 'automation');
console.assert(simAuto[0].adjustedExposure === 0.4, 'AI engine adjustedExposure failed');
console.assert(simAuto[0].deltaWorkers === 160, 'AI engine deltaWorkers failed'); // 1000 * 0.4 * 0.4 = 160
console.assert(simAuto[0].simWorkers === 840, 'AI engine simWorkers failed'); // 1000 - 160 = 840
console.assert(simAuto[0].simWageBill === 4200000, 'AI engine simWageBill failed'); // 840 * 5000 = 4200000
console.assert(simAuto[0].deltaWageBill === -800000, 'AI engine deltaWageBill failed');

// Productivity mode
const simProd = calculateAISimulation(sampleItems, 50, 'productivity');
console.assert(simProd[0].simWorkers === 1000, 'AI engine productivity simWorkers failed');
console.assert(Math.round(simProd[0].deltaIncome) === 700, 'AI engine deltaIncome failed'); // 5000 * (0.4 * 0.35) = 700
console.assert(Math.round(simProd[0].simIncome) === 5700, 'AI engine simIncome failed'); // 5000 + 700 = 5700
console.assert(simProd[0].simWageBill === 5700000, 'AI engine productivity simWageBill failed');
console.assert(simProd[0].deltaWageBill === 700000, 'AI engine productivity deltaWageBill failed');

// Zero penetration mode
const simZero = calculateAISimulation(sampleItems, 0, 'automation');
console.assert(simZero[0].simWorkers === 1000, 'AI engine zero penetration simWorkers failed');
console.assert(simZero[0].deltaWorkers === 0, 'AI engine zero penetration deltaWorkers failed');
console.assert(simZero[0].deltaWageBill === 0, 'AI engine zero penetration deltaWageBill failed');

console.log('Utils tests passed!');
