const API_URL = "http://localhost:8000";
let sessionId = null;

const chatBox = document.getElementById("chat-box");
const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const historyList = document.getElementById("history-list");
const modelSelect = document.getElementById("model-select");
const newChatBtn = document.getElementById("new-chat-btn");

// ---------- Empty state ----------
function showEmptyState() {
  chatBox.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">📖</div>
      <h2>Assalamu'alaikum</h2>
      <p>Saya siap membantu pertanyaan seputar ilmu tajwid <strong>Surat An-Naba'</strong>.<br>
      Jawaban saya hanya berdasarkan dokumen tajwid yang tersedia.</p>
    </div>
  `;
}

function clearEmptyStateIfNeeded() {
  const empty = chatBox.querySelector(".empty-state");
  if (empty) empty.remove();
}

// ---------- Chat Baru ----------
newChatBtn.addEventListener("click", () => {
  sessionId = null;
  showEmptyState();
  input.value = "";
  input.focus();
  highlightActiveHistory(null);
});

// ---------- Penyimpanan riwayat ----------
function getHistory() {
  return JSON.parse(localStorage.getItem("tajwid_history") || "[]");
}

function groupKey(item) {
  return String(item.sessionId || item.id);
}

function saveToHistory(entry) {
  const h = getHistory();
  h.unshift({ id: Date.now() + "-" + Math.random().toString(36).slice(2, 7), ...entry });
  localStorage.setItem("tajwid_history", JSON.stringify(h.slice(0, 300)));
  renderHistory();
}

function deleteHistoryGroup(sessionKey) {
  const h = getHistory().filter(item => groupKey(item) !== sessionKey);
  localStorage.setItem("tajwid_history", JSON.stringify(h));
  if (sessionId === sessionKey) {
    sessionId = null;
    showEmptyState();
  }
  renderHistory();
}

function renderHistory() {
  const h = getHistory();
  const order = [];
  const groups = {};

  h.forEach(item => {
    const key = groupKey(item);
    if (!groups[key]) {
      groups[key] = [];
      order.push(key);
    }
    groups[key].push(item);
  });

  if (order.length === 0) {
    historyList.innerHTML = `<div class="history-empty">Belum ada riwayat.</div>`;
    return;
  }

  historyList.innerHTML = order.map(key => {
    const entries = groups[key];
    const firstEntry = entries[entries.length - 1]; // pertanyaan pertama di sesi ini
    const isActive = sessionId === key;
    return `
      <div class="history-item ${isActive ? 'history-active' : ''}" data-session="${key}" title="${escapeHtml(firstEntry.pertanyaan)}">
        <span class="history-text">${escapeHtml(truncate(firstEntry.pertanyaan, 34))}</span>
        <button type="button" class="history-delete-btn" data-session="${key}" title="Hapus percakapan ini">✕</button>
      </div>
    `;
  }).join("");
}

historyList.addEventListener("click", (e) => {
  const delBtn = e.target.closest(".history-delete-btn");
  if (delBtn) {
    e.stopPropagation();
    deleteHistoryGroup(delBtn.dataset.session);
    return;
  }
  const item = e.target.closest(".history-item");
  if (item) {
    openHistorySession(item.dataset.session);
  }
});

function highlightActiveHistory(sessionKey) {
  historyList.querySelectorAll(".history-item").forEach(el => {
    el.classList.toggle("history-active", el.dataset.session === sessionKey);
  });
}

function openHistorySession(sessionKey) {
  const h = getHistory();
  const entries = h.filter(item => groupKey(item) === sessionKey).slice().reverse();

  if (entries.length === 0) {
    console.warn("Tidak ada entri ditemukan untuk sessionKey:", sessionKey);
    return;
  }

  clearEmptyStateIfNeeded();
  chatBox.innerHTML = "";
  entries.forEach(entry => {
    renderUserBubble(entry.pertanyaan);
    renderBotBubble(entry);
  });
  chatBox.scrollTop = chatBox.scrollHeight;

  sessionId = sessionKey;
  highlightActiveHistory(sessionKey);
}

function truncate(str, n) {
  return str.length > n ? str.slice(0, n) + "…" : str;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------- Render bubble ----------
function renderUserBubble(text) {
  const div = document.createElement("div");
  div.className = "message user-message";
  div.innerHTML = `
    <div class="msg-avatar">U</div>
    <div class="msg-body">${escapeHtml(text)}</div>
  `;
  chatBox.appendChild(div);
  return div;
}

function renderBotBubble(data) {
  const div = document.createElement("div");
  div.className = "message bot-message";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "📖";
  div.appendChild(avatar);

  const body = document.createElement("div");
  body.className = "msg-body";

  const jawabanEl = document.createElement("div");
  jawabanEl.textContent = data.jawaban;
  body.appendChild(jawabanEl);

  if (data.sumber && data.sumber.length > 0) {
    const sumberEl = document.createElement("div");
    sumberEl.className = "sumber";
    sumberEl.textContent = "Sumber: " + data.sumber.join(", ");
    body.appendChild(sumberEl);
  }

  if (typeof data.is_grounded !== "undefined") {
    const scoreRow = document.createElement("div");
    scoreRow.className = "score-row";

    const badge = document.createElement("span");
    badge.className = "grounded-badge " + (data.is_grounded ? "grounded-true" : "grounded-false");
    badge.textContent = data.is_grounded ? "Grounded" : "Tidak grounded";
    scoreRow.appendChild(badge);

    if (typeof data.grounding_score === "number") {
      const barWrap = document.createElement("div");
      barWrap.className = "score-bar-wrap";
      const bar = document.createElement("div");
      bar.className = "score-bar";
      bar.style.width = Math.round(data.grounding_score * 100) + "%";
      barWrap.appendChild(bar);
      scoreRow.appendChild(barWrap);

      const label = document.createElement("span");
      label.className = "score-label";
      label.textContent = data.grounding_score.toFixed(3);
      scoreRow.appendChild(label);
    }
    body.appendChild(scoreRow);
  }

  div.appendChild(body);
  chatBox.appendChild(div);
  return div;
}

function addBotLoading() {
  const div = document.createElement("div");
  div.className = "message bot-message";
  div.innerHTML = `
    <div class="msg-avatar">📖</div>
    <div class="msg-body loading">Mencari jawaban...</div>
  `;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return div;
}

// ---------- Kirim pertanyaan ----------
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const pertanyaan = input.value.trim();
  if (!pertanyaan) return;

  clearEmptyStateIfNeeded();
  renderUserBubble(pertanyaan);
  chatBox.scrollTop = chatBox.scrollHeight;
  input.value = "";
  sendBtn.disabled = true;

  const loadingEl = addBotLoading();

  try {
    const response = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pertanyaan: pertanyaan,
        session_id: sessionId,
        model: modelSelect ? modelSelect.value : undefined
      })
    });

    if (!response.ok) throw new Error(`Server merespons status ${response.status}`);

    const data = await response.json();
    sessionId = data.session_id;

    loadingEl.remove();
    renderBotBubble(data);
    chatBox.scrollTop = chatBox.scrollHeight;

    saveToHistory({
      sessionId: sessionId,
      pertanyaan,
      jawaban: data.jawaban,
      sumber: data.sumber,
      is_grounded: data.is_grounded,
      grounding_score: data.grounding_score
    });
    highlightActiveHistory(String(sessionId));

  } catch (err) {
    loadingEl.remove();
    const div = document.createElement("div");
    div.className = "message bot-message";
    div.innerHTML = `<div class="msg-avatar">📖</div><div class="msg-body">Terjadi kesalahan: ${escapeHtml(err.message)}</div>`;
    chatBox.appendChild(div);
    console.error(err);
  } finally {
    sendBtn.disabled = false;
  }
});

// ---------- Mulai ----------
showEmptyState();
renderHistory();