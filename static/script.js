const API = "/api/projects";
const grid = document.getElementById("grid");
const empty = document.getElementById("empty");
const search = document.getElementById("search");
const filters = document.getElementById("filters");
const dialog = document.getElementById("formDialog");
const form = document.getElementById("projectForm");
const formError = document.getElementById("formError");

let projects = [];
let activeCategory = "All";

const esc = (s = "") =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function loadProjects() {
  const res = await fetch(API);
  projects = await res.json();
  renderStats();
  renderFilters();
  render();
}

function renderStats() {
  const tech = new Set(projects.flatMap((p) => p.tech_stack.map((t) => t.toLowerCase())));
  document.getElementById("statTotal").textContent = projects.length;
  document.getElementById("statDone").textContent = projects.filter((p) => p.status === "Completed").length;
  document.getElementById("statTech").textContent = tech.size;
}

function renderFilters() {
  const cats = ["All", ...new Set(projects.map((p) => p.category).filter(Boolean))];
  if (!cats.includes(activeCategory)) activeCategory = "All";
  filters.innerHTML = cats
    .map((c) => `<button class="chip ${c === activeCategory ? "active" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`)
    .join("");
}

function render() {
  const q = search.value.trim().toLowerCase();
  const list = projects.filter((p) => {
    const inCat = activeCategory === "All" || p.category === activeCategory;
    const text = `${p.title} ${p.description} ${p.tech_stack.join(" ")}`.toLowerCase();
    return inCat && (!q || text.includes(q));
  });
  empty.hidden = list.length > 0;
  grid.innerHTML = list
    .map(
      (p) => `
    <article class="card">
      <div class="card-top"><span>${esc(p.category)}</span><span class="badge ${esc(p.status)}">${esc(p.status)}</span></div>
      <h3>${esc(p.title)}</h3>
      <p>${esc(p.description)}</p>
      <div class="tags">${p.tech_stack.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}</div>
      <div class="card-links">
        ${p.github_url ? `<a href="${esc(p.github_url)}" target="_blank" rel="noopener">GitHub ↗</a>` : ""}
        ${p.live_url ? `<a href="${esc(p.live_url)}" target="_blank" rel="noopener">Live ↗</a>` : ""}
        <button class="del" data-id="${p.id}">Delete</button>
      </div>
    </article>`
    )
    .join("");
}

filters.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  activeCategory = btn.dataset.cat;
  renderFilters();
  render();
});
search.addEventListener("input", render);

grid.addEventListener("click", async (e) => {
  const btn = e.target.closest(".del");
  if (!btn || !confirm("Delete this project?")) return;
  const key = form.admin_key.value || prompt("Admin key (leave empty if none):") || "";
  const res = await fetch(`${API}/${btn.dataset.id}`, { method: "DELETE", headers: { "X-Admin-Key": key } });
  if (!res.ok) return alert((await res.json()).error || "Delete failed");
  loadProjects();
});

document.getElementById("openForm").addEventListener("click", () => {
  formError.textContent = "";
  dialog.showModal();
});
document.getElementById("cancelForm").addEventListener("click", () => dialog.close());

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  const key = data.admin_key;
  delete data.admin_key;
  const res = await fetch(API, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Key": key },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    formError.textContent = (await res.json()).error || "Could not save project";
    return;
  }
  form.reset();
  form.admin_key.value = key;
  dialog.close();
  loadProjects();
});

document.getElementById("year").textContent = new Date().getFullYear();
loadProjects();
