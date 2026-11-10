// Panel del expositor: se actualiza solo cada pocos segundos.
(() => {
    const formPin = document.getElementById("form-pin");
    if (formPin) {
        formPin.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            try {
                await API.post("/panel/ingresar", { pin: document.getElementById("pin").value });
                window.location.reload();
            } catch (error) {
                document.getElementById("pin-error").textContent = error.error || "PIN incorrecto";
            }
        });
        return;
    }

    const NOMBRES_ERROR = {
        trampa_elemmatch: "Trampa de $elemMatch",
        sobran: "Sobran resultados",
        faltan: "Faltan resultados",
        vacio: "Consulta sin resultados",
        falta_unwind: "Falta $unwind",
        falta_limit: "Falta $limit",
        orden: "Falta $sort",
        orden_limit: "$limit antes de $sort",
        totales: "Filtraron antes de agrupar",
        formato: "Formato de agrupación",
        pocos_planes: "Eligieron sin comparar planes",
        plan_ineficiente: "Plan ineficiente",
        forma_existente: "Forma ya registrada (concurrencia)",
    };

    async function refrescar() {
        try {
            const r = await API.get("/api/panel/resumen");
            document.getElementById("panel-url").textContent = r.url;
            document.getElementById("panel-investigadores").textContent = r.investigadores;
            document.getElementById("panel-trampa").textContent = r.errores.trampa_elemmatch || 0;
            document.getElementById("panel-misiones").innerHTML = r.misiones.map((m) => `
                <tr>
                    <td>${esc(m.sprite)} ${esc(m.entrenador)}</td>
                    <td>${esc(m.concepto)}</td>
                    <td><strong>${m.completadas}</strong></td>
                    <td>${m.aciertos}</td>
                    <td>${m.fallos}</td>
                </tr>`).join("");
            const errores = Object.entries(r.errores).sort((a, b) => b[1] - a[1]);
            document.getElementById("panel-errores").innerHTML = errores.length
                ? errores.map(([e, n]) => `<span class="chip">${esc(NOMBRES_ERROR[e] || e)}: ${n}</span>`).join(" ")
                : "Todavía no hay errores.";
            document.getElementById("panel-formas").innerHTML = r.formas.length
                ? r.formas.map((f) => `
                    <details>
                        <summary><strong>${esc(f.pokemon)}</strong> · ${esc(f.forma.nombre)} · por ${esc(f.forma.registrada_por)}</summary>
                        <pre class="codigo json">${resaltarJSON(f.forma)}</pre>
                    </details>`).join("")
                : "<p>Todavía nadie registró formas.</p>";
            const campos = Object.entries(r.campos_extra).sort((a, b) => b[1] - a[1]);
            document.getElementById("panel-campos").innerHTML = campos.length
                ? campos.map(([c, n]) => `<li><code>${esc(c)}</code> × ${n}</li>`).join("")
                : "<li>Sin datos todavía.</li>";
            document.getElementById("panel-ranking").innerHTML = r.ranking.map((f) => `
                <li><span>${esc(f.nombre)}</span><span>${f.completadas}/5 · ${f.puntos} PTS</span></li>`).join("");
        } catch (error) {
            if (error.estado === 401) window.location.reload();
        }
        try {
            const filas = await API.get("/api/panel/bitacora");
            document.getElementById("panel-bitacora").innerHTML = filas.map((f) => `
                <li>
                    <span class="bit-meta">${esc((f.fecha || "").slice(11, 19))} · ${esc(f.investigador)} · ${esc(f.operacion)}
                        ${f.docs_examinados !== null && f.docs_examinados !== undefined ? ` · examinó ${f.docs_examinados} docs` : ""}
                        ${f.indice ? ` · ${esc(f.indice)}` : ""}</span>
                    <code>${esc(f.comando.replace(/\s+/g, " "))}</code>
                </li>`).join("") || "<li>Sin operaciones todavía.</li>";
        } catch (error) { /* reintenta en el próximo ciclo */ }
    }

    // Administración de documentos
    const selectPokemon = document.getElementById("editar-pokemon");
    API.get("/api/panel/pokemon").then((lista) => {
        selectPokemon.innerHTML = lista.map((p) => `<option value="${p.numero}">#${p.numero} ${esc(p.nombre)}</option>`).join("");
    });

    document.getElementById("form-editar").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const datos = Object.fromEntries(new FormData(evento.target));
        const salida = document.getElementById("editar-resultado");
        salida.classList.remove("hidden");
        try {
            const r = await API.post("/api/panel/editar", datos);
            salida.innerHTML = `${esc(r.comando)}\n// documentos modificados: ${r.modificados}\n\n${resaltarJSON(r.documento)}`;
        } catch (error) {
            salida.textContent = `${error.comando ? error.comando + "\n" : ""}// ${error.error}`;
        }
    });

    async function reiniciar(borrar) {
        const aviso = borrar
            ? "Se borran todos los investigadores, sus puntos y la bitácora. ¿Seguro?"
            : "Se recarga la Pokédex original (se pierden las formas registradas). ¿Seguro?";
        if (!window.confirm(aviso)) return;
        const salida = document.getElementById("reiniciar-resultado");
        try {
            const r = await API.post("/api/panel/reiniciar", { borrar_investigadores: borrar });
            salida.textContent = `Listo: ${r.pokemon} Pokémon, ${r.misiones} misiones, ${r.investigadores} investigadores.`;
            refrescar();
        } catch (error) {
            salida.textContent = error.error || "No se pudo reiniciar.";
        }
    }
    document.getElementById("reiniciar-pokedex").addEventListener("click", () => reiniciar(false));
    document.getElementById("reiniciar-todo").addEventListener("click", () => reiniciar(true));

    refrescar();
    setInterval(refrescar, 4000);
})();
