const state = { rows: [], file: "../routes/hk_bus_routes.csv" };
const csvFiles = {
  routes: "../routes/hk_bus_routes.csv",
  nr: "../routes/nr_routes.csv",
  roads: "../maps/HP1C_CW/osm_ways.csv"
};

function parseCsv(text) {
  const records = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i], next = text[i + 1];
    if (char === '"' && quoted && next === '"') { cell += '"'; i += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(cell); cell = "";
      if (row.some(value => value.trim())) records.push(row);
      row = [];
    } else cell += char;
  }
  if (cell || row.length) { row.push(cell); records.push(row); }
  const headers = records.shift() || [];
  return records.map(values => Object.fromEntries(headers.map((key, i) => [key.replace(/^\uFEFF/, ""), (values[i] || "").trim()])));
}

function updateRows() {
  const query = document.querySelector("#route-search").value.toLowerCase();
  const filtered = state.rows.filter(row => Object.values(row).join(" ").toLowerCase().includes(query)).slice(0, 50);
  const body = document.querySelector("#route-table");
  body.innerHTML = filtered.length ? filtered.map(row => `
    <tr><td><b>${escapeHtml(row.route_number || row.route_id || "—")}</b></td>
    <td>${escapeHtml(row.operator || row.service_type || "—")}</td>
    <td>${escapeHtml(row.origin || "—")}</td>
    <td>${escapeHtml(row.destination || "—")}</td></tr>`).join("") : '<tr><td colspan="4">沒有符合的資料</td></tr>';
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

async function loadRoutes(file) {
  const status = document.querySelector("#route-status");
  status.textContent = "正在載入路線資料…";
  try {
    const response = await fetch(file);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.rows = parseCsv(await response.text());
    state.file = file;
    status.textContent = `${state.rows.length.toLocaleString()} 筆資料 · 顯示最多 50 筆，可使用搜尋篩選`;
    updateRows();
  } catch (error) {
    state.rows = [];
    document.querySelector("#route-table").innerHTML = '<tr><td colspan="4">本地檔案模式無法讀取 CSV。請用本機 HTTP server 開啟網站。</td></tr>';
    status.textContent = `路線資料載入失敗：${error.message}`;
  }
}

async function loadStats() {
  const targets = [
    ["#route-count", csvFiles.routes],
    ["#nr-count", csvFiles.nr],
    ["#road-count", csvFiles.roads]
  ];
  await Promise.all(targets.map(async ([selector, file]) => {
    try {
      const response = await fetch(file);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const rows = parseCsv(await response.text());
      document.querySelector(selector).textContent = rows.length.toLocaleString();
    } catch {
      document.querySelector(selector).textContent = "—";
    }
  }));
}

document.querySelectorAll(".route-tabs button").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".route-tabs button").forEach(item => item.classList.remove("active"));
    button.classList.add("active");
    loadRoutes(button.dataset.file);
  });
});
document.querySelector("#route-search").addEventListener("input", updateRows);
loadRoutes(state.file);
loadStats();
