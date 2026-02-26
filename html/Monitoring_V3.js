const FOUR_HOURS = 4 * 60 * 60 * 1000;
const ONE_HOUR  = 60 * 60 * 1000;

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

// Charts anlegen
const co2Series   = createTimeSeriesChart("co2Chart");
const temp1Series = createTimeSeriesChart("temp1Chart");
const temp2Series = createTimeSeriesChart("temp2Chart");
const pwm1Series  = createTimeSeriesChart("pwm1Chart", { min: 0, max: 100 });
const pwm2Series  = createTimeSeriesChart("pwm2Chart", { min: 0, max: 100 });

const allSeries = [co2Series, temp1Series, temp2Series, pwm1Series, pwm2Series];

// neuen Punkt einfügen und auf Zeitfenster begrenzen
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

// Darkmode
const darkBtn = document.getElementById("darkmodeBtn");
darkBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
  const isDark = document.body.classList.contains("dark-mode");
  darkBtn.textContent = isDark ? "☀️" : "🌙";

  for (const s of allSeries) {
    const ds = s.chart.data.datasets[0];
    if (isDark) {
      ds.borderColor = "#ffffff";
      ds.backgroundColor = "rgba(255,255,255,0.15)";
    } else {
      ds.borderColor = "#222222";
      ds.backgroundColor = "rgba(0,0,0,0.05)";
    }
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

  // CO₂ als ganze Zahl + "ppm"
  document.getElementById("co2").textContent = Math.round(j.co2) + " ppm";

  document.getElementById("t").textContent = j.t.toFixed(1);
  document.getElementById("h").textContent = j.h.toFixed(1);
  document.getElementById("p").textContent = j.p.toFixed(1);

  // Einheit 1
  document.getElementById("tempinnen1").textContent = j.tempinnen1;
  document.getElementById("huminnen1").textContent  = j.huminnen1;
  document.getElementById("tempaussen1").textContent= j.tempaussen1;
  document.getElementById("humaussen1").textContent = j.humaussen1;
  document.getElementById("drehzahl1").textContent  = j.drehzahl1;
  document.getElementById("periode1").textContent   = j.periode1;
  document.getElementById("device1").textContent    = j.device1;

  // Einheit 2
  document.getElementById("tempinnen2").textContent = j.tempinnen2;
  document.getElementById("huminnen2").textContent  = j.huminnen2;
  document.getElementById("tempaussen2").textContent= j.tempaussen2;
  document.getElementById("humaussen2").textContent = j.humaussen2;
  document.getElementById("drehzahl2").textContent  = j.drehzahl2;
  document.getElementById("periode2").textContent   = j.periode2;
  document.getElementById("device2").textContent    = j.device2;

  // Airquality
  let air = "Good";
  if (j.co2 >= 1000) air = "Poor";
  else if (j.co2 >= 800) air = "Moderate";
  document.getElementById("airquality-text").textContent  = air;
  document.getElementById("airquality-small").textContent = air;

  // Charts aktualisieren
  pushPoint(co2Series,   j.ts, j.co2,        FOUR_HOURS);
  pushPoint(temp1Series, j.ts, j.tempinnen1, ONE_HOUR);
  pushPoint(temp2Series, j.ts, j.tempinnen2, ONE_HOUR);
  pushPoint(pwm1Series,  j.ts, j.periode1,   ONE_HOUR);
  pushPoint(pwm2Series,  j.ts, j.periode2,   ONE_HOUR);
}

setInterval(refresh, 5000);
refresh();
