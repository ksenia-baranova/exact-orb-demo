// REQ-WHEEL-04/07/08: presentation addresses, never calculation or DTO deduplication.
export function aspectKey({ from, to, type }) {
  return JSON.stringify([...[from, to].sort(), type]);
}

export function createChartSelection() {
  let pointIds = new Set(), rows = [], groups = new Map();
  let selection = null, aspectsExpanded = false, housesExpanded = false, pointsExpanded = false;

  function accept(chart) {
    pointIds = new Set(chart?.points.map(({ id }) => id) ?? []);
    // Own only the source addressing fields; callers cannot mutate the accepted index.
    rows = chart?.aspects.map(({ from, to, type }) => ({ from, to, type })) ?? [];
    groups = new Map();
    rows.forEach((row, index) => {
      const key = aspectKey(row);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(index);
    });
    if (!chart) {
      selection = null;
      aspectsExpanded = false;
      housesExpanded = false;
      pointsExpanded = false;
    } else if (selection?.kind === "point" && !pointIds.has(selection.id)
      || selection?.kind === "aspect" && groups.get(selection.key)?.length !== 1) {
      selection = null;
    }
  }

  return Object.freeze({
    accept,
    activatePoint(id) {
      if (!pointIds.has(id)) return;
      if (selection?.kind === "point" && selection.id === id) {
        selection = null;
        aspectsExpanded = false; // Owner: repeating a point returns the first five.
      } else selection = { kind: "point", id };
    },
    activateAspect(key) {
      if (groups.get(key)?.length !== 1) return; // S1 includes hidden/background rows.
      selection = selection?.kind === "aspect" && selection.key === key ? null : { kind: "aspect", key };
    },
    toggleAspects() { if (selection === null) aspectsExpanded = !aspectsExpanded; },
    toggleHouses() { housesExpanded = !housesExpanded; },
    togglePoints() { if (selection?.kind !== "aspect") pointsExpanded = !pointsExpanded; },
    snapshot() {
      const sourceRows = rows.map((row, index) => {
        const key = aspectKey(row);
        return { index, key, selectable: groups.get(key).length === 1,
          selected: selection?.kind === "aspect" && selection.key === key };
      });
      const filtered = selection?.kind === "point" ? sourceRows.filter(({ index }) =>
        rows[index].from === selection.id || rows[index].to === selection.id)
        : selection?.kind === "aspect" ? sourceRows.filter(({ selected }) => selected) : sourceRows;
      const visible = selection !== null || aspectsExpanded ? filtered : filtered.slice(0, 5);
      return { selection: selection === null ? null : { ...selection }, aspectsExpanded, housesExpanded, pointsExpanded,
        sourceRows, visibleAspectIndices: visible.map(({ index }) => index),
        ambiguousGroups: [...groups].filter(([, indices]) => indices.length > 1)
          .map(([key, indices]) => ({ key, indices: [...indices] })) };
    },
  });
}
