const dialogues = [
    "¡Bienvenido al laboratorio Pokémon!",
    "Soy el Profesor Oak, y necesito tu ayuda con algunas investigaciones.",
    "Aquí podrás consultar información, analizar Pokémon y registrar nuevos descubrimientos.",
    "También tendrás que resolver solicitudes de los entrenadores que visiten el laboratorio.",
    "¡Tu trabajo como investigador comienza ahora!"
];

let currentDialogue = 0;

const dialogueText = document.getElementById("dialogue-text");
const nextButton = document.getElementById("next-dialogue");

nextButton.addEventListener("click", () => {
    currentDialogue++;

    if (currentDialogue < dialogues.length) {
        dialogueText.textContent = dialogues[currentDialogue];
    } else {
        dialogueText.textContent =
            "¡Acércate a los entrenadores para comenzar tus investigaciones!";

        nextButton.style.display = "none";
    }
});