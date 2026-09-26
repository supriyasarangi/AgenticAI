const form = document.getElementById("sip-form");
const suggestBtn = document.getElementById("suggest-btn");
const suggestCaption = document.getElementById("suggest-caption");

function currency(value) {
  return "₹" + Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

suggestBtn.addEventListener("click", async () => {
  const countryCode = document.getElementById("country_code").value;
  suggestCaption.textContent = "Fetching live inflation data…";
  try {
    const res = await fetch(`/api/suggested-rate/${countryCode}`);
    const data = await res.json();
    if (!data.ok) {
      suggestCaption.textContent = "Could not fetch live data right now.";
      return;
    }
    document.getElementById("annual_return_rate").value = data.suggested_annual_return_pct;
    suggestCaption.textContent =
      `Suggested from ${data.year} CPI inflation (${data.inflation_rate_pct}%) ` +
      `+ assumed ${data.assumed_real_premium_pct}% equity premium.`;
  } catch (err) {
    suggestCaption.textContent = "Could not fetch live data right now.";
  }
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    monthly_investment: Number(document.getElementById("monthly_investment").value),
    annual_return_rate: Number(document.getElementById("annual_return_rate").value),
    years: Number(document.getElementById("years").value),
    country_code: document.getElementById("country_code").value,
    include_inflation_adjustment: true,
  };

  const res = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    alert("Something went wrong calculating your SIP. Please check your inputs.");
    return;
  }

  const data = await res.json();

  document.getElementById("r-invested").textContent = currency(data.invested_amount);
  document.getElementById("r-returns").textContent = currency(data.estimated_returns);
  document.getElementById("r-maturity").textContent = currency(data.maturity_value);

  const inflationBlock = document.getElementById("inflation-block");
  const inflationUnavailable = document.getElementById("inflation-unavailable");

  if (data.inflation && data.inflation.ok) {
    document.getElementById("inflation-used").textContent =
      `Based on ${data.inflation.year} inflation of ${data.inflation.inflation_rate_pct}% in ${data.inflation.country_code}.`;
    document.getElementById("r-real-returns").textContent = currency(data.real_estimated_returns);
    document.getElementById("r-real-maturity").textContent = currency(data.real_maturity_value);
    inflationBlock.hidden = false;
    inflationUnavailable.hidden = true;
  } else {
    inflationBlock.hidden = true;
    inflationUnavailable.hidden = false;
  }

  document.getElementById("results").hidden = false;
});
