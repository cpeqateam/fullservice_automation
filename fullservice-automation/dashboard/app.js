// FULL Servis dashboard — sunucudan 1 sn'de bir durum çeker, 4 düğümü canlı gösterir.
// Build gerektirmez; sunucu bu dosyayı statik olarak sunar.

const $ = (id) => document.getElementById(id);

async function fetchState() {
  const res = await fetch("/api/state", { cache: "no-store" });
  if (!res.ok) throw new Error("state alınamadı");
  return res.json();
}

function connIcon(conn) {
  if (conn === "wifi") return "📶";
  if (conn === "cable") return "🔌";
  return "🖥️";
}

// Tek bir testin satırı (isim + yüzde + bar + mesaj)
function renderTest(taskKey, label, t) {
  const status = t.status || "idle";
  const pct = Math.round(t.progress || 0);
  return `
    <div class="test-row">
      <div class="test-line">
        <span class="test-name">${label}</span>
        <span class="test-pct">${pct}%</span>
      </div>
      <div class="bar ${status}"><span style="width:${pct}%"></span></div>
      <div class="test-msg">${t.message || ""}</div>
    </div>`;
}

function renderNode(node, labels) {
  const onlineCls = node.online ? "online" : "offline";
  const meta = [node.platform, node.ip].filter(Boolean).join(" · ") || "bağlı değil";

  let testsHtml = "";
  const roles = node.roles || [];
  if (roles.length === 0) {
    testsHtml = `<div class="empty">Bu düğüme atanmış test yok.</div>`;
  } else {
    testsHtml = roles.map((r) => {
      const t = (node.tests && node.tests[r]) || { progress: 0, status: "idle", message: "" };
      return renderTest(r, labels[r] || r, t);
    }).join("");
  }

  return `
    <div class="node-card">
      <div class="node-head">
        <div>
          <div class="node-title">
            <span class="conn-icon">${connIcon(node.conn)}</span>
            <h3>${node.label}</h3>
          </div>
          <div class="node-meta">${meta}</div>
        </div>
        <span class="dot ${onlineCls}" title="${node.online ? "online" : "offline"}"></span>
      </div>
      <div class="tests">${testsHtml}</div>
    </div>`;
}

function renderSession(s) {
  const badge = $("session-badge");
  if (s.running) {
    badge.textContent = "ÇALIŞIYOR";
    badge.className = "badge running";
  } else if (s.session_id) {
    badge.textContent = "Tamamlandı";
    badge.className = "badge done";
  } else {
    badge.textContent = "Hazır";
    badge.className = "badge";
  }
  $("session-id").textContent = s.session_id || "—";
}

async function tick() {
  try {
    const state = await fetchState();
    $("conn-status").className = "ok";
    $("server-ip").textContent = state.server_lan_ip || "—";
    renderSession(state.session || {});
    const labels = state.test_labels || {};
    $("nodes").innerHTML = (state.nodes || []).map((n) => renderNode(n, labels)).join("");
  } catch (e) {
    $("conn-status").className = "bad";
  }
}

async function startTest() {
  const body = {
    duration: parseInt($("p-duration").value) || null,
    modem_ip: $("p-modem").value.trim() || null,
    internet_ip: $("p-internet").value.trim() || null,
    youtube_link: $("p-youtube").value.trim() || null,
  };
  const res = await fetch("/api/session/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  console.log("start:", data);
  if (data.skipped && data.skipped.length) {
    alert("Şu düğümlere ulaşılamadı (offline): " + data.skipped.join(", "));
  }
  tick();
}

async function stopTest() {
  await fetch("/api/session/stop", { method: "POST" });
  tick();
}

$("btn-start").addEventListener("click", startTest);
$("btn-stop").addEventListener("click", stopTest);

tick();
setInterval(tick, 1000);
