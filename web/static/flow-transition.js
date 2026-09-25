"use strict";

const MAX_RENDERED_TRANSITION_MS = 1800;

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
  window.setTimeout(() => window.location.assign(link.href), delay);
}

for (const form of document.querySelectorAll("form[data-transition-ms]")) {
  form.addEventListener("submit", submitAfterTransition);
}

for (const link of document.querySelectorAll("a[data-transition-ms]")) {
  link.addEventListener("click", followAfterTransition);
}
