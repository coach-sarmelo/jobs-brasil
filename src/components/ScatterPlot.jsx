import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { formatBRL, formatNumber } from '../utils/formatters';

const SECTION_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#d946ef', '#64748b'
];

export default function ScatterPlot({ items, onSelectItem, searchQuery }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || !items || !items.length) return;

    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = 550;
    const margin = { top: 30, right: 30, bottom: 60, left: 80 };

    d3.select(svgRef.current).selectAll('*').remove();
    d3.select(container).selectAll('.scatter-tooltip').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Color Scale by Section
    const sections = Array.from(new Set(items.map(d => d.section)));
    const colorScale = d3.scaleOrdinal()
      .domain(sections)
      .range(SECTION_COLORS);

    // Log Scales
    const maxWorkers = d3.max(items, d => d.simWorkers || d.total_workers) || 10000;
    const maxIncome = d3.max(items, d => d.simIncome || d.avg_income) || 5000;
    const maxWageBill = d3.max(items, d => d.simWageBill || d.wage_bill) || 1000000;

    const xScale = d3.scaleLog()
      .domain([1000, maxWorkers * 1.2])
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLog()
      .domain([500, maxIncome * 1.3])
      .range([height - margin.bottom, margin.top]);

    const rScale = d3.scaleSqrt()
      .domain([0, maxWageBill])
      .range([4, 30]);

    // Clip path for zoom
    svg.append('defs').append('clipPath')
      .attr('id', 'scatter-clip')
      .append('rect')
      .attr('x', margin.left)
      .attr('y', margin.top)
      .attr('width', Math.max(0, width - margin.left - margin.right))
      .attr('height', Math.max(0, height - margin.top - margin.bottom));

    // Axes
    const xAxis = d3.axisBottom(xScale)
      .ticks(5, '~s')
      .tickFormat(d => d3.format('~s')(d).replace('G', 'Bi').replace('M', 'Mi').replace('k', ' Mil'));

    const yAxis = d3.axisLeft(yScale)
      .ticks(5, '$,')
      .tickFormat(d => `R$ ${d3.format(',')(d)}`);

    const gX = svg.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .attr('class', 'text-slate-400 text-xs')
      .call(xAxis);

    const gY = svg.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .attr('class', 'text-slate-400 text-xs')
      .call(yAxis);

    // Gridlines
    svg.append('g')
      .attr('class', 'grid opacity-10')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(xAxis.tickSize(-height + margin.top + margin.bottom).tickFormat(''));

    svg.append('g')
      .attr('class', 'grid opacity-10')
      .attr('transform', `translate(${margin.left},0)`)
      .call(yAxis.tickSize(-width + margin.left + margin.right).tickFormat(''));

    // Plot Group with clip-path
    const plotGroup = svg.append('g')
      .attr('clip-path', 'url(#scatter-clip)');

    // Tooltip
    const tooltip = d3.select(container)
      .append('div')
      .attr('class', 'scatter-tooltip absolute hidden bg-slate-900/95 border border-slate-700 text-white text-xs p-3 rounded-lg shadow-xl pointer-events-none z-50 backdrop-blur');

    // Circles
    const circles = plotGroup.selectAll('circle')
      .data(items)
      .join('circle')
      .attr('cx', d => xScale(d.simWorkers || d.total_workers))
      .attr('cy', d => yScale(d.simIncome || d.avg_income))
      .attr('r', d => rScale(d.simWageBill || d.wage_bill))
      .attr('fill', d => colorScale(d.section))
      .attr('fill-opacity', d => {
        if (!searchQuery) return 0.7;
        return d.name.toLowerCase().includes(searchQuery.toLowerCase()) ? 0.95 : 0.15;
      })
      .attr('stroke', d => searchQuery && d.name.toLowerCase().includes(searchQuery.toLowerCase()) ? '#ffffff' : '#000000')
      .attr('stroke-width', 1.5)
      .attr('class', 'cursor-pointer transition-all hover:scale-125')
      .on('mouseover', (event, d) => {
        const exposure = d.adjustedExposure !== undefined ? d.adjustedExposure : d.ai_exposure_score;
        tooltip.style('display', 'block')
          .html(`
            <div class="font-bold text-emerald-400 text-sm mb-1">${d.name}</div>
            <div class="text-slate-300">Setor: <span class="text-white">${d.section}</span></div>
            <div class="text-slate-300">Trabalhadores: <span class="text-white">${formatNumber(d.simWorkers || d.total_workers)}</span></div>
            <div class="text-slate-300">Rendimento Médio: <span class="text-white">${formatBRL(d.simIncome || d.avg_income)}</span></div>
            <div class="text-slate-300">Exposição à IA: <span class="text-amber-400">${Math.round(exposure * 100)}%</span></div>
          `);
      })
      .on('mousemove', (event) => {
        const [x, y] = d3.pointer(event, container);
        tooltip.style('left', `${x + 15}px`).style('top', `${y - 20}px`);
      })
      .on('mouseout', () => tooltip.style('display', 'none'))
      .on('click', (event, d) => onSelectItem && onSelectItem(d));

    // Axis Labels
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height - 15)
      .attr('fill', '#94a3b8')
      .attr('text-anchor', 'middle')
      .attr('class', 'text-xs font-medium')
      .text('Número de Trabalhadores Ocupados (Escala Logarítmica)');

    svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', 25)
      .attr('fill', '#94a3b8')
      .attr('text-anchor', 'middle')
      .attr('class', 'text-xs font-medium')
      .text('Rendimento Mensal Médio R$ (Escala Logarítmica)');

    // Zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 15])
      .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
      .on('zoom', (event) => {
        const newX = event.transform.rescaleX(xScale);
        const newY = event.transform.rescaleY(yScale);

        gX.call(xAxis.scale(newX));
        gY.call(yAxis.scale(newY));

        circles
          .attr('cx', d => newX(d.simWorkers || d.total_workers))
          .attr('cy', d => newY(d.simIncome || d.avg_income));
      });

    svg.call(zoom);

    return () => {
      tooltip.remove();
    };

  }, [items, searchQuery, onSelectItem]);

  return (
    <div ref={containerRef} className="relative bg-slate-900/80 border border-slate-800 rounded-xl p-4 backdrop-blur shadow-xl mb-6">
      <div className="flex justify-between items-center mb-2 px-2">
        <h2 className="text-base font-semibold text-white">Dispersão Renda vs. Ocupação (Estilo Karpathy)</h2>
        <span className="text-xs text-slate-400">Use a roda do mouse para Zoom & Arraste para Pan</span>
      </div>
      <svg ref={svgRef} className="w-full"></svg>
    </div>
  );
}
