// Passive SVG leaf: positions come only from ChartDTO; HTML owns selection.
import { layoutWheel, ASPECT_COLORS, POINT_GLYPHS, POINT_VECTORS } from "./wheel_layout.mjs";
const NS = "http://www.w3.org/2000/svg";
const FONT = '"Segoe UI Symbol", "Segoe UI", sans-serif';
export function createWheelRenderer(surface) {
  const document = surface.ownerDocument;
  let disposed = false, cached = null;
  const node = (tag, attrs = {}, text) => {
    const element = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, String(value));
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const vector = (id, color, attrs = {}) => {
    const mark = node('g', { 'font-size':16, ...attrs, 'data-symbol':id });
    mark.append(node('title',{},POINT_VECTORS[id].label));
    for(const [tag, values] of POINT_VECTORS[id].shapes) {
      const {solid,...shape}=values;
      mark.append(node(tag,{...shape,fill:solid?color:'none',stroke:color,'stroke-width':1.25}));
    }
    return mark;
  };
  return {
    async update(snapshot, publish, currentSurface = surface) {
      await document.fonts?.ready;
      if (disposed) return;
      const { chart, width, selection } = snapshot;
      const svg = node("svg", { xmlns: NS, width, height: width, viewBox: "0 0 " + width + " " + width,
        role: "img", "aria-label": chart.kind === "natal" ? "Натальная карта" : "Космограмма",
        "font-family": FONT, overflow: "hidden", focusable: "false" });
      currentSurface.replaceChildren(svg);
      const selectedAspectKey = selection?.kind === "aspect" ? selection.key : null;
      const key = JSON.stringify([chart, width, snapshot.fontRevision, selectedAspectKey]);
      if (!cached || cached.key !== key) {
        const measure = (text, size) => {
          const vectorId=Object.keys(POINT_VECTORS).find(id=>POINT_GLYPHS[id]===text);
          const sample = vectorId ? vector(vectorId,"#f3eadb") : node("text", { x: 0, y: 0, "font-size": size }, text);
          svg.append(sample);
          const b = sample.getBBox(); sample.remove();
          return { x: b.x, y: b.y, w: b.width, h: b.height };
        };
        cached = { key, layout: layoutWheel(chart, measure, width, { selectedAspectKey }) };
      }
      const layout = cached.layout, { xy, R, C, H } = layout;
      svg.setAttribute("height", H); svg.setAttribute("viewBox", "0 0 " + width + " " + H);
      svg.append(node("desc", {}, "Значки планет сгруппированы внутри опубликованных домов и могут быть сдвинуты для читаемости. Истинные отметки и аспекты используют точные координаты; числовые данные доступны в таблицах."));
      const selected = selection?.kind === "aspect" ? layout.aspects.find(a => a.unique && a.key === selection.key) : null;
      const drawn = selected ? selected.category === "background" ? [] : [selected] : layout.eligible;
      const markers = new Set(drawn.filter(a => a.type === "conjunction").map(a => "conj:" + a.key));
      const isSelected = g => selection?.kind === "point" ? g.key === selection.id
        : Boolean(selected && (g.key === selected.from || g.key === selected.to
          || g.key === "angle:" + selected.from || g.key === "angle:" + selected.to || g.key === "conj:" + selected.key));
      const visible = g => g.kind !== "marker" || markers.has(g.key);
      const circle = radius => svg.append(node("circle", { cx: C[0], cy: C[1], r: radius,
        fill: "none", stroke: "#777777", "stroke-width": 0.7 }));
      for (let i = 0; i < 12; i++) {
        const a = xy(i * 30, R), b = xy((i + 1) * 30, R), c = xy((i + 1) * 30, R - 26), d = xy(i * 30, R - 26);
        svg.append(node("path", { d: "M"+a+" A"+R+" "+R+" 0 0 0 "+b+" L"+c+" A"+(R-26)+" "+(R-26)+" 0 0 1 "+d+" Z",
          fill: i % 2 ? "#111111" : "#181818", stroke: "#666666", "stroke-width": 0.5, "data-sector": i }));
      }
      circle(R); circle(R - 26); circle(layout.aspectR);
      // Degree ruler and a separate numbered house band make both coordinate systems visible.
      for (let degree = 0; degree < 360; degree++) {
        const from = xy(degree, R - 26), to = xy(degree, R - 26 - (degree % 10 === 0 ? 6 : degree % 5 === 0 ? 4 : 2));
        svg.append(node("line", {x1:from[0],y1:from[1],x2:to[0],y2:to[1],
          stroke:degree % 10 === 0 ? "#b8aa97" : "#666666","stroke-width":0.5,"data-degree-tick":degree}));
      }
      for (const sector of layout.sectors) {
        const outer = layout.houseR + 10, inner = layout.houseR - 10;
        const a = xy(sector.start,outer), b = xy(sector.end,outer), c = xy(sector.end,inner), d = xy(sector.start,inner);
        const large = (sector.end - sector.start + 360) % 360 > 180 ? 1 : 0;
        svg.append(node("path", {d:"M"+a+" A"+outer+" "+outer+" 0 "+large+" 0 "+b+" L"+c+" A"+inner+" "+inner+" 0 "+large+" 1 "+d+" Z",
          fill:selected ? "#292311" : "#15130f",stroke:"#777777","stroke-width":0.6,"data-house-sector":sector.number}));
      }
      const visibleCusps = new Set(layout.sectors.flatMap(sector => [sector.number,sector.number%12+1]));
      for (const h of (chart.houses ?? []).filter(house => !selected || visibleCusps.has(house.number))) {
        const a = xy(h.cusp_longitude, layout.aspectR), b = xy(h.cusp_longitude, R - 26);
        const cusp = node("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1],
          stroke: selected || [1,4,7,10].includes(h.number) ? "#b8aa97" : "#777777", "stroke-width": selected ? 1.1 : 0.7, "data-house": h.number });
        cusp.append(node("title", {}, "Дом " + h.number)); svg.append(cusp);
      }
      for (const a of drawn.filter(a => a.type !== "conjunction")) {
        const p = xy(layout.endpoint.get(a.from), layout.aspectR), q = xy(layout.endpoint.get(a.to), layout.aspectR);
        svg.append(node("line", { x1: p[0], y1: p[1], x2: q[0], y2: q[1],
          stroke: ASPECT_COLORS[a.type], "stroke-width": selected ? 2.5 : 1,
          "stroke-dasharray": a.category === "working" ? "4 3" : "none",
          "data-aspect": a.key, "data-source-index": a.sourceIndex }));
      }
      for (const leader of layout.leaders) {
        const group = layout.groups.find(g => g.key === leader.key);
        if (!visible(group)) continue;
        const d = leader.path.map((p, i) => (i ? "L" : "M") + p.join(" ")).join(" ");
        svg.append(node("path", { d, fill: "none", stroke: "#080706", "stroke-width": 1.5, "data-leader-bridge": group.key }));
        svg.append(node("path", { d, fill: "none", stroke: isSelected(group) ? "#f0cd73" : "#b8aa97",
          "stroke-width": isSelected(group) ? 1.5 : 0.75, "data-leader": group.key }));
      }
      // Paint true marks below their own labels: ○ must never become ☉.
      for (const g of layout.groups.filter(g => visible(g) && g.kind !== "house")) svg.append(node("circle", {
        cx: g.A[0], cy: g.A[1], r: 1, fill: "#f0cd73", "data-anchor": g.key }));
      for (const g of [...layout.fixed, ...layout.groups].filter(visible)) {
        const group = node("g", { "data-label": g.key, "data-kind": g.kind,
          "data-point-house": g.kind === "point" ? g.house ?? "none" : "none", "data-row": g.row ?? "none", transform: "translate(" + g.P[0] + " " + g.P[1] + ")" });
        if (g.kind === "house") group.setAttribute("data-house-number", g.number);
        for (const [i, p] of g.draw.entries()) {
          group.append(node("rect", { x: p.b[0], y: p.b[1], width: p.b[2] - p.b[0], height: p.b[3] - p.b[1],
            rx: 1, fill: "#080706", opacity: 0.94 }));
          if (p.contour && isSelected(g)) group.append(node("rect", { x: p.b[0] + 0.75, y: p.b[1] + 0.75,
            width: p.b[2] - p.b[0] - 1.5, height: p.b[3] - p.b[1] - 1.5,
            rx: 2, fill: "none", stroke: "#f0cd73", "stroke-width": 1.5, "data-selected": g.key }));
          const attrs={ 'data-component':g.key+':'+i };
          if(g.kind==='point'&&i===0&&POINT_VECTORS[g.key])
            group.append(vector(g.key,'#f3eadb',{...attrs,transform:'translate('+p.x+' '+p.y+')'}));
          else group.append(node("text", { x: p.x, y: p.y, "font-size": p.size,
            fill: g.kind === "marker" ? ASPECT_COLORS[g.aspect.type] : g.kind === "house" ? "#f0cd73" : "#f3eadb",...attrs }, p.text));
        }
        svg.append(group);
      }
      if (!disposed) publish(svg);
    },
    dispose() { disposed = true; cached = null; },
  };
}
