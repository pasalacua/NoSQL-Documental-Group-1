// Elementos del laboratorio
const dialogueText = document.getElementById("dialogue-text");
const nextButton = document.getElementById("next-dialogue");

const oakPlaceholder = document.querySelector(".oak-placeholder");
const trainerList = document.getElementById("trainer-list");
const dialogueBox = document.querySelector(".dialogue-box");

// Introducción del Profesor Oak
const dialogues = [
    "¡Bienvenido al laboratorio Pokémon!",
    "Soy el Profesor Oak, y necesito tu ayuda con algunas investigaciones.",
    "Aquí podrás consultar información, analizar Pokémon y registrar nuevos descubrimientos.",
    "También tendrás que resolver solicitudes de los entrenadores que visiten el laboratorio.",
    "¡Tu trabajo como investigador comienza ahora!"
];

let currentDialogue = 0;

// Avanzar la introducción
nextButton.addEventListener("click", () => {

    currentDialogue++;

    if (currentDialogue < dialogues.length) {
        dialogueText.textContent = dialogues[currentDialogue];

    } else {
        // Finalizar introducción y mostrar entrenadores
        oakPlaceholder.classList.add("hidden");
        dialogueBox.classList.add("hidden");
        trainerList.classList.remove("hidden");
    }
});

// Seleccionar un entrenador
const trainerButtons = document.querySelectorAll(".trainer-option");

trainerButtons.forEach((button) => {

    button.addEventListener("click", () => {

        const trainer = button.dataset.trainer;
        const request = button.dataset.request;

        // Ocultar entrenadores y mostrar solicitud
        trainerList.classList.add("hidden");
        dialogueBox.classList.remove("hidden");

        dialogueText.textContent =
            `${trainer}: ${request}`;

        nextButton.textContent = "VOLVER";
    });

});

// Volver a la lista de entrenadores
nextButton.addEventListener("click", () => {

    if (nextButton.textContent === "VOLVER") {

        dialogueBox.classList.add("hidden");
        trainerList.classList.remove("hidden");

        nextButton.textContent = "SIGUIENTE ▼";
    }

});