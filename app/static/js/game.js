const nameSelector = document.getElementById("name-selector");
const laboratory = document.getElementById("laboratory");
const nameDisplay = document.getElementById("name-display-text");
const keyboard = document.getElementById("name-keyboard");
const backspaceButton = document.getElementById("name-backspace");
const confirmButton = document.getElementById("name-confirm");

const maxNameLength = 10;
const defaultName = "NUNEZ";
let researcherName = defaultName;

const savedName = window.localStorage.getItem("pokelab-researcher-name");
if (savedName) {
    researcherName = savedName.toUpperCase().slice(0, maxNameLength);
}

document.body.dataset.researcherName = researcherName;

function updateNameDisplay() {
    nameDisplay.textContent = researcherName || "_";
    confirmButton.disabled = researcherName.length === 0;
}

function addLetter(letter) {
    if (researcherName.length >= maxNameLength) return;
    researcherName += letter;
    updateNameDisplay();
}

"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").forEach((letter) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "name-letter";
    button.textContent = letter;
    button.setAttribute("aria-label", `Agregar ${letter}`);
    button.addEventListener("click", () => addLetter(letter));
    keyboard.appendChild(button);
});

backspaceButton.addEventListener("click", () => {
    researcherName = researcherName.slice(0, -1);
    updateNameDisplay();
});

confirmButton.addEventListener("click", () => {
    const cleanName = researcherName.trim() || defaultName;
    window.localStorage.setItem("pokelab-researcher-name", cleanName);
    document.body.dataset.researcherName = cleanName;
    nameSelector.classList.add("hidden");
    laboratory.classList.remove("hidden");
    document.getElementById("player-character").classList.remove("hidden");
});

updateNameDisplay();
