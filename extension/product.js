// ============================================================
// BUY ME NOT - AMAZON PRODUCT EXTRACTOR
// ============================================================


// ============================================================
// BRAND GUESS
// ============================================================

function extractBrandGuess(title) {

    return title
        .split(" ")
        .slice(0, 2)
        .join(" ")
        .toLowerCase();

}


// ============================================================
// GET TEXT FROM FIRST MATCHING SELECTOR
// ============================================================

function getText(selectors) {

    for (const selector of selectors) {

        const element =
            document.querySelector(selector);

        if (element) {

            const text =
                element.innerText ||
                element.textContent;

            if (text && text.trim()) {

                return text.trim();
            }
        }
    }

    return null;
}


// ============================================================
// GET ATTRIBUTE FROM FIRST MATCHING SELECTOR
// ============================================================

function getAttribute(
    selectors,
    attribute
) {

    for (const selector of selectors) {

        const element =
            document.querySelector(selector);

        if (element) {

            const value =
                element.getAttribute(attribute);

            if (value && value.trim()) {

                return value.trim();
            }
        }
    }

    return null;
}


// ============================================================
// CONVERT PRICE TEXT TO NUMBER
// ============================================================

function parsePrice(value) {

    if (!value) {

        return null;
    }

    const cleaned =
        value
            .replace(/,/g, "")
            .replace(/[^\d.]/g, "");

    const number =
        parseFloat(cleaned);

    if (isNaN(number)) {

        return null;
    }

    return number;
}


// ============================================================
// GET AMAZON PRICE
// ============================================================

function getAmazonPrice() {

    // --------------------------------------------------------
    // Normal Amazon price
    // --------------------------------------------------------

    const offscreenPrice =
        getText([
            ".a-price .a-offscreen",
            "#corePriceDisplay_desktop_feature_div .a-offscreen",
            "#corePriceDisplay_mobile_feature_div .a-offscreen",
            ".priceToPay .a-offscreen"
        ]);

    if (offscreenPrice) {

        return offscreenPrice;
    }


    // --------------------------------------------------------
    // Fallback for pages where a-offscreen is empty
    // --------------------------------------------------------

    const wholeElement =
        document.querySelector(
            ".a-price .a-price-whole"
        );

    if (wholeElement) {

        const whole =
            wholeElement.innerText
                .replace(/[^\d]/g, "")
                .trim();

        const fractionElement =
            wholeElement.parentElement
                ?.querySelector(
                    ".a-price-fraction"
                );

        const fraction =
            fractionElement?.innerText
                ?.replace(/[^\d]/g, "")
                .trim();

        if (whole) {

            if (fraction) {

                return `₹${whole}.${fraction}`;
            }

            return `₹${whole}`;
        }
    }


    // --------------------------------------------------------
    // Additional Amazon price fallbacks
    // --------------------------------------------------------

    const fallbackPrice =
        getText([
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            ".reinventPricePriceToPayMargin",
            ".priceToPay"
        ]);

    if (fallbackPrice) {

        return fallbackPrice;
    }


    return "Price not found";
}


// ============================================================
// GET DISCOUNT PERCENT
// ============================================================

function getDiscountPercent() {

    const discountText =
        getText([
            ".savingsPercentage",
            "#dealprice_savings",
            ".a-price .a-price-discount"
        ]);

    if (discountText) {

        const match =
            discountText.match(
                /(\d+(?:\.\d+)?)\s*%/
            );

        if (match) {

            return parseFloat(
                match[1]
            );
        }
    }


    // --------------------------------------------------------
    // Try calculating discount from current and original price
    // --------------------------------------------------------

    const currentPriceText =
        getAmazonPrice();

    const originalPriceText =
        getText([
            ".a-text-price .a-offscreen",
            "#priceblock_listprice",
            ".basisPrice .a-offscreen",
            ".a-price.a-text-price .a-offscreen"
        ]);

    const currentPrice =
        parsePrice(
            currentPriceText
        );

    const originalPrice =
        parsePrice(
            originalPriceText
        );

    if (
        currentPrice !== null
        && originalPrice !== null
        && originalPrice > currentPrice
    ) {

        return Number(
            (
                (
                    originalPrice -
                    currentPrice
                )
                / originalPrice
                * 100
            ).toFixed(2)
        );
    }


    // Discount was not exposed by the page.
    return null;
}


// ============================================================
// GET PRODUCT INFORMATION
// ============================================================

function getProductInfo() {

    // --------------------------------------------------------
    // PRODUCT NAME
    // --------------------------------------------------------

    const name =
        getText([
            "#productTitle",
            "#title",
            "h1"
        ])
        || "Product name not found";


    // --------------------------------------------------------
    // PRICE
    // --------------------------------------------------------

    const price =
        getAmazonPrice();

    const productPrice =
        parsePrice(price);


    // --------------------------------------------------------
    // RATING
    // --------------------------------------------------------

    const rating =
        getText([
            "#acrPopover",
            "[data-hook='rating-out-of-text']",
            ".a-icon-alt"
        ])
        || "Rating not found";

    let productRating = null;

    const ratingMatch =
        rating.match(
            /(\d+(?:\.\d+)?)/
        );

    if (ratingMatch) {

        productRating =
            parseFloat(
                ratingMatch[1]
            );
    }


    // --------------------------------------------------------
    // REVIEW COUNT
    // --------------------------------------------------------

    const reviewCount =
        getText([
            "#acrCustomerReviewText",
            "[data-hook='total-review-count']",
            "#averageCustomerReviews_feature_div #acrCustomerReviewText"
        ])
        || "Review count not found";


    // --------------------------------------------------------
    // ASIN
    // --------------------------------------------------------

    const asinFromInput =
        document.querySelector(
            'input[name="ASIN"]'
        )?.value;

    const asinFromUrl =
        (
            window.location.pathname.match(
                /\/dp\/([A-Z0-9]{10})/i
            )
            || []
        )[1];

    const asin =
        asinFromInput
        || asinFromUrl
        || "ASIN not found";


    // --------------------------------------------------------
    // SPECIFICATIONS
    // --------------------------------------------------------

    let specifications =
        getText([
            "#productOverview_feature_div",
            "#detailBullets_feature_div",
            "#prodDetails",
            "#productDetails_feature_div",
            "#technicalSpecifications_feature_div"
        ]);


    // --------------------------------------------------------
    // FALLBACK: AMAZON TECHNICAL DETAILS
    // --------------------------------------------------------

    if (!specifications) {

        const rows =
            Array.from(
                document.querySelectorAll(
                    "#productDetails_techSpec_section_1 tr, " +
                    "#productDetails_detailBullets_sections1 tr, " +
                    "#detailBullets_feature_div li"
                )
            );

        const extractedRows =
            rows
                .map(row => {

                    const text =
                        row.innerText ||
                        row.textContent;

                    return text
                        ? text.trim()
                        : "";

                })
                .filter(Boolean);

        if (
            extractedRows.length > 0
        ) {

            specifications =
                extractedRows.join("\n");
        }
    }


    if (!specifications) {

        specifications =
            "Specifications not found";
    }


    // --------------------------------------------------------
    // BRAND
    // --------------------------------------------------------

    const brand =
        getText([
            "#bylineInfo",
            "#brand",
            "tr.po-brand td"
        ])
        ?.replace(
            /visit the|store|brand:/gi,
            ""
        )
        .trim()
        || extractBrandGuess(name);


    // --------------------------------------------------------
    // CATEGORY
    // --------------------------------------------------------

    const category =
        getText([
            "#wayfinding-breadcrumbs_feature_div",
            "#wayfinding-breadcrumbs_container"
        ])
        ?.replace(
            /\s+/g,
            " "
        )
        .trim()
        || null;


    // --------------------------------------------------------
    // NORMALIZED PRODUCT CATEGORY
    // --------------------------------------------------------

    const productCategory =
        category
        ? category
            .split(">")
            .pop()
            .trim()
            .toLowerCase()
        : null;


    // --------------------------------------------------------
    // DISCOUNT
    // --------------------------------------------------------

    const discountPercent =
        getDiscountPercent();


    // --------------------------------------------------------
    // REVIEWS
    // --------------------------------------------------------

    const reviews =
        Array.from(
            document.querySelectorAll(
                '[data-hook="review"]'
            )
        )
        .map(review => {

            const title =
                review.querySelector(
                    '[data-hook="review-title"]'
                )?.innerText.trim()
                || review.querySelector(
                    '[data-hook="reviewTitle"]'
                )?.innerText.trim()
                || "";

            const text =
                review.innerText.trim();

            return {
                title,
                text
            };

        });


    // --------------------------------------------------------
    // RETURN PRODUCT DATA
    // --------------------------------------------------------

    return {

        name,

        title: name,

        price,

        product_price:
            productPrice,

        rating,

        product_rating:
            productRating,

        discount_percent:
            discountPercent,

        reviewCount,

        asin,

        brand,

        category,

        product_category:
            productCategory,

        specifications,

        reviews,

        url:
            window.location.href
    };
}


// ============================================================
// MESSAGE LISTENER
// ============================================================

chrome.runtime.onMessage.addListener(
    (
        message,
        sender,
        sendResponse
    ) => {

        if (
            message.type ===
            "GET_PRODUCT_INFO"
        ) {

            sendResponse(
                getProductInfo()
            );
        }

        return true;
    }
);


// ============================================================
// DEBUG MESSAGE
// ============================================================

console.log(
    "BuyMeNot AI - Amazon product extractor ready"
);