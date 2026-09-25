"use strict";

(() => {
  const emailSuffixes = ["@example.com", "@gemail.com"];
  const syntheticPrefixes = [
    "sandbox-",
    "training-",
    "demo-",
    "local-",
    "test-",
    "sample-",
  ];
  const emailFields = new Set([
    "username",
    "email",
    "identifier",
    "work_email",
    "billing_email",
  ]);
  const paymentMethods = new Set([
    "Fictional card ending 4242",
    "Northstar invoice account",
    "Pay at local pickup",
  ]);

  function notify(message, tone = "success") {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.className = `victim-toast victim-toast-${tone}`;
    toast.setAttribute("role", tone === "error" ? "alert" : "status");
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3200);
  }

  function reject(message) {
    notify(message, "error");
    return false;
  }

  function validateValue(field) {
    const value = field.value.trim();
    if (!value) return true;
    if (field.name === "payment_method") {
      return paymentMethods.has(value)
        ? true
        : reject("Choose one of the fictional payment options.");
    }
    if (field.name === "action") return true;
    if (
      emailFields.has(field.name) &&
      value.includes("@") &&
      !emailSuffixes.some((suffix) => value.toLowerCase().endsWith(suffix))
    ) {
      return reject("Use an email ending in @example.com or @gemail.com.");
    }
    if (
      field.name === "password" &&
      !syntheticPrefixes.some((prefix) => value.toLowerCase().startsWith(prefix))
    ) {
      return reject("Use a training-only value such as sandbox-password.");
    }
    return true;
  }

  function validateForm(form) {
    const fields = [
      ...form.querySelectorAll(
        'input[name="username"], input[name="identifier"], input[name="email"], input[name="confirmation"], input[name="password"], select[name="payment_method"]',
      ),
    ];
    return fields.every(validateValue);
  }

  window.addEventListener("DOMContentLoaded", () => {
    const serverError = document.body.dataset.captureError;
    if (serverError) notify(serverError, "error");
    for (const form of document.querySelectorAll("form")) {
      form.addEventListener("submit", (event) => {
        if (!validateForm(form)) event.preventDefault();
      });
    }
  });
})();
