/* ============================================================
   Mapa do Trabalho Brasileiro — aplicação do companion
   D3 v7 via CDN, sem build. Dados: site/data.json (safra fixa).
   ============================================================ */
"use strict";

const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

/* ---------- formatadores pt-BR ---------- */
const fmtInt = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const fmt1 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const fmt2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmt3 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 });
const ptBrCollator = new Intl.Collator("pt-BR");

const norm = (s) =>
  (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

/* ---------- cores ---------- */
const INK = "#211d18";
const MUTED = "#6d655a";
const HAIR = "#e3ddd2";
const ACCENT = "#8f1d3a";
const STEEL = "#2f5d7a";
const REGION_COLORS = ["#8f1d3a", "#b06a14", "#3f6b4f", "#5b4c8a", "#77746c"];
const REGION_ABBR = {
  "Norte": "N", "Nordeste": "NE", "Centro-Oeste": "CO",
  "Sudeste": "SE", "Sul": "S",
};
const GROUP_COLORS = [
  "#8f1d3a", "#b06a14", "#8a6d1c", "#3f6b4f", "#2f5d7a",
  "#5b4c8a", "#7a4a5e", "#4a5568", "#77746c", "#6b3f2a",
  "#33657a", "#59642f",
];

/* ---------- tooltip compartilhado ---------- */
const tip = {
  el: null,
  ensure() {
    if (!this.el) {
      this.el = document.createElement("div");
      this.el.className = "ttp";
      this.el.style.display = "none";
      document.body.appendChild(this.el);
    }
    return this.el;
  },
  show(html, ev) {
    const el = this.ensure();
    el.innerHTML = html;
    el.style.display = "block";
    this.move(ev);
  },
  move(ev) {
    if (!this.el || this.el.style.display === "none") return;
    const pad = 14;
    const w = this.el.offsetWidth;
    const h = this.el.offsetHeight;
    let x = ev.clientX + pad;
    let y = ev.clientY + pad;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - pad;
    if (y + h > window.innerHeight - 8) y = ev.clientY - h - pad;
    this.el.style.left = x + "px";
    this.el.style.top = y + "px";
  },
  hide() {
    if (this.el) this.el.style.display = "none";
  },
};

/* ---------- utilidades de gráfico ---------- */
function responsive(container, render) {
  render(container);
  let t = null;
  const ro = new ResizeObserver(() => {
    clearTimeout(t);
    t = setTimeout(() => render(container), 120);
  });
  ro.observe(container);
}

function frame(container, width, height, margin) {
  container.innerHTML = "";
  const svg = d3.create("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("width", width)
    .attr("height", height)
    .attr("role", "presentation");
  container.appendChild(svg.node());
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const iw = Math.max(10, width - margin.left - margin.right);
  const ih = Math.max(10, height - margin.top - margin.bottom);
  return { svg, g, iw, ih };
}

function drawXAxis(g, scale, ih, label, fontSize, fmt) {
  const ax = d3.axisBottom(scale).ticks(6).tickSizeInner(-4).tickSizeOuter(0);
  if (fmt) ax.tickFormat(fmt);
  g.append("g")
    .attr("transform", `translate(0,${ih})`)
    .call(ax)
    .call((s) => s.select(".domain").attr("stroke", HAIR))
    .selectAll("tick line").attr("stroke", HAIR);
  g.selectAll(".tick text")
    .attr("font-size", fontSize)
    .attr("font-family", "system-ui, sans-serif")
    .attr("fill", MUTED);
  g.append("text")
    .attr("x", 0).attr("y", ih + 34)
    .attr("font-size", fontSize).attr("font-family", "system-ui, sans-serif")
    .attr("fill", MUTED)
    .text(label);
}

function drawYAxis(g, scale, label, fontSize, fmt) {
  const ax = d3.axisLeft(scale).ticks(5).tickSizeInner(-4).tickSizeOuter(0);
  if (fmt) ax.tickFormat(fmt);
  g.append("g")
    .call(ax)
    .call((s) => s.select(".domain").attr("stroke", HAIR))
    .selectAll("tick line").attr("stroke", HAIR);
  g.selectAll(".tick text")
    .attr("font-size", fontSize)
    .attr("font-family", "system-ui, sans-serif")
    .attr("fill", MUTED);
  const ih = scale.range()[0] - scale.range()[1];
  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -ih / 2).attr("y", -38)
    .attr("text-anchor", "middle")
    .attr("font-size", fontSize).attr("font-family", "system-ui, sans-serif")
    .attr("fill", MUTED)
    .text(label);
}

function bubbleRadius(maxJobs, rMin, rMax) {
  return d3.scaleSqrt().domain([0, maxJobs]).range([rMin, rMax]).clamp(true);
}

function linePath(xScale, yScale, x0, x1, fn) {
  const pts = [];
  const steps = 24;
  for (let i = 0; i <= steps; i++) {
    const x = x0 + ((x1 - x0) * i) / steps;
    pts.push([x, fn(x)]);
  }
  // valores fora do domínio ficam a cargo do clip-path do gráfico
  return d3.line()
    .x((d) => xScale(d[0]))
    .y((d) => yScale(d[1]))(pts);
}

/* ============================================================
   Metadados no HTML (.js-meta)
   ============================================================ */
const META_FMT = {
  author: String,
  n: (v) => fmtInt.format(v),
  n_occupations: (v) => fmtInt.format(v),
  coverage: (v) => fmt1.format(v),
  share_low_exposure: (v) => fmt1.format(v),
  low_exposure_jobs_m: (v) => fmt1.format(v),
  mean_exposure: (v) => fmt2.format(v),
  mean_schooling: (v) => fmt1.format(v),
  informality: (v) => fmt1.format(v),
  s1_beta: (v) => fmt2.format(v),
  s3a_beta: (v) => fmt1.format(v),
};

function fillMeta(meta) {
  $$(".js-meta").forEach((el) => {
    const key = el.dataset.key;
    if (key in meta && META_FMT[key]) el.textContent = META_FMT[key](meta[key]);
  });
}

/* ============================================================
   Exemplo 1 — gradiente escolaridade × exposição (S1)
   ============================================================ */
function chartGradient(data, container) {
  const w = container.clientWidth;
  if (!w) return;
  const small = w < 500;
  const h = Math.round(Math.min(460, Math.max(320, w * 0.62)));
  const margin = { top: 18, right: small ? 14 : 24, bottom: 52, left: small ? 34 : 46 };
  const { g, iw, ih } = frame(container, w, h, margin);

  const occ = data.occupations.filter((o) => o.exposure != null);
  const jobs = d3.sum(occ, (o) => o.jobs);
  const mx = d3.sum(occ, (o) => o.jobs * o.schooling) / jobs;
  const my = d3.sum(occ, (o) => o.jobs * o.exposure) / jobs;
  const s1 = data.specs.S1;

  const x = d3.scaleLinear()
    .domain(d3.extent(occ, (o) => o.schooling)).nice()
    .range([0, iw]);
  const y = d3.scaleLinear()
    .domain([0, d3.max(occ, (o) => o.exposure) * 1.06])
    .range([ih, 0]);
  const r = bubbleRadius(d3.max(occ, (o) => o.jobs), 2.5, small ? 16 : 24);

  drawXAxis(g, x, ih, "Anos de estudo (média da ocupação)", small ? 10 : 11.5);
  drawYAxis(g, y, "Exposição θ", small ? 10 : 11.5);

  const clipId = "clip-grad";
  g.append("clipPath").attr("id", clipId)
    .append("rect").attr("width", iw).attr("height", ih);
  const plot = g.append("g").attr("clip-path", `url(#${clipId})`);

  // banda de incerteza da inclinação: ±1,96·EP·(x − x̄)
  const k = 1.96 * s1.se;
  const area = d3.area()
    .x((d) => x(d))
    .y0((d) => y(my + s1.beta * (d - mx) + k * Math.abs(d - mx)))
    .y1((d) => y(my + s1.beta * (d - mx) - k * Math.abs(d - mx)));
  plot.append("path")
    .datum(d3.ticks(x.domain()[0], x.domain()[1], 24))
    .attr("fill", ACCENT).attr("fill-opacity", 0.08)
    .attr("d", area);

  plot.append("path")
    .attr("fill", "none").attr("stroke", ACCENT)
    .attr("stroke-width", 2.2)
    .attr("d", linePath(x, y, x.domain()[0], x.domain()[1], (d) => my + s1.beta * (d - mx)));

  plot.selectAll("circle.occ")
    .data(occ, (o) => o.code)
    .join("circle")
    .attr("cx", (o) => x(o.schooling))
    .attr("cy", (o) => y(o.exposure))
    .attr("r", (o) => r(o.jobs))
    .attr("fill", ACCENT).attr("fill-opacity", 0.2)
    .attr("stroke", ACCENT).attr("stroke-opacity", 0.5).attr("stroke-width", 1)
    .style("cursor", "pointer")
    .on("pointerenter pointermove", (ev, o) => tip.show(
      `<b>${o.name}</b>θ ${fmt1.format(o.exposure)}<br>${fmt1.format(o.schooling)} anos de estudo<br>${fmtInt.format(o.jobs)} empregos`,
      ev))
    .on("pointerleave", () => tip.hide());

  g.append("text")
    .attr("x", x.range()[1]).attr("y", Math.max(14, y(my + s1.beta * (x.domain()[1] - mx)) - 10))
    .attr("text-anchor", "end")
    .attr("font-size", small ? 10.5 : 12)
    .attr("font-family", "system-ui, sans-serif")
    .attr("font-weight", 600).attr("fill", ACCENT)
    .text(`β = ${fmt2.format(data.meta.s1_beta)}`);
}

/* ============================================================
   Exemplo 2 — mediação exposição → informalidade (S3a vs S3)
   ============================================================ */
function chartMediation(data, container) {
  const w = container.clientWidth;
  if (!w) return;
  const small = w < 500;
  const h = Math.round(Math.min(460, Math.max(320, w * 0.62)));
  const margin = { top: 18, right: small ? 16 : 28, bottom: 52, left: small ? 34 : 46 };
  const { g, iw, ih } = frame(container, w, h, margin);

  const occ = data.occupations.filter((o) => o.exposure != null);
  const jobs = d3.sum(occ, (o) => o.jobs);
  const mx = d3.sum(occ, (o) => o.jobs * o.exposure) / jobs;
  const my = d3.sum(occ, (o) => o.jobs * o.informality) / jobs;
  const s3a = data.specs.S3a.beta;
  const s3 = data.specs.S3.exposure.beta;

  const x = d3.scaleLinear()
    .domain([0, d3.max(occ, (o) => o.exposure) * 1.04])
    .range([0, iw]);
  const y = d3.scaleLinear().domain([0, 100]).range([ih, 0]);
  const r = bubbleRadius(d3.max(occ, (o) => o.jobs), 2.5, small ? 16 : 24);

  drawXAxis(g, x, ih, "Exposição θ da ocupação", small ? 10 : 11.5);
  drawYAxis(g, y, "Informalidade (%)", small ? 10 : 11.5);

  const clipId = "clip-med";
  g.append("clipPath").attr("id", clipId)
    .append("rect").attr("width", iw).attr("height", ih);
  const plot = g.append("g").attr("clip-path", `url(#${clipId})`);

  plot.selectAll("circle.occ")
    .data(occ, (o) => o.code)
    .join("circle")
    .attr("cx", (o) => x(o.exposure))
    .attr("cy", (o) => y(o.informality))
    .attr("r", (o) => r(o.jobs))
    .attr("fill", INK).attr("fill-opacity", 0.14)
    .style("cursor", "pointer")
    .on("pointerenter pointermove", (ev, o) => tip.show(
      `<b>${o.name}</b>θ ${fmt1.format(o.exposure)}<br>informalidade ${fmt1.format(o.informality)}%<br>${fmtInt.format(o.jobs)} empregos`,
      ev))
    .on("pointerleave", () => tip.hide());

  const lines = [
    { slope: s3a, color: ACCENT, label: `S3a  ${fmt1.format(-s3a)} p.p.` },
    { slope: s3, color: STEEL, label: `S3  ${fmt1.format(-s3)} p.p.` },
  ];
  const x0 = x.domain()[0], x1 = x.domain()[1];
  lines.forEach((L) => {
    plot.append("path")
      .attr("fill", "none").attr("stroke", L.color)
      .attr("stroke-width", 2.2)
      .attr("d", linePath(x, y, x0, x1, (d) => my + L.slope * (d - mx)));
  });

  // rótulos fixos no canto superior esquerdo (área sem dados)
  lines.forEach((L, i) => {
    g.append("text")
      .attr("x", 6)
      .attr("y", 18 + i * 19)
      .attr("font-size", small ? 10.5 : 12)
      .attr("font-family", "system-ui, sans-serif")
      .attr("font-weight", 600).attr("fill", L.color)
      .text(L.label);
  });

  g.append("text")
    .attr("x", iw).attr("y", ih - 8)
    .attr("text-anchor", "end")
    .attr("font-size", small ? 10 : 11)
    .attr("font-family", "system-ui, sans-serif")
    .attr("fill", MUTED)
    .text(`atenuação de ${fmt1.format(data.specs.S3.attenuation)}% ao condicionar na escolaridade`);
}

/* ============================================================
   Exemplo 3 — gradiente por região (inclinações de S4)
   ============================================================ */
function chartRegions(data, container) {
  const w = container.clientWidth;
  if (!w) return;
  const small = w < 500;
  const h = Math.round(Math.min(470, Math.max(330, w * 0.64)));
  const margin = { top: 18, right: small ? 40 : 58, bottom: 52, left: small ? 34 : 46 };
  const { g, iw, ih } = frame(container, w, h, margin);

  const regions = data.regions;
  const cells = regions.flatMap((rg, ri) => rg.cells.map((c) => ({ ...c, ri })));
  const x = d3.scaleLinear()
    .domain(d3.extent(cells, (c) => c.x)).nice()
    .range([0, iw]);
  const y = d3.scaleLinear()
    .domain([0, d3.max(cells, (c) => c.y) * 1.06])
    .range([ih, 0]);

  drawXAxis(g, x, ih, "Anos de estudo (média na região)", small ? 10 : 11.5);
  drawYAxis(g, y, "Exposição θ", small ? 10 : 11.5);

  const clipId = "clip-reg";
  g.append("clipPath").attr("id", clipId)
    .append("rect").attr("width", iw).attr("height", ih);
  const plot = g.append("g").attr("clip-path", `url(#${clipId})`);

  regions.forEach((rg, i) => {
    const color = REGION_COLORS[i % REGION_COLORS.length];
    plot.append("path")
      .attr("fill", "none").attr("stroke", color)
      .attr("stroke-width", 2)
      .attr("d", linePath(x, y, x.domain()[0], x.domain()[1], (d) => rg.my + rg.slope * (d - rg.mx)));
  });

  plot.selectAll("circle.cell")
    .data(cells)
    .join("circle")
    .attr("cx", (c) => x(c.x))
    .attr("cy", (c) => y(c.y))
    .attr("r", 3)
    .attr("fill", (c) => REGION_COLORS[c.ri % REGION_COLORS.length])
    .attr("fill-opacity", 0.16);

  // rótulos diretos no fim direito, com afastamento mínimo
  const ends = regions
    .map((rg, i) => ({
      rg, color: REGION_COLORS[i % REGION_COLORS.length],
      y: rg.my + rg.slope * (x.domain()[1] - rg.mx),
    }))
    .sort((a, b) => a.y - b.y);
  let prevY = -Infinity;
  ends.forEach((e) => {
    let ly = Math.max(1.5, Math.min(y.domain()[1] - 0.4, e.y));
    if (ly - prevY < 1.1) ly = prevY + 1.1;
    prevY = ly;
    g.append("text")
      .attr("x", iw + 6)
      .attr("y", y(ly) + 3.5)
      .attr("font-size", small ? 9.5 : 11)
      .attr("font-family", "system-ui, sans-serif")
      .attr("font-weight", 600).attr("fill", e.color)
      .text(`${REGION_ABBR[e.rg.region] || e.rg.region.slice(0, 2)} ${fmt2.format(e.rg.slope)}`);
  });
}

/* ============================================================
   Exemplo 4 — 27 UFs: formalidade × exposição média
   ============================================================ */
function chartUfs(data, container) {
  const w = container.clientWidth;
  if (!w) return;
  const small = w < 500;
  const h = Math.round(Math.min(470, Math.max(330, w * 0.64)));
  const margin = { top: 18, right: small ? 20 : 30, bottom: 52, left: small ? 34 : 46 };
  const { g, iw, ih } = frame(container, w, h, margin);

  const ufs = data.ufs;
  const LABEL = new Set(["SP", "SC", "MA", "PA", "DF"]);
  const x = d3.scaleLinear()
    .domain(d3.extent(ufs, (u) => u.formality)).nice()
    .range([0, iw]);
  const y = d3.scaleLinear()
    .domain(d3.extent(ufs, (u) => u.mean_exposure)).nice()
    .range([ih, 0]);
  const r = bubbleRadius(d3.max(ufs, (u) => u.jobs), 3, small ? 15 : 22);

  drawXAxis(g, x, ih, "Formalidade do emprego (%)", small ? 10 : 11.5, (v) => fmtInt.format(v));
  drawYAxis(g, y, "Exposição média θ", small ? 10 : 11.5, (v) => fmt1.format(v));

  // ajuste linear das 27 UFs, ponderado por empregos
  const wSum = d3.sum(ufs, (u) => u.jobs);
  const cx = d3.sum(ufs, (u) => u.jobs * u.formality) / wSum;
  const cy = d3.sum(ufs, (u) => u.jobs * u.mean_exposure) / wSum;
  const bUf = d3.sum(ufs, (u) => u.jobs * (u.formality - cx) * (u.mean_exposure - cy))
    / d3.sum(ufs, (u) => u.jobs * (u.formality - cx) ** 2);

  const clipUf = "clip-uf";
  g.append("clipPath").attr("id", clipUf)
    .append("rect").attr("width", iw).attr("height", ih);
  g.append("path")
    .attr("clip-path", `url(#${clipUf})`)
    .attr("fill", "none").attr("stroke", STEEL)
    .attr("stroke-width", 2).attr("stroke-opacity", 0.8)
    .attr("d", linePath(x, y, x.domain()[0], x.domain()[1], (d) => cy + bUf * (d - cx)));

  g.append("g")
    .selectAll("circle.uf")
    .data(ufs, (u) => u.uf)
    .join("circle")
    .attr("cx", (u) => x(u.formality))
    .attr("cy", (u) => y(u.mean_exposure))
    .attr("r", (u) => r(u.jobs))
    .attr("fill", STEEL).attr("fill-opacity", 0.2)
    .attr("stroke", STEEL).attr("stroke-opacity", 0.5).attr("stroke-width", 1)
    .style("cursor", "pointer")
    .on("pointerenter pointermove", (ev, u) => tip.show(
      `<b>${u.uf}</b>formalidade ${fmt1.format(u.formality)}%<br>θ médio ${fmt2.format(u.mean_exposure)}<br>${fmtInt.format(u.jobs)} empregos`,
      ev))
    .on("pointerleave", () => tip.hide());

  g.append("g")
    .selectAll("text.uf")
    .data(ufs.filter((u) => LABEL.has(u.uf)), (u) => u.uf)
    .join("text")
    .attr("x", (u) => x(u.formality) + r(u.jobs) + 5)
    .attr("y", (u) => y(u.mean_exposure) + 3.5)
    .attr("font-size", small ? 10 : 11.5)
    .attr("font-family", "system-ui, sans-serif")
    .attr("font-weight", 600).attr("fill", INK)
    .text((u) => u.uf);

  const ann = g.append("g")
    .attr("transform", `translate(${iw * 0.02},${ih * 0.04})`);
  ann.append("rect")
    .attr("width", small ? iw * 0.9 : iw * 0.52)
    .attr("height", 56)
    .attr("rx", 6)
    .attr("fill", "#f2efe8");
  ann.append("text")
    .attr("x", 10).attr("y", 16)
    .attr("font-size", small ? 9.5 : 11)
    .attr("font-family", "system-ui, sans-serif").attr("fill", INK)
    .text("∂θ/∂formalidade = −3,10 + 0,28·e");
  ann.append("text")
    .attr("x", 10).attr("y", 31)
    .attr("font-size", small ? 9.5 : 11)
    .attr("font-family", "system-ui, sans-serif").attr("fill", MUTED)
    .text("derivada marginal nula em e ≈ 11 anos de estudo");
  ann.append("text")
    .attr("x", 10).attr("y", 46)
    .attr("font-size", small ? 9.5 : 11)
    .attr("font-family", "system-ui, sans-serif").attr("fill", STEEL)
    .attr("font-weight", 600)
    .text(`ajuste ponderado: ${bUf >= 0 ? "+" : "\u2212"}${fmt3.format(Math.abs(bUf))} θ p.p.`);
}

/* ============================================================
   Exemplo 5 — floresta de robustez
   ============================================================ */
function chartForest(data, container) {
  const w = container.clientWidth;
  if (!w) return;
  const small = w < 520;
  const rows = data.robustness;
  const rowH = small ? 24 : 27;
  const h = rows.length * rowH + 64;
  const margin = {
    top: 14, bottom: 42,
    left: small ? 128 : 196,
    right: small ? 44 : 56,
  };
  const { g, iw, ih } = frame(container, w, h, margin);

  const x = d3.scaleLinear().domain([0.15, 0.3]).range([0, iw]);
  const baseline = rows[0].beta;

  const grid = g.append("g");
  x.ticks(6).forEach((t) => {
    grid.append("line")
      .attr("x1", x(t)).attr("x2", x(t))
      .attr("y1", 0).attr("y2", ih)
      .attr("stroke", HAIR).attr("stroke-dasharray", "2 3");
    grid.append("text")
      .attr("x", x(t)).attr("y", ih + 16)
      .attr("text-anchor", "middle")
      .attr("font-size", small ? 9.5 : 11)
      .attr("font-family", "system-ui, sans-serif").attr("fill", MUTED)
      .text(fmt2.format(t));
  });
  g.append("text")
    .attr("x", iw).attr("y", ih + 34)
    .attr("text-anchor", "end")
    .attr("font-size", small ? 9.5 : 11)
    .attr("font-family", "system-ui, sans-serif").attr("fill", MUTED)
    .text("coeficiente de escolaridade (IC 95%)");

  g.append("line")
    .attr("x1", x(baseline)).attr("x2", x(baseline))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", ACCENT).attr("stroke-width", 1).attr("stroke-dasharray", "4 3");

  rows.forEach((rw, i) => {
    const cy = i * rowH + rowH / 2;
    const lo = rw.beta - 1.96 * rw.se;
    const hi = rw.beta + 1.96 * rw.se;
    const isBase = i === 0;

    g.append("text")
      .attr("x", -10).attr("y", cy + 3.5)
      .attr("text-anchor", "end")
      .attr("font-size", small ? 9.5 : 11)
      .attr("font-family", "system-ui, sans-serif")
      .attr("fill", isBase ? ACCENT : INK)
      .attr("font-weight", isBase ? 600 : 400)
      .text(rw.label);

    g.append("line")
      .attr("x1", x(Math.max(0.15, lo))).attr("x2", x(Math.min(0.3, hi)))
      .attr("y1", cy).attr("y2", cy)
      .attr("stroke", isBase ? ACCENT : MUTED).attr("stroke-width", 1.5);
    [lo, hi].forEach((v) => {
      g.append("line")
        .attr("x1", x(Math.max(0.15, v))).attr("x2", x(Math.max(0.15, v)))
        .attr("y1", cy - 4).attr("y2", cy + 4)
        .attr("stroke", isBase ? ACCENT : MUTED).attr("stroke-width", 1.5);
    });
    g.append("circle")
      .attr("cx", x(Math.max(0.15, Math.min(0.3, rw.beta))))
      .attr("cy", cy)
      .attr("r", isBase ? 4.5 : 3.5)
      .attr("fill", isBase ? ACCENT : INK)
      .style("cursor", "pointer")
      .on("pointerenter pointermove", (ev) => tip.show(
        `<b>${rw.label}</b>β ${fmt3.format(rw.beta)}<br>EP ${fmt3.format(rw.se)}, R² ${fmt2.format(rw.r2)}`,
        ev))
      .on("pointerleave", () => tip.hide());

    g.append("text")
      .attr("x", iw + 8).attr("y", cy + 3.5)
      .attr("font-size", small ? 9.5 : 11)
      .attr("font-family", "ui-monospace, monospace")
      .attr("fill", isBase ? ACCENT : INK)
      .attr("font-weight", isBase ? 600 : 400)
      .text(fmt3.format(rw.beta));
  });
}

/* ============================================================
   Explorador — tabela + dispersão + detalhe
   ============================================================ */
function initExplorer(data) {
  const table = $("#occ-table");
  const tbody = $("tbody", table);
  const searchInput = $("#search");
  const showNull = $("#show-null");
  const countEl = $("#occ-count");
  const detailEl = $("#occ-detail");
  const scatterEl = $("#chart-scatter");

  const groups = Array.from(new Set(data.occupations.map((o) => o.group))).sort();
  const groupColor = new Map(groups.map((gr, i) => [gr, GROUP_COLORS[i % GROUP_COLORS.length]]));

  // ⚡ Bolt: Cache normalized strings to avoid expensive repeated norm() calls during search
  data.occupations.forEach((o) => {
    o._normName = norm(o.name);
    o._normGroup = norm(o.group);
  });

  const state = { sortKey: "jobs", sortDir: -1, query: "", selected: null };

  function rows() {
    let list = data.occupations.filter((o) =>
      showNull.checked || o.exposure != null);
    if (state.query) {
      const q = norm(state.query);
      list = list.filter((o) =>
        o._normName.includes(q) || o._normGroup.includes(q));
    }
    const dir = state.sortDir;
    const key = state.sortKey;
    list = list.slice().sort((a, b) => {
      let va = a[key], vb = b[key];
      if (typeof va === "string") return dir * ptBrCollator.compare(va, vb);
      if (va == null) return 1;
      if (vb == null) return -1;
      return dir * (va - vb);
    });
    return list;
  }

  function renderTable() {
    const list = rows();
    tbody.innerHTML = "";
    list.forEach((o) => {
      const tr = document.createElement("tr");
      tr.dataset.code = o.code;
      if (state.selected === o.code) tr.className = "sel";
      tr.setAttribute("tabindex", "0");
      tr.innerHTML = `
        <td class="occ-name">${o.name}${state.selected === o.code ? ' <span class="visually-hidden">(selecionada)</span>' : ""}<span class="occ-group">${o.group}</span></td>
        <td class="num">${fmtInt.format(o.jobs)}</td>
        <td class="num">${o.exposure == null ? "n.d." : fmt1.format(o.exposure)}</td>
        <td class="num">${fmt1.format(o.informality)}%</td>
        <td class="num">${fmt1.format(o.schooling)}</td>
        <td class="num">R$ ${fmtInt.format(o.income)}</td>`;
      tr.addEventListener("click", () => select(o.code));
      tr.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(o.code); }
      });
      tbody.appendChild(tr);
    });
    countEl.textContent = `Exibindo ${fmtInt.format(list.length)} de ${fmtInt.format(data.occupations.length)} ocupações`;
    $$(".sort-btn", table).forEach((btn) => {
      const th = btn.closest("th");
      const active = th.dataset.sort === state.sortKey;
      btn.setAttribute("aria-pressed", active ? "true" : "false");
      th.setAttribute("aria-sort",
        active ? (state.sortDir === 1 ? "ascending" : "descending") : "none");
    });
  }

  function renderScatter() {
    const container = scatterEl;
    const w = container.clientWidth;
    if (!w) return;
    const small = w < 420;
    const h = Math.round(Math.min(430, Math.max(300, w * 0.95)));
    const margin = { top: 14, right: 18, bottom: 50, left: small ? 34 : 44 };
    const { g, iw, ih } = frame(container, w, h, margin);

    const occ = data.occupations.filter((o) => o.exposure != null);
    const x = d3.scaleLinear()
      .domain([0, d3.max(occ, (o) => o.exposure) * 1.04])
      .range([0, iw]);
    const y = d3.scaleLinear().domain([0, 100]).range([ih, 0]);
    const r = bubbleRadius(d3.max(occ, (o) => o.jobs), 2.5, small ? 13 : 19);

    drawXAxis(g, x, ih, "Exposição θ", small ? 10 : 11.5);
    drawYAxis(g, y, "Informalidade (%)", small ? 10 : 11.5);

    // inclinações de referência do Exemplo 2 (S3a e S3), tracejadas
    const jobs = d3.sum(occ, (o) => o.jobs);
    const mx = d3.sum(occ, (o) => o.jobs * o.exposure) / jobs;
    const my = d3.sum(occ, (o) => o.jobs * o.informality) / jobs;
    const ref = [
      { slope: data.specs.S3a.beta, color: ACCENT, label: `S3a ${fmt1.format(-data.specs.S3a.beta)} p.p.` },
      { slope: data.specs.S3.exposure.beta, color: STEEL, label: `S3 ${fmt1.format(-data.specs.S3.exposure.beta)} p.p.` },
    ];
    ref.forEach((L) => {
      g.append("path")
        .attr("fill", "none").attr("stroke", L.color)
        .attr("stroke-width", 1.6).attr("stroke-opacity", 0.55)
        .attr("stroke-dasharray", "5 4")
        .attr("d", linePath(x, y, x.domain()[0], x.domain()[1], (d) => my + L.slope * (d - mx)));
    });
    ref.forEach((L, i) => {
      g.append("text")
        .attr("x", 6).attr("y", 14 + i * 16)
        .attr("font-size", small ? 9.5 : 10.5)
        .attr("font-family", "system-ui, sans-serif")
        .attr("font-weight", 600).attr("fill", L.color).attr("fill-opacity", 0.85)
        .text(L.label);
    });

    const sel = occ.find((o) => o.code === state.selected);
    const plain = occ.filter((o) => o.code !== state.selected);

    g.append("g")
      .selectAll("circle")
      .data(plain, (o) => o.code)
      .join("circle")
      .attr("cx", (o) => x(o.exposure))
      .attr("cy", (o) => y(o.informality))
      .attr("r", (o) => r(o.jobs))
      .attr("fill", (o) => groupColor.get(o.group) || MUTED)
      .attr("fill-opacity", 0.3)
      .style("cursor", "pointer")
      .on("pointerenter pointermove", (ev, o) => tip.show(
        `<b>${o.name}</b>${o.group}<br>θ ${fmt1.format(o.exposure)}<br>informalidade ${fmt1.format(o.informality)}%`,
        ev))
      .on("pointerleave", () => tip.hide())
      .on("click", (ev, o) => { ev.stopPropagation(); select(o.code); });

    if (sel) {
      g.append("circle")
        .attr("cx", x(sel.exposure)).attr("cy", y(sel.informality))
        .attr("r", r(sel.jobs) + 4)
        .attr("fill", "none").attr("stroke", ACCENT).attr("stroke-width", 2);
      g.append("circle")
        .attr("cx", x(sel.exposure)).attr("cy", y(sel.informality))
        .attr("r", r(sel.jobs))
        .attr("fill", ACCENT).attr("fill-opacity", 0.75);
    }
  }

  function renderDetail() {
    const o = data.occupations.find((occ) => occ.code === state.selected);
    if (!o) {
      detailEl.innerHTML = `<p class="occ-detail-empty">Selecione uma linha da tabela para ver o detalhe.</p>`;
      return;
    }
    detailEl.innerHTML = `
      <h3>${o.name}</h3>
      <dl>
        <div><dt>Empregos</dt><dd>${fmtInt.format(o.jobs)}</dd></div>
        <div><dt>Exposição θ</dt><dd>${o.exposure == null ? "n.d." : fmt1.format(o.exposure)}</dd></div>
        <div><dt>Informalidade</dt><dd>${fmt1.format(o.informality)}%</dd></div>
        <div><dt>Escolaridade</dt><dd>${fmt1.format(o.schooling)} anos</dd></div>
        <div><dt>Renda habitual</dt><dd>R$ ${fmtInt.format(o.income)}</dd></div>
        <div><dt>Idade média</dt><dd>${fmt1.format(o.age)} anos</dd></div>
      </dl>`;
  }

  function select(code) {
    state.selected = code;
    renderDetail();
    renderScatter();
    renderTable();
    // devolve o foco à linha selecionada (re-render recriou o DOM)
    const tr = tbody.querySelector(`tr[data-code="${code}"]`);
    if (tr) tr.focus();
  }

  $$(".sort-btn", table).forEach((btn) => {
    const th = btn.closest("th");
    btn.addEventListener("click", () => {
      const key = th.dataset.sort;
      if (state.sortKey === key) state.sortDir *= -1;
      else { state.sortKey = key; state.sortDir = key === "name" ? 1 : -1; }
      renderTable();
    });
  });

  let t = null;
  searchInput.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => { state.query = searchInput.value; renderTable(); }, 120);
  });
  showNull.addEventListener("change", renderTable);

  renderTable();
  renderDetail();
  responsive(scatterEl, renderScatter);
}

/* ============================================================
   Cópia da citação
   ============================================================ */
function initCopyBib() {
  const btn = $("#copy-bib");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    const text = $("code", $("#bibtex")).textContent;
    let ok = false;
    try {
      await navigator.clipboard.writeText(text);
      ok = true;
    } catch (err) {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { ok = document.execCommand("copy"); } catch (e2) { ok = false; }
      ta.remove();
    }
    const old = btn.textContent;
    btn.textContent = ok ? "Copiado" : "Não foi possível copiar";
    setTimeout(() => { btn.textContent = old; }, 2000);
  });
}

/* ============================================================
   Boot
   ============================================================ */
function dataError() {
  $$(".js-meta").forEach((el) => { el.textContent = "n.d."; });
  $$(".chart").forEach((el) => {
    el.innerHTML = '<p class="chart-note">Não foi possível carregar data.json.</p>';
  });
}

async function boot() {
  initCopyBib();
  let data;
  try {
    const res = await fetch("data.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    dataError();
    return;
  }
  if (!window.d3) { dataError(); return; }

  fillMeta(data.meta);
  responsive($("#chart-gradient"), (c) => chartGradient(data, c));
  responsive($("#chart-mediation"), (c) => chartMediation(data, c));
  responsive($("#chart-regions"), (c) => chartRegions(data, c));
  responsive($("#chart-ufs"), (c) => chartUfs(data, c));
  responsive($("#chart-forest"), (c) => chartForest(data, c));
  initExplorer(data);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
