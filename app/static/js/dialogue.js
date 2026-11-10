// Cuadro de diálogo del laboratorio.
// Muestra una lista de líneas (botón SIGUIENTE) y, al final, botones de acción opcionales.
const Dialogo = (() => {
    const caja = document.querySelector(".dialogue-box");
    const texto = document.getElementById("dialogue-text");
    const siguiente = document.getElementById("next-dialogue");
    const acciones = document.getElementById("dialogue-actions");

    let lineas = [];
    let indice = 0;
    let opcionesActuales = {};

    function pintar() {
        texto.textContent = lineas[indice];
        const esUltima = indice === lineas.length - 1;
        acciones.innerHTML = "";

        if (!esUltima) {
            siguiente.classList.remove("hidden");
            siguiente.textContent = "SIGUIENTE ▼";
            return;
        }

        const botones = opcionesActuales.botones || [];
        if (botones.length) {
            siguiente.classList.add("hidden");
            botones.forEach((boton) => {
                const elemento = document.createElement("button");
                elemento.type = "button";
                elemento.className = "dialogue-action";
                elemento.textContent = boton.texto;
                elemento.addEventListener("click", boton.accion);
                acciones.appendChild(elemento);
            });
        } else {
            siguiente.classList.remove("hidden");
            siguiente.textContent = opcionesActuales.textoFinal || "SIGUIENTE ▼";
        }
    }

    siguiente.addEventListener("click", () => {
        if (indice < lineas.length - 1) {
            indice++;
            pintar();
            return;
        }
        const alTerminar = opcionesActuales.alTerminar;
        if (!opcionesActuales.botones?.length) {
            if (alTerminar) alTerminar();
        }
    });

    return {
        mostrar(nuevasLineas, opciones = {}) {
            lineas = Array.isArray(nuevasLineas) ? nuevasLineas : [nuevasLineas];
            indice = 0;
            opcionesActuales = opciones;
            caja.classList.remove("hidden");
            pintar();
        },
        ocultar() {
            caja.classList.add("hidden");
        },
    };
})();
