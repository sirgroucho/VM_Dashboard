document.addEventListener("DOMContentLoaded", () => {
  // Dropdown toggle
  const userDropdown = document.querySelector(".user-dropdown");
  const dropdownToggle = document.querySelector(".dropdown-toggle");
  if (dropdownToggle) {
    dropdownToggle.addEventListener("click", () => {
      userDropdown.classList.toggle("open");
    });
    document.addEventListener("click", (e) => {
      if (!userDropdown.contains(e.target)) {
        userDropdown.classList.remove("open");
      }
    });
  }

  // Chart.js load
  const script = document.createElement("script");
  script.src = "https://cdn.jsdelivr.net/npm/chart.js";
  script.onload = initDashboard;
  document.head.appendChild(script);
});

function initDashboard() {
  let chart;
  const fmtTime = (t) => new Date(t * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  const ago = (t) => {
    const s = Math.floor(Date.now() / 1000) - t;
    if (s < 60) return `${s}s ago`;
    const m = Math.floor(s / 60);
    return `${m}m ago`;
  };
  const pillClass = (ev) => {
    if (ev.event === "player_joined") return "pill join";
    if (ev.event === "player_left") return "pill leave";
    return "pill metrics";
  };

  async function loadLive() {
    try {
      const res = await fetch("/mc/live.json", { cache: "no-store" });
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();

      const snap = data.snapshot || {};
      const series = data.players_series || [];
      const events = data.events || [];

      // Update stats
      document.getElementById("players").textContent = snap.players_online ?? "—";
      document.getElementById("latency").textContent = snap.latency_ms ?? "—";
      document.getElementById("version").textContent = snap.version || "—";
      document.getElementById("motd").textContent = snap.motd || "—";
      document.getElementById("last-update").textContent = snap.ts ? fmtTime(snap.ts) : "—";
      document.getElementById("ts-ago").textContent = snap.ts ? ago(snap.ts) : "—";

      // Chart
      const labels = series.map((p) => fmtTime(p.t));
      const values = series.map((p) => p.v);
      const ctx = document.getElementById("playersLine");
      if (chart) chart.destroy();
      chart = new Chart(ctx, {
        type: "line",
        data: { labels, datasets: [{ label: "Players", data: values, tension: 0.3 }] },
        options: { responsive: true, animation: false, scales: { y: { beginAtZero: true } } }
      });

      // Events
      const evHost = document.getElementById("events");
      evHost.innerHTML = "";
      events.slice(0, 50).forEach(ev => {
        const line = document.createElement("div");
        line.className = "evt";
        line.innerHTML = `<span class="${pillClass(ev)}">${ev.event}</span>
                          <span>${fmtTime(ev.ts || 0)}</span>
                          <span>players: ${ev.players_online ?? ""}</span>`;
        evHost.appendChild(line);
      });

      // KV dump
      const kvHost = document.getElementById("kvs");
      kvHost.innerHTML = "";
      Object.entries(snap).forEach(([k,v]) => {
        if (["ts","players_online","latency_ms","version","motd","event"].includes(k)) return;
        const row = document.createElement("div");
        row.className = "kv";
        row.innerHTML = `<span>${k}</span><span>${typeof v === "object" ? JSON.stringify(v) : v}</span>`;
        kvHost.appendChild(row);
      });

    } catch (err) {
      console.error("Live fetch error:", err);
    }
  }

  loadLive();
  setInterval(loadLive, 5000);
}
