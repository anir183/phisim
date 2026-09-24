"use strict";

for (const form of document.querySelectorAll("form[data-transition-ms]")) {
  form.addEventListener("submit", (event) => {
    const delay = Number(form.dataset.transitionMs || "0");
    if (!delay || form.dataset.transitionStarted === "true") return;
    event.preventDefault();
    form.dataset.transitionStarted = "true";
    const submit = form.querySelector("button[type=submit]");
    if (submit) {
      submit.disabled = true;
      submit.setAttribute("aria-busy", "true");
    }
    window.setTimeout(() => form.submit(), delay);
  });
}
