const dialogueText = document.getElementById("dialogue-text");
const nextButton = document.getElementById("next-dialogue");
const oakCharacter = document.querySelector(".oak-character");
const trainerList = document.getElementById("trainer-list");
const dialogueBox = document.querySelector(".dialogue-box");
const researcherName = document.body.dataset.researcherName ||
    window.localStorage.getItem("pokelab-researcher-name") || "INVESTIGADOR";

const dialogues = [
    `¡Bienvenido al laboratorio Pokémon, ${researcherName}!`,
    "Soy el Profesor Oak, y necesito tu ayuda con algunas investigaciones.",
    "Aquí podrás consultar información, analizar Pokémon y registrar nuevos descubrimientos.",
    "También tendrás que resolver solicitudes de los entrenadores que visiten el laboratorio.",
    "¡Tu trabajo como investigador comienza ahora!"
];

let currentDialogue = 0;
let dialogueMode = "introduction";

nextButton.addEventListener("click", () => {
    if (dialogueMode === "request") {
        dialogueMode = "trainers";
        dialogueBox.classList.add("hidden");
        trainerList.classList.remove("hidden");
        nextButton.textContent = "SIGUIENTE ▼";
        return;
    }

    currentDialogue++;

    if (currentDialogue < dialogues.length) {
        dialogueText.textContent = dialogues[currentDialogue];
        return;
    }

    dialogueMode = "trainers";
    oakCharacter.classList.add("hidden");
    dialogueBox.classList.add("hidden");
    trainerList.classList.remove("hidden");
});

document.querySelectorAll(".trainer-option").forEach((button) => {
    button.addEventListener("click", () => {
        const trainer = button.dataset.trainer;
        const request = button.dataset.request;

        trainerList.classList.add("hidden");
        dialogueBox.classList.remove("hidden");
        dialogueText.textContent = `${trainer}: ${request}`;
        nextButton.textContent = "VOLVER";
        dialogueMode = "request";
    });
});
