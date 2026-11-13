const API_BASE = window.location.origin;

// State
let activeUser = "alvin_ai";
let activePersona = "AI / ML Engineer";
let activeStrategy = "HYBRID";
let catalogItems = [];

// Default Seed Catalog
const SEED_CATALOG = [
  {
    title: "Deep Reinforcement Learning in Robotics",
    category: "Artificial Intelligence",
    description: "Policy gradient algorithms, actor-critic architectures, and sim-to-real robotic control transfer.",
    tags: "ai, reinforcement-learning, robotics, neural-networks",
    price: 59.99,
    avg_rating: 4.9
  },
  {
    title: "Transformers & LLM Attention Mechanics",
    category: "Artificial Intelligence",
    description: "Multi-head self-attention, rotary positional embeddings, and memory-efficient FlashAttention implementations.",
    tags: "ai, llm, transformers, deep-learning, nlp",
    price: 64.99,
    avg_rating: 4.8
  },
  {
    title: "Distributed Consensus & Raft Protocol",
    category: "Cloud Architecture",
    description: "Understanding leader election, log replication safety invariants, and fault-tolerant cluster storage.",
    tags: "cloud, distributed-systems, raft, golang",
    price: 49.99,
    avg_rating: 4.9
  },
  {
    title: "High-Throughput Kafka Event Streaming",
    category: "Cloud Architecture",
    description: "Partitioning strategies, consumer group rebalancing, and exactly-once processing guarantees.",
    tags: "cloud, kafka, streaming, architecture",
    price: 44.99,
    avg_rating: 4.7
  },
  {
    title: "Automated Market Making in DeFi",
    category: "FinTech",
    description: "Constant product formula, impermanent loss, and arbitrage mechanics in decentralized liquidity pools.",
    tags: "fintech, defi, crypto, trading",
    price: 69.99,
    avg_rating: 4.8
  },
  {
    title: "Zero-Trust Cybersecurity & Microsegmentation",
    category: "Cybersecurity",
    description: "Continuous identity assertion, mutual TLS, and dynamic network policy enforcement.",
    tags: "cybersecurity, zerotrust, identity, network",
    price: 54.99,
    avg_rating: 4.6
  }
];

// DOM Elements
const metricItems = document.getElementById("metric-items");
const metricUsers = document.getElementById("metric-users");
const metricInteractions = document.getElementById("metric-interactions");
const metricLatency = document.getElementById("metric-latency");

const personaChips = document.getElementById("persona-chips");
const strategySelect = document.getElementById("strategy-select");
const recoSubtitle = document.getElementById("reco-subtitle");
const recoShelf = document.getElementById("reco-shelf");
const btnRefreshReco = document.getElementById("btn-refresh-reco");

const categoryFilter = document.getElementById("category-filter");
const catalogGrid = document.getElementById("catalog-grid");

const btnToggleAdd = document.getElementById("btn-toggle-add");
const addModal = document.getElementById("add-modal");
const btnCloseModal = document.getElementById("btn-close-modal");
const btnCancelAdd = document.getElementById("btn-cancel-add");
const addItemForm = document.getElementById("add-item-form");

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadAnalytics();
  initCatalogAndRecommendations();
});

function setupEventListeners() {
  // Persona switcher
  document.querySelectorAll(".btn-persona").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".btn-persona").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeUser = btn.dataset.user;
      activePersona = btn.dataset.persona;
      recoSubtitle.textContent = `Personalized feed for ${activePersona} (${activeUser})`;
      loadRecommendations();
    });
  });

  strategySelect.addEventListener("change", (e) => {
    activeStrategy = e.target.value;
    loadRecommendations();
  });

  btnRefreshReco.addEventListener("click", loadRecommendations);

  categoryFilter.addEventListener("change", (e) => {
    const cat = e.target.value;
    filterCatalog(cat);
  });

  // Modal
  btnToggleAdd.addEventListener("click", () => addModal.classList.remove("hidden"));
  btnCloseModal.addEventListener("click", () => addModal.classList.add("hidden"));
  btnCancelAdd.addEventListener("click", () => addModal.classList.add("hidden"));
  addItemForm.addEventListener("submit", handleAddItemSubmit);
}

async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/api/analytics/reco-metrics`);
    if (!res.ok) return;
    const data = await res.json();
    metricItems.textContent = data.total_items;
    metricUsers.textContent = data.total_users;
    metricInteractions.textContent = data.total_interactions;
    metricLatency.textContent = `${data.avg_latency_ms} ms`;
  } catch (err) {
    console.error("Metrics fetch error:", err);
  }
}

async function initCatalogAndRecommendations() {
  try {
    const res = await fetch(`${API_BASE}/api/items`);
    if (!res.ok) throw new Error("Catalog fetch failed");
    catalogItems = await res.json();

    // Auto-seed if catalog is empty
    if (catalogItems.length === 0) {
      await autoSeedCatalog();
      const ref = await fetch(`${API_BASE}/api/items`);
      catalogItems = await ref.json();
    }

    renderCatalog(catalogItems);
    await loadRecommendations();
  } catch (err) {
    catalogGrid.innerHTML = `<div style="color:var(--text-secondary);padding:1rem;">Failed to load catalog.</div>`;
  }
}

async function autoSeedCatalog() {
  for (const item of SEED_CATALOG) {
    await fetch(`${API_BASE}/api/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item)
    });
  }

  // Seed baseline interactions for Alvin and Sophia so collaborative matrix is populated
  const res = await fetch(`${API_BASE}/api/items`);
  const items = await res.json();
  if (items.length >= 4) {
    await fetch(`${API_BASE}/api/interactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "alvin_ai", item_id: items[0].id, interaction_type: "PURCHASE" })
    });
    await fetch(`${API_BASE}/api/interactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "peer_user_1", item_id: items[0].id, interaction_type: "PURCHASE" })
    });
    await fetch(`${API_BASE}/api/interactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "peer_user_1", item_id: items[1].id, interaction_type: "PURCHASE" })
    });
    await fetch(`${API_BASE}/api/interactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "sophia_devops", item_id: items[2].id, interaction_type: "PURCHASE" })
    });
  }
  await loadAnalytics();
}

async function loadRecommendations() {
  recoShelf.innerHTML = `<div class="shelf-loading" style="padding:1.5rem;color:var(--text-secondary);">Recalculating neural weights...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/recommendations/${activeUser}?strategy=${activeStrategy}&beta=0.6&top_k=4`);
    if (!res.ok) throw new Error("Recommendations failed");
    const data = await res.json();
    renderRecommendations(data.recommendations);
    await loadAnalytics();
  } catch (err) {
    recoShelf.innerHTML = `<div style="color:var(--text-secondary);padding:1rem;">No recommendations generated.</div>`;
  }
}

function renderRecommendations(recs) {
  if (recs.length === 0) {
    recoShelf.innerHTML = `<div style="color:var(--text-secondary);padding:1rem;">No personalized recommendations found. Try interacting with catalog items below.</div>`;
    return;
  }

  recoShelf.innerHTML = recs.map(r => `
    <div class="reco-card">
      <div>
        <div class="reco-badge-row">
          <span class="score-pill">${(r.score * 100).toFixed(0)}% Affinity</span>
          <span class="strategy-tag">${escapeHtml(r.strategy)}</span>
        </div>
        <div class="reco-title">${escapeHtml(r.title)}</div>
        <div class="reco-desc">${escapeHtml(r.description)}</div>
      </div>
      <div>
        <div class="reco-explanation">${escapeHtml(r.explanation)}</div>
        <div class="reco-footer">
          <span class="price">$${r.price.toFixed(2)}</span>
          <span style="color:var(--accent-amber);">★ ${r.avg_rating.toFixed(1)}</span>
        </div>
      </div>
    </div>
  `).join("");
}

function renderCatalog(items) {
  if (items.length === 0) {
    catalogGrid.innerHTML = `<div style="color:var(--text-secondary);padding:1rem;">No items in category.</div>`;
    return;
  }

  catalogGrid.innerHTML = items.map(it => `
    <div class="item-card">
      <div>
        <div class="item-top">
          <span>${escapeHtml(it.category)}</span>
          <span style="color:var(--accent-amber);">★ ${it.avg_rating.toFixed(1)}</span>
        </div>
        <div class="item-title">${escapeHtml(it.title)}</div>
        <div class="item-desc">${escapeHtml(it.description)}</div>
      </div>
      <div>
        <div style="font-size:0.75rem; color:var(--text-dim); margin-bottom:0.5rem;">$${it.price.toFixed(2)}</div>
        <div class="action-bar">
          <button class="btn-action" onclick="recordInteraction('${it.id}', 'VIEW')">👁 View</button>
          <button class="btn-action" onclick="recordInteraction('${it.id}', 'BOOKMARK')">🔖 Save</button>
          <button class="btn-action" onclick="recordInteraction('${it.id}', 'RATING')">⭐ Rate</button>
          <button class="btn-action purchase" onclick="recordInteraction('${it.id}', 'PURCHASE')">💳 Buy</button>
        </div>
      </div>
    </div>
  `).join("");
}

function filterCatalog(category) {
  if (!category) {
    renderCatalog(catalogItems);
  } else {
    const filtered = catalogItems.filter(i => i.category === category);
    renderCatalog(filtered);
  }
}

async function recordInteraction(itemId, type) {
  try {
    const res = await fetch(`${API_BASE}/api/interactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: activeUser,
        item_id: itemId,
        interaction_type: type
      })
    });

    if (res.ok) {
      // Re-query recommendations immediately
      await loadRecommendations();
      await loadAnalytics();
    }
  } catch (err) {
    console.error("Interaction failed:", err);
  }
}

async function handleAddItemSubmit(e) {
  e.preventDefault();
  const title = document.getElementById("item-title").value.trim();
  const category = document.getElementById("item-cat").value.trim();
  const price = parseFloat(document.getElementById("item-price").value) || 0.0;
  const tags = document.getElementById("item-tags").value.trim();
  const description = document.getElementById("item-desc").value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, category, price, tags, description })
    });

    if (res.ok) {
      addModal.classList.add("hidden");
      addItemForm.reset();
      await initCatalogAndRecommendations();
      await loadAnalytics();
    }
  } catch (err) {
    alert("Failed to add catalog item");
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
