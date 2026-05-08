/**
 * utils/text.js — Text utility helpers.
 */

/** Count words in a string. */
export function countWords(text = "") {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

/** Truncate a string to maxLen chars, appending ellipsis. */
export function truncate(str = "", maxLen = 60) {
  return str.length > maxLen ? str.slice(0, maxLen) + "…" : str;
}

/** Slugify a string for use in filenames. */
export function slugify(str = "") {
  return str
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .slice(0, 60);
}
