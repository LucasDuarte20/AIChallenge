const API = "/api";

const messagesEl = document.getElementById("messages");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send");
const typingIndicator = document.getElementById("typing-indicator");
const statusDot = document.getElementById("status-dot");
const audioInput = document.getElementById("audio-input");

// --- Utilidades ---

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function formatNumber(val, decimals = 0) {
  if (val === null || val === undefined) return "-";
  return Number(val).toLocaleString("es-AR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}

function markdownToHtml(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br>");
}

// --- Verificar API ---
async function checkHealth() {
  try {
    const res = await fetch(`${API}/health`);
    if (res.ok) {
      statusDot.className = "status-dot ok";
      statusDot.title = "API conectada";
    } else {
      throw new Error();
    }
  } catch {
    statusDot.className = "status-dot error";
    statusDot.title = "API no disponible";
  }
}

// --- Renderizado de mensajes ---

function addMessage(role, html, data = null) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  if (role === "bot") {
    wrapper.innerHTML = `<div class="avatar">🤖</div><div class="bubble">${html}</div>`;
    if (data) {
      const card = buildMaterialCard(data);
      if (card) wrapper.querySelector(".bubble").appendChild(card);
    }
  } else {
    wrapper.innerHTML = `<div class="bubble">${html}</div>`;
  }

  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

function buildMaterialCard(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) return null;

  const card = document.createElement("div");
  card.className = "material-card";

  const title = data.material_raw || data.material_code || "Material";
  card.innerHTML = `<div class="card-title">${escapeHtml(title)}</div>`;

  const grid = document.createElement("div");
  grid.className = "card-grid";

  const rows = [
    ["Código", data.material_code],
    ["MLFB", data.material_mlfb],
    ["Stock actual", data.stock_actual !== null ? formatNumber(data.stock_actual) + " un." : null],
    ["En viaje", data.stock_en_viaje > 0 ? formatNumber(data.stock_en_viaje) + " un." : null],
    ["Pendiente", data.stock_pendiente > 0 ? formatNumber(data.stock_pendiente) + " un." : null],
    ["A comprar", data.stock_a_comprar > 0 ? formatNumber(data.stock_a_comprar) + " un." : null],
    ["Costo unit.", data.costo_estante_usd_unit !== null ? "USD " + formatNumber(data.costo_estante_usd_unit, 2) : null],
    ["Total estante", data.stock_actual_x_costo_usd !== null ? "USD " + formatNumber(data.stock_actual_x_costo_usd, 2) : null],
  ];

  for (const [label, value] of rows) {
    if (value === null || value === undefined) continue;
    const row = document.createElement("div");
    row.className = "card-row";
    const valClass = label === "Total estante" || label === "Costo unit." ? "card-value highlight" : "card-value";
    row.innerHTML = `<span class="card-label">${label}</span><span class="${valClass}">${escapeHtml(String(value))}</span>`;
    grid.appendChild(row);
  }

  card.appendChild(grid);
  return card;
}

function buildListCard(items) {
  if (!Array.isArray(items) || items.length === 0) return null;
  const card = document.createElement("div");
  card.className = "material-card";
  card.innerHTML = `<div class="card-title">Resultados (${items.length})</div>`;

  for (const item of items.slice(0, 10)) {
    const row = document.createElement("div");
    row.className = "card-row";
    const val = item.stock_a_comprar || item.stock_pendiente || item.stock_actual;
    row.innerHTML = `
      <span class="card-label" style="font-size:12px">${escapeHtml(item.material_raw || item.material_code || "")}</span>
      <span class="card-value">${val !== null ? formatNumber(val) + " un." : "-"}</span>
    `;
    card.appendChild(row);
  }

  return card;
}

// --- Enviar mensaje al chat ---

async function sendMessage(text) {
  if (!text.trim()) return;

  addMessage("user", escapeHtml(text));
  chatInput.value = "";
  typingIndicator.classList.remove("hidden");
  btnSend.disabled = true;
  scrollToBottom();

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const json = await res.json();
    typingIndicator.classList.add("hidden");
    btnSend.disabled = false;

    if (!res.ok) {
      addMessage("bot", `<p>⚠️ Error: ${escapeHtml(json.detail || "Error desconocido")}</p>`);
      return;
    }

    const html = markdownToHtml(escapeHtml(json.response));
    const isListIntent = ["pending_stock", "buy_list"].includes(json.intent);
    const data = isListIntent && Array.isArray(json.data) ? null : json.data;

    const wrapper = addMessage("bot", `<p>${html}</p>`, data);

    if (isListIntent && Array.isArray(json.data) && json.data.length > 0) {
      const card = buildListCard(json.data);
      if (card) wrapper.querySelector(".bubble").appendChild(card);
    }
  } catch (err) {
    typingIndicator.classList.add("hidden");
    btnSend.disabled = false;
    addMessage("bot", `<p>⚠️ No se pudo conectar con la API. ¿Está el backend corriendo?</p>`);
  }
}

// --- Enviar audio ---

audioInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  addMessage("user", `🎤 <em>Audio enviado: ${escapeHtml(file.name)}</em>`);
  typingIndicator.classList.remove("hidden");
  btnSend.disabled = true;

  const formData = new FormData();
  formData.append("audio", file);

  try {
    const res = await fetch(`${API}/transcribe-audio`, {
      method: "POST",
      body: formData,
    });
    const json = await res.json();
    typingIndicator.classList.add("hidden");
    btnSend.disabled = false;

    if (!res.ok) {
      addMessage("bot", `<p>⚠️ Error en transcripción: ${escapeHtml(json.detail || "")}</p>`);
      return;
    }

    const html = markdownToHtml(escapeHtml(json.response));
    addMessage("bot", `<p>${html}</p>`, json.data);
  } catch {
    typingIndicator.classList.add("hidden");
    btnSend.disabled = false;
    addMessage("bot", `<p>⚠️ Error procesando audio.</p>`);
  }

  audioInput.value = "";
});

// --- Modal de importación ---

const modalImport = document.getElementById("modal-import");
const btnImport = document.getElementById("btn-import");
const btnImportCancel = document.getElementById("btn-import-cancel");
const btnImportConfirm = document.getElementById("btn-import-confirm");
const importResult = document.getElementById("import-result");
const excelFileInput = document.getElementById("excel-file");
const sheetNameInput = document.getElementById("sheet-name");

btnImport.addEventListener("click", () => {
  importResult.className = "import-result hidden";
  importResult.textContent = "";
  modalImport.classList.remove("hidden");
});

btnImportCancel.addEventListener("click", () => modalImport.classList.add("hidden"));

modalImport.addEventListener("click", (e) => {
  if (e.target === modalImport) modalImport.classList.add("hidden");
});

btnImportConfirm.addEventListener("click", async () => {
  const file = excelFileInput.files[0];
  if (!file) {
    showImportResult("error", "Seleccioná un archivo Excel.");
    return;
  }

  btnImportConfirm.disabled = true;
  btnImportConfirm.textContent = "Importando...";

  const formData = new FormData();
  formData.append("file", file);
  formData.append("sheet_name", sheetNameInput.value || "Sheet1");

  try {
    const res = await fetch(`${API}/import-excel`, {
      method: "POST",
      body: formData,
    });
    const json = await res.json();

    if (res.ok) {
      const j = json.job;
      showImportResult(
        "success",
        `✅ ${json.message} (${j.rows_inserted} ok, ${j.rows_failed} fallidas)`
      );
      addMessage("bot", `<p>📥 Excel importado: <strong>${j.file_name}</strong> — ${j.rows_inserted} filas procesadas.</p>`);
    } else {
      showImportResult("error", `❌ ${json.detail || "Error desconocido"}`);
    }
  } catch (err) {
    showImportResult("error", "❌ No se pudo conectar con el servidor.");
  }

  btnImportConfirm.disabled = false;
  btnImportConfirm.textContent = "Importar";
});

function showImportResult(type, msg) {
  importResult.className = `import-result ${type}`;
  importResult.textContent = msg;
}

// --- Envío por teclado ---

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(chatInput.value);
  }
});

btnSend.addEventListener("click", () => sendMessage(chatInput.value));

// --- Sugerencias clicables ---

messagesEl.addEventListener("click", (e) => {
  if (e.target.tagName === "EM") {
    chatInput.value = e.target.textContent;
    chatInput.focus();
  }
});

// --- Inicialización ---
checkHealth();
setInterval(checkHealth, 30000);
