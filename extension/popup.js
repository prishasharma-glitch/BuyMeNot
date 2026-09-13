// ============================================================
// BUY ME NOT POPUP
// ============================================================


// ============================================================
// USER PROFILE
// ============================================================

const userProfile = {
    customer_age: "",
    past_purchase_count: "",
    past_return_rate: "",
    session_length_minutes: "",
    num_product_views: "",
    device_type: "",
    shipping_method: "",
    payment_method: "",
    used_coupon: ""
};


// ============================================================
// PROFILE FIELD MAPPING
// ============================================================

const profileFields = {
    customer_age: "customerAge",
    past_purchase_count: "pastPurchaseCount",
    past_return_rate: "pastReturnRate",
    session_length_minutes: "sessionLength",
    num_product_views: "productViews",
    device_type: "deviceType",
    shipping_method: "shippingMethod",
    payment_method: "paymentMethod",
    used_coupon: "usedCoupon"
};


// ============================================================
// LOAD USER PROFILE
// ============================================================

async function loadUserProfile() {

    try {

        const stored =
            await chrome.storage.local.get(
                "userProfile"
            );

        if (
            stored.userProfile
        ) {

            Object.assign(
                userProfile,
                stored.userProfile
            );
        }

        // ----------------------------------------------------
        // UPDATE PURCHASE HISTORY FROM SYNCED AMAZON ORDERS
        // ----------------------------------------------------

        await updateProfileFromOrderHistory();

        Object.keys(profileFields).forEach(
            key => {

                const element =
                    document.getElementById(
                        profileFields[key]
                    );

                if (
                    element
                    && userProfile[key] !== ""
                ) {

                    element.value =
                        userProfile[key];
                }
            }
        );

    } catch (error) {

        console.error(
            "Could not load user profile:",
            error
        );
    }
}


// ============================================================
// UPDATE PROFILE FROM ORDER HISTORY
// ============================================================

async function updateProfileFromOrderHistory() {

    try {

        const stored =
            await chrome.storage.local.get(
                "buymenot_orders"
            );

        const orders =
            stored.buymenot_orders || [];

        if (!Array.isArray(orders) || orders.length === 0) {

            console.log(
                "No synced order history available."
            );

            return;
        }


        // ----------------------------------------------------
        // COUNT PURCHASED PRODUCTS
        // ----------------------------------------------------

        let purchaseCount = 0;
        let returnedCount = 0;

        orders.forEach(order => {

            const products =
                Array.isArray(order.products)
                    ? order.products
                    : [];

            products.forEach(product => {

                purchaseCount++;

                if (
                    product.likelyReturned === true
                ) {

                    returnedCount++;
                }
            });
        });


        // ----------------------------------------------------
        // CALCULATE RETURN RATE
        // ----------------------------------------------------

        let returnRate = 0;

        if (purchaseCount > 0) {

            returnRate =
                returnedCount / purchaseCount;
        }


        // ----------------------------------------------------
        // UPDATE PROFILE
        // ----------------------------------------------------

        userProfile.past_purchase_count =
            purchaseCount.toString();

        userProfile.past_return_rate =
            returnRate.toFixed(4);


        // ----------------------------------------------------
        // SAVE UPDATED PROFILE
        // ----------------------------------------------------

        await chrome.storage.local.set({
            userProfile: userProfile
        });


        console.log(
            "Profile updated from order history:",
            {
                purchaseCount,
                returnedCount,
                returnRate
            }
        );

    } catch (error) {

        console.error(
            "Could not update profile from order history:",
            error
        );
    }
}


// ============================================================
// SAVE USER PROFILE
// ============================================================

async function saveUserProfile() {

    Object.keys(profileFields).forEach(
        key => {

            const element =
                document.getElementById(
                    profileFields[key]
                );

            if (element) {

                userProfile[key] =
                    element.value;
            }
        }
    );

    try {

        await chrome.storage.local.set({
            userProfile: userProfile
        });

    } catch (error) {

        console.error(
            "Could not save user profile:",
            error
        );
    }
}


// ============================================================
// PROFILE INPUT LISTENERS
// ============================================================

Object.keys(profileFields).forEach(
    key => {

        const element =
            document.getElementById(
                profileFields[key]
            );

        if (element) {

            element.addEventListener(
                "change",
                saveUserProfile
            );
        }
    }
);


// ============================================================
// ORDER HISTORY SYNC
// ============================================================

document
    .getElementById("syncOrdersButton")
    .addEventListener(
        "click",
        async () => {

            const syncStatus =
                document.getElementById(
                    "orderSyncStatus"
                );

            syncStatus.innerText =
                "Starting order history sync...";

            try {

                const [tab] =
                    await chrome.tabs.query({
                        active: true,
                        currentWindow: true
                    });

                if (!tab || !tab.id) {

                    syncStatus.innerText =
                        "Could not find the active tab.";

                    return;
                }

                chrome.tabs.sendMessage(
                    tab.id,
                    {
                        type: "START_SYNC"
                    },
                    async response => {

                        if (
                            chrome.runtime.lastError
                        ) {

                            console.error(
                                "Order sync error:",
                                chrome.runtime.lastError
                            );

                            syncStatus.innerText =
                                "Please open Amazon Your Orders first.";

                            return;
                        }

                        if (
                            !response
                            || !response.ok
                        ) {

                            if (
                                response
                                && response.reason ===
                                "not_orders_page"
                            ) {

                                syncStatus.innerText =
                                    "Please open Amazon Your Orders first.";

                            } else {

                                syncStatus.innerText =
                                    "Could not start order sync.";
                            }

                            return;
                        }

                        syncStatus.innerText =
                            "Sync started. Please wait...";

                    }
                );

            } catch (error) {

                console.error(
                    "Order sync failed:",
                    error
                );

                syncStatus.innerText =
                    "Could not start order sync.";
            }
        }
    );


// ============================================================
// CHECK STORED ORDERS
// ============================================================

async function displayStoredOrderCount() {

    try {

        const stored =
            await chrome.storage.local.get(
                "buymenot_orders"
            );

        const orders =
            stored.buymenot_orders || [];

        const syncStatus =
            document.getElementById(
                "orderSyncStatus"
            );

        if (orders.length > 0) {

            syncStatus.innerText =
                `${orders.length} orders synced.`;

        }

    } catch (error) {

        console.error(
            "Could not load stored orders:",
            error
        );
    }
}


// ============================================================
// USER REQUIREMENTS
// ============================================================

const userRequirements = {};


// ============================================================
// DISPLAY REQUIREMENTS
// ============================================================

function displayRequirements() {

    const requirementsList =
        document.getElementById(
            "requirementsList"
        );

    requirementsList.innerHTML = "";

    const keys =
        Object.keys(userRequirements);

    if (keys.length === 0) {

        requirementsList.innerText =
            "No requirements added.";

        return;
    }

    keys.forEach(key => {

        const item =
            document.createElement("div");

        item.className =
            "aspect-card";

        item.innerHTML = `
            <strong>${key}</strong>

            <p>
                Required: ${userRequirements[key]}
            </p>
        `;

        requirementsList.appendChild(
            item
        );
    });
}


// ============================================================
// ADD REQUIREMENT
// ============================================================

document
    .getElementById("addRequirementButton")
    .addEventListener(
        "click",
        () => {

            const keyInput =
                document.getElementById(
                    "requirementKey"
                );

            const valueInput =
                document.getElementById(
                    "requirementValue"
                );

            const key =
                keyInput.value
                    .trim()
                    .toLowerCase()
                    .replace(/ /g, "_");

            const value =
                valueInput.value.trim();

            if (!key || !value) {

                return;
            }

            let convertedValue = value;

            if (
                value.toLowerCase() ===
                "true"
            ) {

                convertedValue = true;

            } else if (
                value.toLowerCase() ===
                "false"
            ) {

                convertedValue = false;

            } else if (
                !isNaN(value)
                && value !== ""
            ) {

                convertedValue =
                    Number(value);
            }

            userRequirements[key] =
                convertedValue;

            keyInput.value = "";
            valueInput.value = "";

            displayRequirements();
        }
    );


// ============================================================
// DISPLAY PRODUCT INFORMATION
// ============================================================

function displayProduct(response) {

    document.getElementById(
        "productName"
    ).innerText =
        response.name || "-";

    document.getElementById(
        "productPrice"
    ).innerText =
        response.price || "-";

    document.getElementById(
        "productRating"
    ).innerText =
        response.rating || "-";

    document.getElementById(
        "reviewCount"
    ).innerText =
        response.reviewCount || "0";

    document.getElementById(
        "productAsin"
    ).innerText =
        response.asin || "-";

    document.getElementById(
        "productSpecifications"
    ).innerText =
        response.specifications || "-";
}


// ============================================================
// DISPLAY COMPATIBILITY
// ============================================================

function displayCompatibility(
    compatibility
) {

    const container =
        document.getElementById(
            "compatibilityResults"
        );

    container.innerHTML = "";

    if (!compatibility) {

        container.innerText =
            "No compatibility information.";

        return;
    }

    const overall =
        document.createElement("div");

    overall.className =
        "aspect-card";

    if (compatibility.compatible) {

        overall.innerHTML = `
            <div class="aspect-header">

                <strong>
                    &#9989; Compatible
                </strong>

                <span class="positive">
                    PASS
                </span>

            </div>

            <p class="reason">
                All supplied requirements
                were satisfied.
            </p>
        `;

    } else {

        overall.innerHTML = `
            <div class="aspect-header">

                <strong>
                    &#10060; Not Compatible
                </strong>

                <span class="negative">
                    FAIL
                </span>

            </div>

            <p class="reason">
                One or more requirements
                were not satisfied.
            </p>
        `;
    }

    container.appendChild(
        overall
    );

    const violations =
        compatibility.violations || [];

    violations.forEach(
        violation => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "aspect-card";

            card.innerHTML = `
                <div class="aspect-header">

                    <strong>
                        &#10060; ${violation.requirement}
                    </strong>

                    <span class="negative">
                        FAIL
                    </span>

                </div>

                <p class="reason">
                    ${violation.reason}
                </p>

                <p>
                    <strong>
                        Required:
                    </strong>

                    ${violation.required}
                </p>

                <p>
                    <strong>
                        Actual:
                    </strong>

                    ${violation.actual ?? "Not found"}
                </p>
            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// DISPLAY FINAL DECISION
// ============================================================

function displayDecision(
    decision
) {

    const container =
        document.getElementById(
            "decisionResults"
        );

    container.innerHTML = "";

    if (!decision) {

        container.innerText =
            "No personalized decision available.";

        return;
    }

    const card =
        document.createElement(
            "div"
        );

    card.className =
        "aspect-card";

    let decisionClass =
        "neutral";

    let decisionSymbol =
        "&#9888;";

    if (
        decision.decision ===
        "BUY"
    ) {

        decisionClass =
            "positive";

        decisionSymbol =
            "&#9989;";

    } else if (
        decision.decision ===
        "DON'T BUY"
    ) {

        decisionClass =
            "negative";

        decisionSymbol =
            "&#10060;";
    }

    let scoreHTML = "";

    if (
        decision.score !== undefined
    ) {

        scoreHTML = `
            <p>

                <strong>
                    Decision Score:
                </strong>

                ${decision.score}

            </p>
        `;
    }

    let returnRiskHTML = "";

    if (
        decision.return_probability
        !== undefined
    ) {

        returnRiskHTML = `
            <p>

                <strong>
                    Return Probability:
                </strong>

                ${decision.return_probability}

            </p>

            <p>

                <strong>
                    Return Risk:
                </strong>

                ${decision.return_risk || "-"}

            </p>
        `;
    }

    card.innerHTML = `

        <div class="aspect-header">

            <strong
                class="${decisionClass}"
            >
                ${decisionSymbol}
                ${decision.decision}
            </strong>

        </div>

        <p class="reason">
            ${decision.reason || ""}
        </p>

        ${scoreHTML}

        ${returnRiskHTML}

    `;

    container.appendChild(
        card
    );
}


// ============================================================
// DISPLAY AI ANALYSIS
// ============================================================

function displayAnalysis(
    analysis
) {

    const container =
        document.getElementById(
            "analysisResults"
        );

    container.innerHTML = "";

    if (
        !analysis
        || !analysis.aspects
    ) {

        container.innerText =
            "No review analysis available.";

        return;
    }

    analysis.aspects.forEach(
        item => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "aspect-card";

            let sentimentClass =
                "neutral";

            if (
                item.sentiment ===
                "positive"
            ) {

                sentimentClass =
                    "positive";

            } else if (
                item.sentiment ===
                "negative"
            ) {

                sentimentClass =
                    "negative";
            }

            let evidenceHTML = "";

            if (
                item.evidence
                && item.evidence.length > 0
            ) {

                evidenceHTML = `

                    <div class="evidence">

                        <strong>
                            Evidence:
                        </strong>

                        <ul>

                            ${item.evidence
                                .map(
                                    evidence =>
                                        `<li>${evidence}</li>`
                                )
                                .join("")}

                        </ul>

                    </div>
                `;
            }

            card.innerHTML = `

                <div class="aspect-header">

                    <strong>
                        ${item.aspect}
                    </strong>

                    <span
                        class="${sentimentClass}"
                    >
                        ${item.sentiment.toUpperCase()}
                    </span>

                </div>

                <p class="reason">
                    ${item.reason}
                </p>

                ${evidenceHTML}

            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// ANALYZE PRODUCT
// ============================================================

document
    .getElementById("analyzeButton")
    .addEventListener(
        "click",
        async () => {

            const status =
                document.getElementById(
                    "status"
                );

            status.innerText =
                "Reading product...";

            try {

                await saveUserProfile();

                const [tab] =
                    await chrome.tabs.query({
                        active: true,
                        currentWindow: true
                    });

                chrome.tabs.sendMessage(
                    tab.id,
                    {
                        type:
                            "GET_PRODUCT_INFO"
                    },
                    async response => {

                        if (
                            chrome.runtime.lastError
                        ) {

                            status.innerText =
                                "Unable to read this page.";

                            return;
                        }

                        if (!response) {

                            status.innerText =
                                "No product information found.";

                            return;
                        }

                        displayProduct(
                            response
                        );

                        const requestData = {

                            ...response,

                            user_requirements:
                                userRequirements,

                            user_profile:
                                userProfile

                        };

                        try {

                            status.innerText =
                                "Analyzing product...";

                            const backendResponse =
                                await fetch(
                                    "http://127.0.0.1:8000/analyze",
                                    {
                                        method:
                                            "POST",

                                        headers: {
                                            "Content-Type":
                                                "application/json"
                                        },

                                        body:
                                            JSON.stringify(
                                                requestData
                                            )
                                    }
                                );

                            const result =
                                await backendResponse.json();

                            console.log(
                                "Backend analysis:",
                                result
                            );

                            if (
                                result.error
                            ) {

                                status.innerText =
                                    result.error;

                                return;
                            }

                            displayCompatibility(
                                result.compatibility
                            );

                            displayDecision(
                                result.decision
                            );

                            displayAnalysis(
                                result.analysis
                            );

                            status.innerText =
                                "Analysis complete!";

                        }

                        catch (error) {

                            console.error(
                                "Backend error:",
                                error
                            );

                            status.innerText =
                                "Could not connect to backend.";

                            document.getElementById(
                                "analysisResults"
                            ).innerText =
                                "Backend is unavailable.";
                        }
                    }
                );

            }

            catch (error) {

                console.error(
                    "Extension error:",
                    error
                );

                status.innerText =
                    "Could not analyze this page.";
            }
        }
    );


// ============================================================
// INITIAL DISPLAY
// ============================================================

displayRequirements();

loadUserProfile();

displayStoredOrderCount();