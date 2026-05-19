const countrySelect = document.getElementById("country-select");
const loadReportButton = document.getElementById("load-report");
const stickerInput = document.getElementById("sticker-input");
const saveStickersButton = document.getElementById("save-stickers");
const reportOutput = document.getElementById("report-output");
const saveStatus = document.getElementById("save-status");

async function apiFetch(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    throw new Error(data.detail || data || response.statusText);
  }
  return data;
}

function formatReport(data) {
  const dupEntries = Object.entries(data.duplicates || {});
  const dupText = dupEntries.length > 0 ? dupEntries.map(([id, count]) => `${id} (x${count})`).join(", ") : "none";

  return [
    `Country: ${data.country}`,
    `Completion: ${data.completion_percentage}%`,
    `Found: ${data.counts.found}`,
    `Missing: ${data.counts.missing}`,
    "",
    `Missing: ${data.missing.join(", ") || "none"}`,
    `Duplicates: ${dupText}`,
  ].join("\n");
}

function showMessage(message, type = "success") {
  saveStatus.textContent = message;
  saveStatus.className = `status ${type}`;
}

async function loadCountries() {
  try {
    const data = await apiFetch("/countries");
    countrySelect.innerHTML = data.countries.map(code => `<option value="${code}">${code}</option>`).join("");
  } catch (error) {
    reportOutput.textContent = `Error loading countries: ${error.message}`;
  }
}

async function loadReport() {
  const countryCode = countrySelect.value;
  if (!countryCode) {
    return;
  }

  try {
    const data = await apiFetch(`/inventory/${countryCode}`);
    reportOutput.textContent = formatReport(data);
    showMessage("Report loaded.", "success");
  } catch (error) {
    reportOutput.textContent = `Error: ${error.message}`;
    showMessage("Could not load report.", "error");
  }
}

async function saveStickers() {
  const countryCode = countrySelect.value;
  const stickersText = stickerInput.value.trim();
  if (!countryCode || !stickersText) {
    showMessage("Enter a country and sticker list.", "error");
    return;
  }

  try {
    const payload = { stickers: stickersText };
    const data = await apiFetch(`/inventory/${countryCode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    reportOutput.textContent = formatReport(data);
    showMessage("Stickers saved successfully.", "success");
    stickerInput.value = "";
  } catch (error) {
    showMessage(error.message, "error");
  }
}

loadCountries();
loadReportButton.addEventListener("click", loadReport);
saveStickersButton.addEventListener("click", saveStickers);
