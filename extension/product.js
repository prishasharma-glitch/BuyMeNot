function extractBrandGuess(title) {
  return title.split(" ").slice(0, 2).join(" ").toLowerCase();
}

function getProductInfo() {
  const name =
    document.querySelector("#productTitle")?.innerText.trim()
    || "Product name not found";

  const price =
    document.querySelector(".a-price .a-offscreen")?.innerText.trim()
    || document.querySelector("#priceblock_ourprice")?.innerText.trim()
    || "Price not found";

  const rating =
    document.querySelector("#acrPopover")?.innerText.trim()
    || "Rating not found";

  const reviewCount =
    document.querySelector("#acrCustomerReviewText")?.innerText.trim()
    || "Review count not found";

  const asinFromInput = document.querySelector('input[name="ASIN"]')?.value;
  const asinFromUrl = (window.location.pathname.match(/\/dp\/([A-Z0-9]+)/) || [])[1];
  const asin = asinFromInput || asinFromUrl || "ASIN not found";

  const specifications =
    document.querySelector("#productOverview_feature_div")?.innerText.trim()
    || "Specifications not found";

  const brand =
    document.querySelector("#bylineInfo")?.innerText.replace(/visit the|store|brand:/gi, "").trim()
    || extractBrandGuess(name);

  const category =
    document.querySelector("#wayfinding-breadcrumbs_feature_div")?.innerText.replace(/\s+/g, " ").trim()
    || null;

  const reviews = Array.from(
    document.querySelectorAll('[data-hook="review"]')
  ).map(review => ({
    title: review.querySelector('[data-hook="reviewTitle"]')?.innerText.trim() || "",
    text: review.innerText.trim()
  }));

  return {
    name,
    title: name,        // alias, used by the local order-history matcher
    price,
    rating,
    reviewCount,
    asin,
    brand,
    category,
    specifications,
    reviews,
    url: window.location.href
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_PRODUCT_INFO") {
    sendResponse(getProductInfo());
  }
  return true;
});

console.log("BuyMeNot AI - product page listener ready");