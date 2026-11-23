// Pick or drop a photo, preview it, send it to /api/predict and show the answer.
const form = document.getElementById("form");
const input = document.getElementById("photo");
const drop = document.getElementById("drop");
const preview = document.getElementById("preview");
const hint = document.getElementById("hint");
const submit = document.getElementById("submit");
const result = document.getElementById("result");
const error = document.getElementById("error");

const MAX_MB = 5;
const WORDS = { cat: "It's a cat 🐱", dog: "It's a dog 🐶", neither: "Neither a cat nor a dog" };

function showError(message) {
  error.textContent = message;
  error.hidden = false;
}

function choose(file) {
  result.hidden = true;
  error.hidden = true;
  if (!file) return;
  if (!file.type.startsWith("image/")) return showError("Please choose an image file.");
  if (file.size > MAX_MB * 1024 * 1024) return showError(`That photo is bigger than ${MAX_MB} MB.`);
  if (preview.src) URL.revokeObjectURL(preview.src);
  preview.src = URL.createObjectURL(file);
  preview.alt = `Preview of ${file.name}`;
  preview.hidden = false;
  hint.hidden = true;
  submit.disabled = false;
}

input.addEventListener("change", () => choose(input.files[0]));

["dragenter", "dragover"].forEach((type) =>
  drop.addEventListener(type, (event) => {
    event.preventDefault();
    drop.classList.add("over");
  }),
);
["dragleave", "drop"].forEach((type) => drop.addEventListener(type, () => drop.classList.remove("over")));
drop.addEventListener("drop", (event) => {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (!file) return;
  const list = new DataTransfer();
  list.items.add(file);
  input.files = list.files;
  choose(file);
});

const percent = (value) => `${Math.round(value * 100)}%`;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = input.files[0];
  if (!file) return;
  submit.disabled = true;
  submit.textContent = "Looking…";
  error.hidden = true;
  try {
    const body = new FormData();
    body.append("photo", file);
    const response = await fetch("/api/predict", { method: "POST", body });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Something went wrong. Please try again.");
    document.getElementById("verdict").textContent = WORDS[data.label] ?? data.label;
    document.getElementById("bar-cat").style.width = percent(data.cat);
    document.getElementById("bar-dog").style.width = percent(data.dog);
    document.getElementById("pct-cat").textContent = percent(data.cat);
    document.getElementById("pct-dog").textContent = percent(data.dog);
    document.getElementById("guess").textContent = `Closest match: ${data.best_guess}`;
    result.hidden = false;
  } catch (err) {
    showError(err.message);
  } finally {
    submit.disabled = false;
    submit.textContent = "Identify";
  }
});
