// Pantalla de título: crear o cargar la partida (documento en la colección investigadores).
const modal = document.getElementById("modal-partida");
const formulario = document.getElementById("form-partida");
const titulo = document.getElementById("modal-titulo");
const campoNombre = document.getElementById("nombre-investigador");
const errorModal = document.getElementById("modal-error");
const estadoConexion = document.getElementById("estado-conexion");

let modo = "nueva";

function abrirModal(nuevoModo) {
    modo = nuevoModo;
    titulo.textContent = modo === "nueva" ? "NUEVA PARTIDA" : "CARGAR PARTIDA";
    errorModal.textContent = "";
    modal.classList.remove("hidden");
    campoNombre.focus();
}

document.getElementById("nueva-partida").addEventListener("click", () => abrirModal("nueva"));
document.getElementById("cargar-partida").addEventListener("click", () => abrirModal("cargar"));
document.getElementById("modal-cancelar").addEventListener("click", () => modal.classList.add("hidden"));

document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") modal.classList.add("hidden");
});

formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    errorModal.textContent = "";
    const url = modo === "nueva" ? "/api/investigadores" : "/api/investigadores/cargar";
    try {
        await API.post(url, { nombre: campoNombre.value });
        window.location.href = "/partida";
    } catch (error) {
        errorModal.textContent = error.error || "No se pudo iniciar la partida.";
    }
});

// Verifica que el servidor llegue a MongoDB antes de jugar.
API.get("/api/estado")
    .then((estado) => {
        estadoConexion.textContent = `● MongoDB conectado · ${estado.pokemon} Pokémon en la Pokédex`;
        estadoConexion.classList.add("ok");
    })
    .catch((error) => {
        estadoConexion.textContent = `● ${error.error || "Sin conexión con la base de datos"}`;
        estadoConexion.classList.add("error");
    });
