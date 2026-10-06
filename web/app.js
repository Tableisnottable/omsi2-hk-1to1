const state = { rows: [], file: "../routes/hk_bus_routes.csv" };
const csvFiles = {
  routes: "../routes/hk_bus_routes.csv",
  nr: "../routes/nr_routes.csv",
  roads: "../maps/HP1C_CW/osm_ways.csv"
};
let map;
let layers;

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
  return records.map(values => Object.fromEntries(headers.map((key, i) =>
    [key.replace(/^\uFEFF/, ""), (values[i] || "").trim()])));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

function updateRows() {
  const query = document.querySelector("#route-search").value.toLowerCase();
  const filtered = state.rows.filter(row =>
    Object.values(row).join(" ").toLowerCase().includes(query)).slice(0, 50);
  const body = document.querySelector("#route-table");
  body.innerHTML = filtered.length ? filtered.map(row => `
    <tr><td><b>${escapeHtml(row.route_number || row.route_id || "—")}</b></td>
    <td>${escapeHtml(row.operator || row.service_type || "—")}</td>
    <td>${escapeHtml(row.origin || "—")}</td>
    <td>${escapeHtml(row.destination || "—")}</td></tr>`).join("") :
    '<tr><td colspan="4">沒有符合的資料</td></tr>';
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
    document.querySelector("#route-table").innerHTML =
      '<tr><td colspan="4">請用本機 HTTP server 開啟網站，以讀取 CSV。</td></tr>';
    status.textContent = `路線資料載入失敗：${error.message}`;
  }
}

async function loadStats() {
  const targets = [["#route-count", csvFiles.routes], ["#nr-count", csvFiles.nr],
    ["#road-count", csvFiles.roads]];
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

function csvCoordinates(value) {
  return String(value || "").split(" ").map(pair => {
    const [longitude, latitude] = pair.split(",").map(Number);
    return Number.isFinite(latitude) && Number.isFinite(longitude) ?
      [latitude, longitude] : null;
  }).filter(Boolean);
}

function updateMapVisibility() {
  [["#show-roads", layers.roads], ["#show-stops", layers.stops],
    ["#show-buildings", layers.buildings]].forEach(([selector, layer]) => {
    if (document.querySelector(selector).checked) layer.addTo(map);
    else map.removeLayer(layer);
  });
}

async function loadMapData(area) {
  const status = document.querySelector("#map-status");
  status.textContent = `正在載入 HP1C_${area}…`;
  Object.values(layers).forEach(layer => layer.clearLayers());
  try {
    const base = `../maps/HP1C_${encodeURIComponent(area)}`;
    const responses = await Promise.all(["osm_ways.csv", "osm_stops.csv", "osm_buildings.csv"]
      .map(file => fetch(`${base}/${file}`)));
    if (responses.some(response => !response.ok)) throw new Error("map CSV not found");
    const [ways, stops, buildings] =
      await Promise.all(responses.map(response => response.text().then(parseCsv)));
    const roadLines = ways.map(row => {
      const points = csvCoordinates(row.coordinates);
      return points.length > 1 ? L.polyline(points, { color: "#1261a0", weight: 2, opacity: .72 })
        .bindPopup(`<b>${escapeHtml(row.name || "Unnamed road")}</b><br>${escapeHtml(row.highway || "")}`) : null;
    }).filter(Boolean);
    const stopPoints = stops.map(row => {
      const point = [Number(row.latitude), Number(row.longitude)];
      return Number.isFinite(point[0]) ? L.circleMarker(point, { radius: 4, color: "#ff7f3f", fillOpacity: .9 })
        .bindPopup(`<b>${escapeHtml(row.name || "Bus stop")}</b>`) : null;
    }).filter(Boolean);
    const buildingPolygons = buildings.map(row => {
      const points = csvCoordinates(row.coordinates);
      return points.length > 2 ? L.polygon(points, { color: "#7a5aa6", weight: 1, fillColor: "#9f82c7", fillOpacity: .25 })
        .bindPopup(`<b>${escapeHtml(row.name || "Building")}</b>`) : null;
    }).filter(Boolean);
    roadLines.forEach(item => item.addTo(layers.roads));
    stopPoints.forEach(item => item.addTo(layers.stops));
    buildingPolygons.forEach(item => item.addTo(layers.buildings));
    const points = roadLines.flatMap(item => item.getLatLngs()).filter(point => point && point.lat);
    if (points.length) map.fitBounds(L.latLngBounds(points), { padding: [20, 20] });
    updateMapVisibility();
    status.textContent = `${roadLines.length.toLocaleString()} roads · ${stopPoints.length.toLocaleString()} stops · ${buildingPolygons.length.toLocaleString()} buildings`;
  } catch (error) {
    status.textContent = `地圖載入失敗：${error.message}`;
  }
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

if (window.L) {
  map = L.map("map-view").setView([22.285, 114.175], 15);
  layers = { roads: L.layerGroup(), stops: L.layerGroup(), buildings: L.layerGroup() };
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);
  document.querySelectorAll("#show-roads, #show-stops, #show-buildings")
    .forEach(item => item.addEventListener("change", updateMapVisibility));
  document.querySelector("#map-area").addEventListener("change",
    event => loadMapData(event.target.value));
  loadMapData("CW");
}
