const detailState = { rows: [] };
function parseDetailCsv(text) {
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i], n = text[i + 1];
    if (c === '"' && quoted && n === '"') { cell += '"'; i += 1; }
    else if (c === '"') quoted = !quoted;
    else if (c === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((c === "\n" || c === "\r") && !quoted) {
      if (c === "\r" && n === "\n") i += 1;
      row.push(cell); cell = ""; if (row.some(v => v.trim())) rows.push(row); row = [];
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const headers = rows.shift() || [];
  return rows.map(values => Object.fromEntries(headers.map((key, i) =>
    [key.replace(/^\uFEFF/, ""), (values[i] || "").trim()])));
}
function safe(value) {
  return String(value).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]));
}
function renderDetails() {
  const query = document.querySelector("#detail-search").value.toLowerCase();
  const group = document.querySelector("#detail-group").value;
  const filtered = detailState.rows.filter(row =>
    (!group || row.service_group === group) &&
    Object.values(row).join(" ").toLowerCase().includes(query)).slice(0, 100);
  document.querySelector("#detail-table").innerHTML = filtered.length ? filtered.map(row => `
    <tr><td><b>${safe(row.route_number || row.route_id)}</b></td>
    <td>${safe(row.service_group)}<br><small>${safe(row.operator)}</small></td>
    <td>${safe(row.origin || "—")} → ${safe(row.destination || "—")}</td>
    <td>${safe(row.route_map)}</td><td>${safe(row.timetable)}</td>
    <td>${safe(row.vehicle_type)}</td><td>${safe(row.fare)}</td><td>${safe(row.depot)}</td></tr>`).join("") :
    '<tr><td colspan="8">沒有符合的資料</td></tr>';
  document.querySelector("#detail-status").textContent =
    `${detailState.rows.length.toLocaleString()} 筆資料 · 顯示最多 100 筆`;
}
async function start() {
  try {
    const response = await fetch("../routes/route_details.csv");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    detailState.rows = parseDetailCsv(await response.text());
    renderDetails();
  } catch (error) {
    document.querySelector("#detail-status").textContent = `載入失敗：${error.message}`;
  }
}
document.querySelector("#detail-search").addEventListener("input", renderDetails);
document.querySelector("#detail-group").addEventListener("change", renderDetails);
start();
