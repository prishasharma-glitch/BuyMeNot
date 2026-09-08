function isOrdersPage() {
  return window.location.pathname.startsWith("/your-orders") ||
         window.location.pathname.startsWith("/gp/css/order-history");
}

function scrapeCurrentPageOrders() {
  const orderCards = document.querySelectorAll(".order-card.js-order-card");
  const orders = [];

  orderCards.forEach((card) => {
    const header = card.querySelector(".order-header");
    if (!header) return;

    const orderIdEl = header.querySelector(".yohtmlc-order-id span:last-child");
    const orderId = orderIdEl ? orderIdEl.textContent.trim() : null;

    let orderDate = null;
    let total = null;
    header.querySelectorAll(".order-header__header-list-item").forEach((block) => {
      const label = block.querySelector(".a-text-caps");
      const value = block.querySelector(".a-row:nth-child(2) span");
      if (!label || !value) return;
      const labelText = label.textContent.trim().toLowerCase();
      if (labelText.includes("order placed")) orderDate = value.textContent.trim();
      if (labelText.includes("total")) total = value.textContent.trim();
    });

    const products = [];
    card.querySelectorAll(".delivery-box").forEach((box) => {
      const statusEl = box.querySelector(".yohtmlc-shipment-status-primaryText span");
      const shipmentStatus = statusEl ? statusEl.textContent.trim() : null;

      const boxText = box.textContent.toLowerCase();
      const hasReturnStatusButton = boxText.includes("return/refund status") ||
                                     boxText.includes("refund status");
      const statusSuggestsReturn = shipmentStatus ? /replac|return/i.test(shipmentStatus) : false;
      const likelyReturned = hasReturnStatusButton || statusSuggestsReturn;

      box.querySelectorAll(".yohtmlc-product-title").forEach((item) => {
        const link = item.querySelector("a");
        if (!link) return;
        const title = link.textContent.trim();
        const href = link.getAttribute("href");
        const asinMatch = href.match(/\/dp\/([A-Z0-9]+)/);
        const asin = asinMatch ? asinMatch[1] : null;
        products.push({ title, asin, shipmentStatus, likelyReturned });
      });
    });

    orders.push({ orderId, orderDate, total, products });
  });

  return orders;
}

function getYearOptions() {
  const select = document.querySelector("#time-filter");
  if (!select) return [];
  return Array.from(select.options).map((opt) => opt.value);
}

function findNextPageUrl() {
  const nextLink = Array.from(document.querySelectorAll("a"))
    .find((el) => el.textContent.trim() === "Next" && el.offsetParent !== null);
  return nextLink ? nextLink.href : null;
}

const STORAGE_KEY = "buymenot_scrape_state";

function loadState(callback) {
  chrome.storage.local.get(STORAGE_KEY, (result) => {
    callback(result[STORAGE_KEY] || null);
  });
}

function saveState(state, callback) {
  chrome.storage.local.set({ [STORAGE_KEY]: state }, callback || (() => {}));
}

function navigateTo(url) {
  window.location.href = url;
}

function finishScrape(state) {
  const uniqueMap = new Map();
  state.allOrders.forEach((o) => { if (o.orderId) uniqueMap.set(o.orderId, o); });
  const uniqueOrders = Array.from(uniqueMap.values());

  console.log(`BuyMeNot AI - DONE. Total unique orders: ${uniqueOrders.length}`);

  chrome.storage.local.set({ buymenot_orders: uniqueOrders }, () => {
    console.log("BuyMeNot AI - saved final orders to chrome.storage.local");
  });
  chrome.storage.local.remove(STORAGE_KEY);
}

function step() {
  loadState((state) => {
    if (!state) {
      const years = getYearOptions();
      console.log("BuyMeNot AI - starting scrape. Years found:", years);
      state = { yearsQueue: years, yearIndex: 0, allOrders: [], scraping: true };
      saveState(state, () => proceedWithYear(state));
      return;
    }
    proceedWithYear(state);
  });
}

function proceedWithYear(state) {
  const pageOrders = scrapeCurrentPageOrders();
  state.allOrders.push(...pageOrders);
  console.log(`BuyMeNot AI - scraped ${pageOrders.length} orders from current page. Total so far: ${state.allOrders.length}`);

  const nextPageUrl = findNextPageUrl();
  if (nextPageUrl) {
    saveState(state, () => navigateTo(nextPageUrl));
    return;
  }

  state.yearIndex++;
  if (state.yearIndex >= state.yearsQueue.length) {
    finishScrape(state);
    return;
  }

  const nextYear = state.yearsQueue[state.yearIndex];
  saveState(state, () => {
    const url = `${window.location.origin}/your-orders/orders?timeFilter=${nextYear}`;
    navigateTo(url);
  });
}

if (isOrdersPage()) {
  loadState((state) => {
    if (state && state.scraping) {
      console.log("BuyMeNot AI - resuming in-progress scrape...");
      step();
    } else {
      console.log("BuyMeNot AI - orders page loaded. Waiting for user to trigger sync from popup.");
    }
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "START_SYNC") {
    if (!isOrdersPage()) {
      sendResponse({ ok: false, reason: "not_orders_page" });
      return true;
    }
    chrome.storage.local.remove(STORAGE_KEY, () => {
      chrome.storage.local.remove("buymenot_orders", () => {
        sendResponse({ ok: true });
        step();
      });
    });
    return true;
  }
});