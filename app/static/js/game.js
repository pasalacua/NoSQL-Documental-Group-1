// Flujo principal del laboratorio: introducción, entrenadores y misiones.
// Las misiones se leen de la colección `misiones` y el progreso de `investigadores`.
(() => {
    const listaEntrenadores = document.getElementById("trainer-list");
    const opciones = document.getElementById("trainer-options");
    const puntosHud = document.getElementById("hud-points");
    const rankingPanel = document.getElementById("ranking-panel");
    const oak = document.querySelector(".oak-character");

    let misiones = [];

    // Introducción del Profesor Oak (primera partida)
    const introduccion = [
        "¡Bienvenido al laboratorio Pokémon!",
        "Soy el Profesor Oak, y necesito tu ayuda con algunas investigaciones.",
        "Toda la información del laboratorio está guardada en MongoDB, una base de datos de documentos.",
        "Aquí podrás consultar información, analizar Pokémon y registrar nuevos descubrimientos.",
        "También tendrás que resolver solicitudes de los entrenadores que visiten el laboratorio.",
        "Si te trabás, abrí el cuaderno de investigación (arriba a la derecha).",
        "¡Tu trabajo como investigador comienza ahora!",
    ];

    function ocultarOak() {
        oak?.classList.add("hidden");
    }

    async function finalizarIntroduccion() {
        try {
            await API.post("/api/introduccion/completar");
            window.POKELAB.introduccionCompletada = true;
            ocultarOak();
            mostrarEntrenadores();
        } catch (error) {
            Dialogo.mostrar(error.error || "No se pudo guardar el progreso de la introducción. Intentá nuevamente.");
        }
    }

    function actualizarPerfil(perfil) {
        if (perfil) puntosHud.textContent = perfil.puntos;
    }

    async function cargarMisiones() {
        misiones = await API.get("/api/misiones");
        return misiones;
    }

    function pendientes() {
        return misiones.filter((m) => !m.completada).length;
    }

    function mostrarEntrenadores() {
        Dialogo.ocultar();
        opciones.innerHTML = "";
        misiones.forEach((mision) => {
            const boton = document.createElement("button");
            boton.className = `trainer-option${mision.completada ? " completada" : ""}`;
            boton.innerHTML = `
                <span class="trainer-sprite">${esc(mision.sprite)}</span>
                <span class="trainer-name">${esc(mision.entrenador.toUpperCase())}</span>
                <span class="trainer-state">${mision.completada ? `✓ ${mision.puntos}` : "!"}</span>`;
            boton.addEventListener("click", () => elegirEntrenador(mision));
            opciones.appendChild(boton);
        });
        listaEntrenadores.classList.remove("hidden");
    }

    function elegirEntrenador(mision) {
        listaEntrenadores.classList.add("hidden");
        const volver = { texto: "VOLVER", accion: mostrarEntrenadores };
        if (mision.completada) {
            Dialogo.mostrar(`${mision.entrenador}: ¡Gracias otra vez por tu ayuda! Si querés, podés practicar de nuevo.`, {
                botones: [{ texto: "PRACTICAR", accion: () => abrirMision(mision) }, volver],
            });
            return;
        }
        Dialogo.mostrar(`${mision.entrenador}: ${mision.pedido}`, {
            botones: [{ texto: "ACEPTAR", accion: () => abrirMision(mision) }, volver],
        });
    }

    function abrirMision(mision) {
        Dialogo.ocultar();
        Terminal.abrir(mision, {
            alActualizarPerfil: actualizarPerfil,
            alCerrar: mostrarEntrenadores,
            alCompletar: async (resultado) => {
                await cargarMisiones();
                const restantes = pendientes();
                const cierre = restantes
                    ? `Profesor Oak: ¡Buen trabajo! Te quedan ${restantes} solicitud${restantes === 1 ? "" : "es"} por resolver.`
                    : "Profesor Oak: ¡Resolviste todas las solicitudes! Mirá tu puesto en el RANKING.";
                Dialogo.mostrar([`${mision.entrenador}: ${resultado.mensaje}`, cierre], {
                    textoFinal: "CONTINUAR ▶",
                    alTerminar: mostrarEntrenadores,
                });
            },
        });
    }

    // Ranking: pipeline de agregación sobre la colección investigadores
    async function abrirRanking() {
        const lista = document.getElementById("ranking-list");
        lista.innerHTML = "<li>Cargando...</li>";
        rankingPanel.classList.remove("hidden");
        try {
            const filas = await API.get("/api/ranking");
            lista.innerHTML = filas.length
                ? filas.map((f) => `
                    <li class="${f.nombre === window.POKELAB.nombre ? "yo" : ""}">
                        <span>${esc(f.nombre)}</span>
                        <span>${f.completadas}/5 · ${f.puntos} PTS</span>
                    </li>`).join("")
                : "<li>Todavía no hay investigadores.</li>";
        } catch (error) {
            lista.innerHTML = `<li>${esc(error.error || "No se pudo cargar el ranking")}</li>`;
        }
    }

    document.getElementById("ranking-button").addEventListener("click", abrirRanking);
    document.getElementById("ranking-close").addEventListener("click", () => rankingPanel.classList.add("hidden"));
    document.getElementById("logout-button").addEventListener("click", async () => {
        await API.post("/api/salir");
        window.location.href = "/";
    });

    // Inicio
    (async () => {
        try {
            await cargarMisiones();
        } catch (error) {
            Dialogo.mostrar(error.error || "No se pudo conectar con la base de datos del laboratorio.");
            return;
        }
        if (window.POKELAB.introduccionCompletada) {
            ocultarOak();
            mostrarEntrenadores();
        } else {
            Dialogo.mostrar(introduccion, { alTerminar: finalizarIntroduccion });
        }
    })();
})();
