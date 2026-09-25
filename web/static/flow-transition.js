"use strict";

const MAX_RENDERED_TRANSITION_MS = 2500;
let loadingIndicator = null;

function showLoadingIndicator() {
  if (loadingIndicator) return;
  loadingIndicator = document.createElement("div");
  loadingIndicator.className = "flow-transition-loading";
  loadingIndicator.setAttribute("role", "status");
  loadingIndicator.setAttribute("aria-live", "polite");
  const spinner = document.createElement("span");
  spinner.className = "flow-transition-spinner";
  spinner.setAttribute("aria-hidden", "true");
  const label = document.createElement("span");
  label.className = "flow-transition-label";
  label.textContent = "Loading local simulation…";
  loadingIndicator.append(spinner, label);
  document.body.appendChild(loadingIndicator);
}

function transitionDelay(element) {
  const value = Number(element.dataset.transitionMs || "0");
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(MAX_RENDERED_TRANSITION_MS, Math.round(value));
}

function markPending(element, pending) {
  element.dataset.transitionPending = String(pending);
  if (pending) {
    element.setAttribute("aria-busy", "true");
  } else {
    element.removeAttribute("aria-busy");
  }
}

function submitAfterTransition(event) {
  const form = event.currentTarget;
  if (event.defaultPrevented || form.dataset.transitionPending === "true") {
    return;
  }
  const delay = transitionDelay(form);
  if (!delay) return;
  event.preventDefault();
  markPending(form, true);
  showLoadingIndicator();
  for (const control of form.querySelectorAll(
    'button[type="submit"], input[type="submit"]',
  )) {
    control.disabled = true;
  }
  window.setTimeout(() => HTMLFormElement.prototype.submit.call(form), delay);
}

function followAfterTransition(event) {
  const link = event.currentTarget;
  if (
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    link.target ||
    link.hasAttribute("download")
  ) {
    return;
  }
  const delay = transitionDelay(link);
  if (!delay) return;
  event.preventDefault();
  markPending(link, true);
  showLoadingIndicator();
  window.setTimeout(() => window.location.assign(link.href), delay);
}

for (const form of document.querySelectorAll("form[data-transition-ms]")) {
  form.addEventListener("submit", submitAfterTransition);
}

for (const link of document.querySelectorAll("a[data-transition-ms]")) {
  link.addEventListener("click", followAfterTransition);
}
