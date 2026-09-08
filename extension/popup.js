// ---------- YOUR LOCAL ORDER-HISTORY MATCHING ----------

function extractBrandGuess(title) {
  return title.split(" ").slice(0, 2).join(" ").toLowerCase();
}

function scoreAgainstOrderHistory(product, orders) {
  const productBrand = (product.brand || extractBrandGuess(product.title)).toLowerCase();
  let riskySignals = 0;
  let safeSignals = 0;
  let matchDetails = [];

  orders.forEach((order) => {
    order.products.forEach((item) => {
      if (!item.title) return;
      const itemBrandGuess = extractBrandGuess(item.title);
      const brandMatch = productBrand.includes(itemBrandGuess) || itemBrandGuess.includes(productBrand);
      if (brandMatch) {
        if (item.likelyReturned) {
          riskySignals++;
          matchDetails.push(`Returned: ${item.title.slice(0, 40)}...`);
        } else {
          safeSignals++;
          matchDetails.push(`Kept: ${item.title.slice(0, 40)}...`);
        }
      }
    });
  });

  return { riskySignals, safeSignals, matchDetails };
}

function renderPersonalVerdict(product) {
  const el = document.getElementById("personalVerdictResult");
  chrome.storage.local.get("buymenot_orders", (data) => {
    const orders = data.buymenot_orders || [];
    if (orders.length === 0) {
      el.innerHTML = `<span class="negative">No order history synced yet.</span> Use Sync above first.`;
      return;
    }
    const { riskySignals, safeSignals, matchDetails } = scoreAgainstOrderHistory(product, orders);
    let verdict;
    if (riskySignals > safeSignals) {
      verdict = `<span class="negative">⚠ Possible regret risk</span> — similar brand items were returned/replaced before.`;
    } else if (safeSignals > 0) {
      verdict = `<span class="positive">✔ Looks like a safe pick</span> — similar brand items were kept before.`;
    } else {
      verdict = `No strong match with your past orders.`;
    }
    const details = matchDetails.length ? `<br><small>${matchDetails.slice(0, 3).join("<br>")}</small>` : "";
    el.innerHTML = `${verdict}${details}`;
  });
}

// ---------- SYNC BUTTON ----------

function updateSyncStatusDisplay() {
  const el = document.getElementById("syncStatus");
  chrome.storage.local.get("buymenot_orders", (data) => {
    const orders = data.buymenot_orders || [];
    el.textContent = orders.length > 0
      ? `✔ Synced: ${orders.length} orders saved.`
      : "Not synced yet.";
  });
}

document.getElementById("syncBtn").addEventListener("click", () => {
  const el = document.getElementById("syncStatus");
  el.textContent = "Starting sync...";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    const url = tab.url || "";
    const isOrdersPage = url.includes("/your-orders") || url.includes("/gp/css/order-history");

    if (!isOrdersPage) {
      el.innerHTML = `<span class="negative">Go to your Amazon Orders page first</span>, then click Sync.`;
      return;
    }

    chrome.tabs.sendMessage(tab.id, { type: "START_SYNC" }, (response) => {
      if (chrome.runtime.lastError || !response || !response.ok) {
        el.innerHTML = `<span class="negative">Couldn't start sync.</span> Try refreshing the orders page.`;
        return;
      }
      el.textContent = "Syncing... this may take a minute.";
    });
  });
});

// ---------- ANALYZE BUTTON ----------

document.getElementById("analyzeButton").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.tabs.sendMessage(tab.id, { type: "GET_PRODUCT_INFO" }, async (response) => {
    if (chrome.runtime.lastError || !response) {
      document.getElementById("status").innerText = "Unable to read this page.";
      return;
    }

    const userRequirements = {
      needs_oven_safe: document.getElementById("needsOvenSafe").checked,
      needs_induction: document.getElementById("needsInduction").checked
    };

    document.getElementById("productName").innerText = response.name;
    document.getElementById("productPrice").innerText = response.price;
    document.getElementById("productRating").innerText = response.rating;
    document.getElementById("reviewCount").innerText = response.reviewCount;
    document.getElementById("productAsin").innerText = response.asin;

    // Run your local personal fit check immediately (doesn't need backend)
    renderPersonalVerdict(response);

    const requestData = { ...response, user_requirements: userRequirements };

    try {
      document.getElementById("status").innerText = "Analyzing product...";

      const backendResponse = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData)
      });

      const result = await backendResponse.json();
      console.log("Backend analysis:", result);

      if (result.error) {
        document.getElementById("status").innerText = result.error;
        document.getElementById("analysisResults").innerText = "AI analysis is temporarily unavailable.";
        return;
      }

      // Compatibility
      const compatibilityResults = document.getElementById("compatibilityResults");
      compatibilityResults.innerHTML = "";
      result.compatibility.forEach(item => {
        const card = document.createElement("div");
        card.className = "aspect-card";
        let statusSymbol = "⚠️", statusClass = "neutral";
        if (item.status === "pass") { statusSymbol = "✅"; statusClass = "positive"; }
        else if (item.status === "fail") { statusSymbol = "❌"; statusClass = "negative"; }
        card.innerHTML = `
          <div class="aspect-header">
            <strong>${statusSymbol} ${item.requirement}</strong>
            <span class="${statusClass}">${item.status.toUpperCase()}</span>
          </div>
          <p class="reason">${item.message}</p>
        `;
        compatibilityResults.appendChild(card);
      });

      // AI review analysis
      const analysisResults = document.getElementById("analysisResults");
      analysisResults.innerHTML = "";
      result.analysis.aspects.forEach(item => {
        const card = document.createElement("div");
        card.className = "aspect-card";
        const sentimentClass = item.sentiment === "positive" ? "positive" : item.sentiment === "negative" ? "negative" : "neutral";
        const evidenceHTML = item.evidence && item.evidence.length > 0
          ? `<div class="evidence"><strong>Evidence:</strong><ul>${item.evidence.map(e => `<li>${e}</li>`).join("")}</ul></div>`
          : "";
        card.innerHTML = `
          <div class="aspect-header">
            <strong>${item.aspect}</strong>
            <span class="${sentimentClass}">${item.sentiment.toUpperCase()}</span>
          </div>
          <p class="reason">${item.reason}</p>
          ${evidenceHTML}
        `;
        analysisResults.appendChild(card);
      });

      document.getElementById("status").innerText = "Analysis complete!";

    } catch (error) {
      console.error("Backend error:", error);
      document.getElementById("status").innerText = "Could not connect to backend.";
      document.getElementById("analysisResults").innerText = "Backend is unavailable.";
    }
  });
});

updateSyncStatusDisplay();