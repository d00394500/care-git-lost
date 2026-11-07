"use strict";

let routes = [];
const byId = id => document.getElementById(id);

for (const name of ["arcade", "explorer"]) {
  byId(`${name}-tab`).addEventListener("click", () => {
    for (const section of ["arcade", "explorer"]) {
      const active = section === name;
      byId(`${section}-panel`).hidden = !active;
      byId(`${section}-tab`).classList.toggle("active", active);
      byId(`${section}-tab`).setAttribute("aria-pressed", String(active));
    }
  });
}

async function apiRequest(path, options = {}) {
  const target = new URL(path, window.location.origin);
  if (target.origin !== window.location.origin) throw new Error("Use an endpoint on this API.");
  const response = await fetch("/api" + target.pathname + target.search, { ...options, signal: AbortSignal.timeout(90000) });
  const text = await response.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  return { response, data };
}

document.querySelectorAll("form[data-game]").forEach(form => {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const card = form.closest(".game");
    const output = card.querySelector(".game-result");
    const button = form.querySelector("button");
    const fields = new FormData(form);
    const game = form.dataset.game;
    const paths = {
      coin: `/coinflip/${encodeURIComponent(fields.get("choice"))}`,
      roulette: `/roulette-payout?${new URLSearchParams(fields)}`,
      slots: "/api/lucky-slot-machine",
      dice: `/luckyDice?${new URLSearchParams(fields)}`,
      crossRoad: `/crossRoad?${new URLSearchParams(fields)}`,
      rocketRide: `/rocketRide?${new URLSearchParams(fields)}`
    };
    button.disabled = true;
    card.classList.add("busy");
    output.className = "game-result";
    output.textContent = "Making a little luck…";
    try {
      const { response, data } = await apiRequest(paths[game]);
      if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
      let won = data.won;
      if (game === "coin") output.textContent = `${data.result.toUpperCase()}! ${won ? "Good call. You won!" : "Not your flip. Try again?"}`;
      if (game === "roulette") output.textContent = `${data.spin.number} · ${data.spin.color.toUpperCase()} — ${won ? "You won!" : "No luck this time."} Payout: ${data.payout} play credits.`;
      if (game === "slots") output.textContent = `${data.spin.join(" / ")} — ${data.prize.replaceAll("_", " ")} · ${data.payout_multiplier}×`;
      if (game === "dice") {
        won = data.result === "You won!";
        output.textContent = `Rolled a ${data.dice_roll}. ${data.result}`;
      }
      if (game === "crossRoad") {
        won = data.win === "you win!";
        output.textContent = `${won ? "Safe crossing!" : "You hit the danger point."} ${data.jumps} jump${data.jumps === 1 ? "" : "s"} · ${won ? `${data.multiplier}× multiplier · ` : ""}Payout: ${data.payout} play credits.`;
      }
      if (game === "rocketRide") {
        output.textContent = `${data.crashed ? `Crashed at ${data.crash_point}×.` : `Cashed out at ${data.cash_out}× before the ${data.crash_point}× crash.`} ${data.won ? "You won!" : "No payout this time."} Payout: ${data.payout} · Profit: ${data.profit} play credits.`;
      }
      output.classList.toggle("win", Boolean(won));
    } catch (error) {
      output.classList.add("error");
      output.textContent = error.name === "TimeoutError" ? "The backend is taking a while to wake up. Try again." : `Couldn't play: ${error.message}`;
    } finally {
      button.disabled = false;
      card.classList.remove("busy");
    }
  });
});

byId("fortune-button").addEventListener("click", async () => {
  const button = byId("fortune-button");
  button.disabled = true;
  try {
    const { response, data } = await apiRequest("/api/fortune-cookie");
    if (!response.ok) throw new Error("The cookie jar is unavailable. Try again.");
    byId("fortune-text").textContent = data.fortune;
  } catch (error) {
    byId("fortune-text").textContent = `Couldn't open a cookie. ${error.message}`;
  } finally { button.disabled = false; }
});

let selectedRoute;
const examples = {
  "/redline": "string=JP&bet=10", "/catbox": "number=42",
  "/roulette-payout": "color=red&bet=10", "/highCard": "guess=higher&bet=10",
  "/luckyDice": "guess=high", "/luckyNumber": "guess=7",
  "/rigged_coin_toss": "guess=heads", "/word-count": "text=Hello+world",
  "/api/slugify": "text=Hello+world", "/certificate": "common_name=localhost&days=30"
};
function selectRoute(route) {
  selectedRoute = route;
  byId("selected-route").textContent = route.path;
  byId("request-path").value = route.path.replace(/<(?:(?:[^:>]+):)?([^>]+)>/g, (_, name) => ({ choice: "heads", number: "4", num: "42" })[name] || "1");
  byId("request-method").replaceChildren(...route.methods.map(method => {
    const option = document.createElement("option");
    option.value = option.textContent = method;
    return option;
  }));
  byId("request-query").value = examples[route.path] || "";
  byId("request-body").value = route.path === "/add-score" ? JSON.stringify({ name: "Player", score: 10 }, null, 2) : "{}";
  byId("response-output").textContent = "Your response will appear here.";
  byId("response-status").textContent = "Ready when you are";
  updateMethod();
  document.querySelectorAll(".route-button").forEach(button => {
    const selected = button.dataset.path === route.path;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}
function updateMethod() {
  const method = byId("request-method").value;
  byId("method-badge").textContent = method;
  byId("body-label").hidden = method === "GET";
}
function renderRoutes() {
  const query = byId("route-search").value.toLowerCase();
  const filtered = routes.filter(route => `${route.path} ${route.methods.join(" ")}`.toLowerCase().includes(query));
  byId("route-count").textContent = `${routes.length} LIVE ROUTES`;
  byId("route-list").replaceChildren(...filtered.map(route => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "route-button";
    button.dataset.path = route.path;
    button.classList.toggle("selected", selectedRoute === route);
    button.setAttribute("aria-pressed", String(selectedRoute === route));
    const method = document.createElement("small");
    method.textContent = route.methods.join(" / ");
    button.append(method, document.createTextNode(route.path));
    button.addEventListener("click", () => selectRoute(route));
    return button;
  }));
  if (!filtered.length) byId("route-list").textContent = "No matching endpoints.";
}
byId("route-search").addEventListener("input", renderRoutes);
byId("request-method").addEventListener("change", updateMethod);
byId("request-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = byId("send-request");
  button.disabled = true;
  byId("response-status").textContent = "Requesting…";
  const started = performance.now();
  try {
    const path = byId("request-path").value.trim();
    if (!path.startsWith("/") || path.startsWith("//") || path.includes("\\") || path.includes("#") || path.includes("?")) throw new Error("Enter a local path starting with /. Use the query field for parameters.");
    const url = new URL(path, window.location.origin);
    if (url.origin !== window.location.origin) throw new Error("Use an endpoint on this API.");
    const method = byId("request-method").value;
    if (!selectedRoute.methods.includes(method)) throw new Error("Select a supported method.");
    url.search = new URLSearchParams(byId("request-query").value.trim()).toString();
    const options = { method };
    if (method !== "GET") {
      const body = byId("request-body").value.trim() || "{}";
      JSON.parse(body);
      options.body = body;
      options.headers = { "Content-Type": "application/json" };
    }
    const { response, data } = await apiRequest(url, options);
    byId("response-output").textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    byId("response-status").textContent = `${response.status} ${response.statusText} · ${Math.round(performance.now() - started)} ms`;
  } catch (error) {
    byId("response-status").textContent = "Request failed";
    byId("response-output").textContent = error.name === "SyntaxError" ? "Invalid JSON body. Check your syntax and try again." : error.message;
  } finally { button.disabled = false; }
});

async function loadRoutes() {
  try {
    const response = await fetch("./api-routes.json");
    if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
    const catalog = await response.json();
    if (!Array.isArray(catalog)) throw new Error("The endpoint catalog is not a list.");

    routes = catalog;
    renderRoutes();
    const initialRoute = routes.find(route => route.path === "/api-info") || routes[0];
    if (initialRoute) selectRoute(initialRoute);
  } catch (error) {
    byId("route-count").textContent = "CATALOG UNAVAILABLE";
    byId("route-list").textContent = `Couldn't load endpoints: ${error.message}`;
  }
}

loadRoutes();
