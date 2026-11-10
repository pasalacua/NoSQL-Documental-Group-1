const notebookButton = document.getElementById("notebook-button");
const notebookPanel = document.getElementById("notebook-panel");
const closeNotebook = document.getElementById("close-notebook");

// Abrir el cuaderno
notebookButton.addEventListener("click", () => {
    notebookPanel.classList.remove("hidden");
});

// Cerrar el cuaderno
closeNotebook.addEventListener("click", () => {
    notebookPanel.classList.add("hidden");
});