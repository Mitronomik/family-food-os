#!/usr/bin/env node
"use strict";

/** Exercise the water choice against the actual two-process HTML artifact.
 * No third-party DOM library: this mock covers selectors/events used by the
 * internal preview. It does not establish real browser/device compatibility.
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const file = process.argv[2];
if (!file) throw new Error("Expected path to generated week-preview.html");
const html = fs.readFileSync(file, "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1, "Exactly one inline interaction script");

function control(value = "") {
  return {
    value,
    textContent: "",
    listeners: {},
    addEventListener(name, callback) { this.listeners[name] = callback; },
    fire(name) {
      assert.equal(typeof this.listeners[name], "function");
      this.listeners[name]();
    },
  };
}
function groceryRow(label, isWater) {
  const checkbox = control();
  checkbox.checked = false;
  checkbox.disabled = isWater;
  const item = { classList: { toggle(name, enabled) { this[name] = enabled; } } };
  return {
    dataset: { label, water: String(isWater) },
    hidden: false,
    checkbox,
    item,
    querySelector(selector) {
      if (selector === "input" || selector === "input[type=checkbox]") {
        return checkbox;
      }
      if (selector === ".item") return item;
      throw new Error("Unsupported UI selector: " + selector);
    },
  };
}
const rows = [
  ...html.matchAll(
    /<div class="grocery-row" data-label="([^"]+)" data-water="(true|false)">/g,
  ),
].map((match) => groceryRow(match[1], match[2] === "true"));
assert.ok(rows.length > 1, "Need a real multi-item Shopping result");
const waterRows = rows.filter((row) => row.dataset.water === "true");
assert.equal(waterRows.length, 1, "Exactly one WATER item on accepted fixture");
assert.match(html, /<option value="unknown" selected>/);
assert.match(html, /<option value="buy">/);
assert.match(html, /<option value="available">/);
assert.match(html, /disabled aria-label="Отметить: Вода питьевая"/);
assert.match(html, /не меняет расчёты Shopping Engine или Pantry/);
assert.ok(!scripts[0][1].includes("localStorage"));
assert.ok(!scripts[0][1].includes("fetch("));

const water = waterRows[0];
const other = rows.find((row) => row.dataset.water === "false");
const search = control();
const counter = control();
const waterChoice = control("unknown");
const waterNote = control();
const waterFlag = control();
const document = {
  querySelectorAll(selector) {
    assert.equal(selector, ".grocery-row");
    return rows;
  },
  querySelector(selector) {
    const map = {
      "#search": search,
      "#counter": counter,
      "#water-choice": waterChoice,
      "#water-choice-note": waterNote,
      ".water-review-status": waterFlag,
    };
    return map[selector] || null;
  },
};
vm.runInNewContext(scripts[0][1], { document });
assert.equal(water.checkbox.disabled, true);
assert.equal(other.checkbox.disabled, false);
assert.match(counter.textContent, new RegExp("0 из " + (rows.length - 1)));
assert.match(waterFlag.textContent, /Требует решения/);

waterChoice.value = "buy";
waterChoice.fire("change");
assert.equal(water.checkbox.disabled, false);
assert.match(counter.textContent, new RegExp("0 из " + rows.length));
water.checkbox.checked = true;
water.checkbox.fire("change");
assert.match(counter.textContent, new RegExp("1 из " + rows.length));

waterChoice.value = "available";
waterChoice.fire("change");
assert.equal(water.checkbox.disabled, true);
assert.equal(water.checkbox.checked, false);
assert.equal(other.checkbox.disabled, false);
assert.match(counter.textContent, new RegExp("0 из " + (rows.length - 1)));
assert.match(waterNote.textContent, /Pantry и Shopping не изменены/);

waterChoice.value = "unknown";
waterChoice.fire("change");
assert.equal(water.checkbox.disabled, true);
assert.match(waterFlag.textContent, /Требует решения/);
search.value = other.dataset.label;
search.fire("input");
assert.equal(water.hidden, true);
assert.equal(other.hidden, false);

console.log(
  "PASS: real-week WATER UNKNOWN -> BUY -> AVAILABLE -> UNKNOWN; " +
  "checklist reset, non-water rows and search preserved",
);
