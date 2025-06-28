document.addEventListener('DOMContentLoaded', function () {
  var summaryCollapse = document.getElementById('summaryCollapse');
  var toggleBtn = document.getElementById('summary-toggle-btn');
  if (summaryCollapse && toggleBtn) {
    summaryCollapse.addEventListener('show.bs.collapse', function () {
      toggleBtn.textContent = 'Hide Summary';
    });
    summaryCollapse.addEventListener('hide.bs.collapse', function () {
      toggleBtn.textContent = 'Show Summary';
    });
  }

  // Table sorting logic
  const table = document.getElementById('expenses-table');
  if (table) {
    let currentSort = { col: null, dir: 'asc' };
    const getCellValue = (tr, idx) => {
      const td = tr.children[idx];
      if (!td) return '';
      // Remove currency symbols and commas for numeric sort
      let text = td.textContent.trim();
      if (idx === 1) text = text.replace(/[^\d.-]/g, '');
      return text;
    };
    const comparer = (idx, asc, type) => (a, b) => {
      let v1 = getCellValue(a, idx);
      let v2 = getCellValue(b, idx);
      if (type === 'number') {
        v1 = parseFloat(v1) || 0;
        v2 = parseFloat(v2) || 0;
      } else {
        v1 = v1.toLowerCase();
        v2 = v2.toLowerCase();
      }
      if (v1 < v2) return asc ? -1 : 1;
      if (v1 > v2) return asc ? 1 : -1;
      return 0;
    };
    table.querySelectorAll('th[data-sort]').forEach((th, idx) => {
      th.style.cursor = 'pointer';
      th.addEventListener('click', function () {
        const type = th.dataset.sort === 'amount' ? 'number' : 'string';
        const asc = currentSort.col === idx ? currentSort.dir === 'desc' : true;
        const tbody = table.querySelector('tbody');
        Array.from(tbody.querySelectorAll('tr'))
          .sort(comparer(idx, asc, type))
          .forEach(tr => tbody.appendChild(tr));
        // Update indicators
        table.querySelectorAll('.sort-indicator').forEach(i => (i.textContent = ''));
        th.querySelector('.sort-indicator').textContent = asc ? '▲' : '▼';
        currentSort = { col: idx, dir: asc ? 'asc' : 'desc' };
      });
    });
    // Default sort by date added (created_at) ascending (first render)
    // No explicit column for date, so keep as is (already sorted by backend)
  }
});
