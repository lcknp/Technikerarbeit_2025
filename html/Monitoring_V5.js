const FOUR_HOURS = 4 * 60 * 60 * 1000;
const ONE_HOUR   = 60 * 60 * 1000;

// Hilfsfunktion: Chart mit Standard-Optik erstellen
function createTimeSeriesChart(canvasId, yOptions = {}) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const labels = [];
  const data = [];

  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data,
        borderColor: "#222",
        backgroundColor: "rgba(0,0,0,0.05)",
        tension: 0.25,
        borderWidth: 2,
        pointRadius: 0
      }]
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "time",
          time: { displayFormats: { minute: "HH:mm" } }
        },
        y: yOptions
      },
      plugins: { legend: { display: false } }
    }
  });

  return { chart, labels, data };
}

// Neuen Punkt einfügen und auf Zeitfenster begrenzen
function pushPoint(series, tsString, value, windowMs) {
  const t = new Date(tsString);
  series.labels.push(t);
  series.data.push(value);

  const cutoff = Date.now() - windowMs;
  while (series.labels.length && series.labels[0].getTime() < cutoff) {
    series.labels.shift();
    series.data.shift();
  }
  series.chart.update("none");
}

// CO₂ Chart
const co2Series = createTimeSeriesChart("co2Chart");
const allSeries = [co2Series];

// Einheiten-State
let unitCount = 0;
const unitSeries = {};

// Einheitenkarte ins HTML einfügen
function buildUnitCard(n) {
  const row = document.getElementById("einheiten-row");
  const col = document.createElement("div");
  col.className = "col-md-4";
  col.innerHTML = `
    <div class="card card-custom p-3">
      <h6 class="fw-bold mb-3">Einheit <span id="device${n}"></span></h6>
      <div class="row mb-1"><div class="col-7">Temperatur Innen:</div><div class="col-5 text-end"><span id="tempinnen${n}">–</span> °C</div></div>
      <div class="row mb-1"><div class="col-7">Feuchte Innen:</div><div class="col-5 text-end"><span id="huminnen${n}">–</span> %</div></div>
      <div class="row mb-1"><div class="col-7">Temperatur Außen:</div><div class="col-5 text-end"><span id="tempaussen${n}">–</span> °C</div></div>
      <div class="row mb-1"><div class="col-7">Feuchte Außen:</div><div class="col-5 text-end"><span id="humaussen${n}">–</span> %</div></div>
      <div class="row mb-1"><div class="col-7">Drehzahl:</div><div class="col-5 text-end"><span id="drehzahl${n}">–</span> U/min</div></div>
      <div class="row mb-1"><div class="col-7">PWM:</div><div class="col-5 text-end"><span id="periode${n}">–</span> %</div></div>
    </div>`;
  row.appendChild(col);
}

// Temperatur- und PWM-Charts für eine Einheit einfügen
function buildUnitCharts(n) {
  const container = document.getElementById("charts-container");

  const tempRow = document.createElement("div");
  tempRow.className = "row g-3 mt-4";
  tempRow.innerHTML = `
    <div class="col-md-6">
      <div class="card card-custom p-3 h-100">
        <h6 class="fw-bold mb-2">Temperatur Innen – Einheit ${n} (1 Stunde)</h6>
        <div><canvas id="tempInnen${n}Chart"></canvas></div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card card-custom p-3 h-100">
        <h6 class="fw-bold mb-2">Temperatur Außen – Einheit ${n} (1 Stunde)</h6>
        <div><canvas id="tempAussen${n}Chart"></canvas></div>
      </div>
    </div>`;
  container.appendChild(tempRow);

  const pwmRow = document.createElement("div");
  pwmRow.className = "row g-3 mt-4 mb-5";
  pwmRow.innerHTML = `
    <div class="col-md-6">
      <div class="card card-custom p-3 h-100">
        <h6 class="fw-bold mb-2">PWM – Einheit ${n} (1 Stunde)</h6>
        <div><canvas id="pwm${n}Chart"></canvas></div>
      </div>
    </div>`;
  container.appendChild(pwmRow);

  const tempInnen  = createTimeSeriesChart(`tempInnen${n}Chart`);
  const tempAussen = createTimeSeriesChart(`tempAussen${n}Chart`);
  const pwm        = createTimeSeriesChart(`pwm${n}Chart`, { min: 0, max: 100 });

  unitSeries[n] = { tempInnen, tempAussen, pwm };
  allSeries.push(tempInnen, tempAussen, pwm);
}

// Darkmode
const darkBtn = document.getElementById("darkmodeBtn");
darkBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
  const isDark = document.body.classList.contains("dark-mode");
  darkBtn.textContent = isDark ? "☀️" : "🌙";

  for (const s of allSeries) {
    const ds = s.chart.data.datasets[0];
    ds.borderColor     = isDark ? "#ffffff" : "#222222";
    ds.backgroundColor = isDark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.05)";
    s.chart.update("none");
  }
});

// Daten holen und Oberfläche + Charts aktualisieren
async function refresh() {
  const r = await fetch("/latest.json?" + Date.now());
  const j = await r.json();

  // Kopf / Status
  document.getElementById("ts").textContent        = j.ts;
  document.getElementById("ts_status").textContent = j.ts;

  // CO₂
  document.getElementById("co2").textContent = Math.round(j.co2) + " ppm";
  document.getElementById("t").textContent   = j.t.toFixed(1);
  document.getElementById("h").textContent   = j.h.toFixed(1);
  document.getElementById("p").textContent   = j.p.toFixed(1);

  // Air Quality
  let air = "Good";
  if      (j.co2 >= 1000) air = "Poor";
  else if (j.co2 >= 800)  air = "Moderate";
  document.getElementById("airquality-text").textContent  = air;
  document.getElementById("airquality-small").textContent = air;

  // CO₂ Chart
  pushPoint(co2Series, j.ts, j.co2, FOUR_HOURS);

  // Anzahl Einheiten aus JSON ermitteln (zählt device1, device2, ...)
  if (unitCount === 0) {
    let n = 1;
    while (j[`device${n}`] !== undefined) n++;
    unitCount = n - 1;

    for (let i = 1; i <= unitCount; i++) {
      buildUnitCard(i);
      buildUnitCharts(i);
    }
  }

  // Einheiten-Werte aktualisieren
  for (let n = 1; n <= unitCount; n++) {
    document.getElementById(`device${n}`).textContent     = j[`device${n}`]    ?? "–";
    document.getElementById(`tempinnen${n}`).textContent  = j[`tempinnen${n}`] ?? "–";
    document.getElementById(`huminnen${n}`).textContent   = j[`huminnen${n}`]  ?? "–";
    document.getElementById(`tempaussen${n}`).textContent = j[`tempaussen${n}`]?? "–";
    document.getElementById(`humaussen${n}`).textContent  = j[`humaussen${n}`] ?? "–";
    document.getElementById(`drehzahl${n}`).textContent   = j[`drehzahl${n}`]  ?? "–";
    document.getElementById(`periode${n}`).textContent    = j[`periode${n}`]   ?? "–";

    if (unitSeries[n]) {
      pushPoint(unitSeries[n].tempInnen,  j.ts, j[`tempinnen${n}`],  ONE_HOUR);
      pushPoint(unitSeries[n].tempAussen, j.ts, j[`tempaussen${n}`], ONE_HOUR);
      pushPoint(unitSeries[n].pwm,        j.ts, j[`periode${n}`],    ONE_HOUR);
    }
  }
}

setInterval(refresh, 5000);
refresh();