// Terminal de la Pokédex: la interfaz donde el investigador opera sobre MongoDB.
// Cada misión abre una herramienta distinta: consultas find(), pipeline de agregación,
// registro de formas (escrituras) y comparación de planes de ejecución (índices).
const Terminal = (() => {
    const overlay = document.getElementById("terminal");
    const cuerpo = document.getElementById("terminal-body");
    const feedback = document.getElementById("terminal-feedback");
    const textoPista = document.getElementById("terminal-hint-text");

    let mision = null;
    let callbacks = {};
    let catalogo = null;

    // ------------------------------------------------------------------
    // Apertura y cierre
    // ------------------------------------------------------------------

    async function abrir(nuevaMision, opciones = {}) {
        mision = nuevaMision;
        callbacks = opciones;
        document.getElementById("terminal-sprite").textContent = mision.sprite;
        document.getElementById("terminal-trainer").textContent = mision.entrenador.toUpperCase();
        document.getElementById("terminal-request").textContent = mision.pedido;
        document.getElementById("terminal-concept").textContent = mision.concepto;
        textoPista.textContent = mision.pista;
        textoPista.classList.add("hidden");
        limpiarFeedback();
        cuerpo.innerHTML = '<p class="cargando">Conectando con la Pokédex...</p>';
        overlay.classList.remove("hidden");
        overlay.scrollTop = 0;

        try {
            if (!catalogo) catalogo = await API.get("/api/catalogo");
            const renderizar = {
                busqueda: renderBusqueda,
                agregacion: renderAgregacion,
                registro: renderRegistro,
                indices: renderIndices,
            }[mision.tipo];
            await renderizar();
        } catch (error) {
            cuerpo.innerHTML = `<p class="error-texto">${esc(error.error || "No se pudo abrir la terminal.")}</p>`;
        }
    }

    function cerrar() {
        overlay.classList.add("hidden");
        if (callbacks.alCerrar) callbacks.alCerrar();
    }

    document.getElementById("terminal-close").addEventListener("click", cerrar);
    document.getElementById("terminal-hint").addEventListener("click", () => {
        textoPista.classList.toggle("hidden");
    });
    document.getElementById("terminal-notebook").addEventListener("click", () => window.Cuaderno?.abrir());

    // ------------------------------------------------------------------
    // Devoluciones del servidor
    // ------------------------------------------------------------------

    function limpiarFeedback() {
        feedback.className = "terminal-feedback hidden";
        feedback.innerHTML = "";
    }

    function mostrarError(texto) {
        feedback.className = "terminal-feedback error";
        feedback.innerHTML = `<p>${esc(texto)}</p>`;
        feedback.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function mostrarResultado(resultado) {
        if (resultado.perfil && callbacks.alActualizarPerfil) callbacks.alActualizarPerfil(resultado.perfil);

        if (!resultado.correcta) {
            let html = `<p class="feedback-titulo">✗ ${esc(resultado.mensaje)}</p>`;
            const lista = (titulo, items) => items?.length
                ? `<p class="feedback-sub">${titulo}</p><ul>${items.map((p) =>
                    `<li><strong>#${esc(p.numero)} ${esc(p.nombre)}</strong>: ${esc(p.motivo)}</li>`).join("")}</ul>`
                : "";
            html += lista("SOBRAN", resultado.sobran);
            html += lista("FALTAN", resultado.faltan);
            feedback.className = "terminal-feedback error";
            feedback.innerHTML = html;
            feedback.scrollIntoView({ behavior: "smooth", block: "nearest" });
            return;
        }

        const puntos = resultado.puntos_ganados
            ? `<p class="feedback-puntos">+${resultado.puntos_ganados} PUNTOS</p>`
            : (resultado.ya_completada ? '<p class="feedback-puntos">MISIÓN YA COMPLETADA · SIN PUNTOS NUEVOS</p>' : "");
        feedback.className = "terminal-feedback exito";
        feedback.innerHTML = `
            <p class="feedback-titulo">✓ ¡MISIÓN CUMPLIDA!</p>
            ${puntos}
            <p>${esc(resultado.mensaje)}</p>
            <button type="button" class="btn" id="volver-laboratorio">VOLVER AL LABORATORIO</button>`;
        document.getElementById("volver-laboratorio").addEventListener("click", () => {
            overlay.classList.add("hidden");
            if (callbacks.alCompletar) callbacks.alCompletar(resultado);
        });
        feedback.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    async function entregar(datos) {
        limpiarFeedback();
        try {
            mostrarResultado(await API.post(`/api/misiones/${mision.clave}/entregar`, datos));
        } catch (error) {
            mostrarError(error.error || "No se pudo entregar.");
        }
    }

    // ------------------------------------------------------------------
    // Visor de documentos
    // ------------------------------------------------------------------

    const visor = document.getElementById("doc-viewer");
    document.getElementById("doc-close").addEventListener("click", () => visor.classList.add("hidden"));

    function verDocumento(doc, resaltarForma) {
        document.getElementById("doc-title").textContent = `#${doc.numero} ${doc.nombre}`;
        document.getElementById("doc-json").innerHTML = resaltarJSON(doc);
        const filas = [
            ["pokemon", 1, "numero, nombre, generación y las 6 estadísticas como columnas"],
            ["pokemon_tipo", (doc.tipos || []).length, "una fila por tipo"],
            ["pokemon_habilidad", (doc.habilidades || []).length, "una fila por habilidad (con la columna oculta)"],
            ["habilidad", (doc.habilidades || []).length, "catálogo de habilidades"],
            ["pokemon_movimiento", (doc.movimientos || []).length, "una fila por movimiento aprendido"],
            ["movimiento", (doc.movimientos || []).length, "catálogo de movimientos"],
            ["forma", (doc.formas || []).length, "una fila por forma alternativa"],
        ];
        const total = filas.reduce((suma, fila) => suma + fila[1], 0);
        const extras = Object.keys(doc).filter((k) =>
            !["_id", "numero", "nombre", "generacion", "tipos", "estadisticas", "habilidades", "movimientos", "formas"].includes(k));
        document.getElementById("doc-sql").innerHTML = `
            <table class="tabla">
                <thead><tr><th>Tabla</th><th>Filas</th><th>Contenido</th></tr></thead>
                <tbody>${filas.map(([tabla, n, detalle]) =>
                    `<tr><td><code>${tabla}</code></td><td>${n}</td><td>${detalle}</td></tr>`).join("")}</tbody>
            </table>
            <p class="doc-resumen">En MongoDB: <strong>1 documento</strong>, una sola lectura.<br>
               En SQL: <strong>${total} filas en 7 tablas</strong> que hay que unir con JOIN.</p>
            ${extras.length ? `<p class="doc-resumen">Campos que solo tiene este documento:
                ${extras.map((k) => `<code>${esc(k)}</code>`).join(" ")} → en SQL serían columnas nuevas
                (ALTER TABLE) o una tabla aparte.</p>` : ""}
            ${resaltarForma ? `<p class="doc-resumen destacado">Tu forma está embebida dentro del array
                <code>formas</code> de este documento.</p>` : ""}`;
        visor.classList.remove("hidden");
    }

    
    function tarjetaPokemon(doc) {
        const tipos = (doc.tipos || [])
            .map((t) => `<span class="tipo">${esc(t)}</span>`)
            .join("");

        const vel = doc.estadisticas
            ? `VEL ${esc(doc.estadisticas.velocidad)}`
            : "";

        const iniciales = esc(
            String(doc.nombre || "?").slice(0, 2).toUpperCase()
        );

        const sprite = doc.sprite
            ? `<img
                    src="/static/assets/pokemon/${encodeURIComponent(doc.sprite)}"
                    alt="${esc(doc.nombre)}"
                    onerror="this.replaceWith(Object.assign(document.createElement('span'), {
                        className: 'poke-sprite-fallback',
                        textContent: '${iniciales}'
                    }))"
                >`
            : `<span class="poke-sprite-fallback">${iniciales}</span>`;

        return `
            <button type="button" class="poke-card" data-numero="${esc(doc.numero)}">
                <span class="poke-sprite">
                    ${sprite}
                </span>
                <span class="poke-info">
                    <span class="poke-nombre">#${esc(doc.numero)} ${esc(doc.nombre)}</span>
                    <span class="poke-tipos">${tipos}</span>
                    <span class="poke-stat">${vel}</span>
                </span>
                <span class="poke-ver">VER DOC</span>
            </button>`;
    }


    function textoPlan(plan) {
        if (!plan || !plan.disponible) return "";
        const indice = plan.indice ? `usando el índice <code>${esc(plan.indice)}</code>` : "sin índice";
        return `Plan: <code>${esc((plan.etapas || []).join(" → "))}</code> ${indice} ·
                examinó <strong>${esc(plan.docs_examinados)}</strong> documentos y
                <strong>${esc(plan.claves_examinadas)}</strong> claves de índice`;
    }

    // ------------------------------------------------------------------
    // Misión de búsqueda: constructor de consultas find()
    // ------------------------------------------------------------------

    function operadoresPara(meta) {
        const todos = catalogo.operadores;
        if (meta.tipo === "entero") return todos;
        const permitidos = meta.tipo === "booleano"
            ? ["$eq", "$ne", "$exists"]
            : ["$eq", "$ne", "$in", "$nin", "$exists"];
        return todos.filter((o) => permitidos.includes(o.op));
    }

    async function renderBusqueda() {
        const estado = {
            modo: "visual",
            condiciones: [{ campo: "nombre", operador: "$eq", valor: "" }],
            elemMatch: new Set(),
        };

        cuerpo.innerHTML = `
            <div class="tabs" role="tablist">
                <button type="button" class="tab activa" data-modo="visual">CONSTRUCTOR</button>
                <button type="button" class="tab" data-modo="texto">ESCRIBIR CONSULTA</button>
            </div>
            <section data-panel="visual">
                <p class="etiqueta">FILTRO · CONDICIONES SOBRE LOS DOCUMENTOS DE pokemon</p>
                <div id="condiciones" class="condiciones"></div>
                <button type="button" id="agregar-condicion" class="btn-sec">+ AGREGAR CONDICIÓN</button>
                <div id="elem-match" class="elem-match"></div>
            </section>
            <section data-panel="texto" class="hidden">
                <p class="etiqueta">FILTRO EN SINTAXIS DE MONGODB</p>
                <textarea id="filtro-texto" class="editor" spellcheck="false" rows="6"
                    placeholder='{ "tipos": "Agua", "estadisticas.velocidad": { "$gt": 80 } }'></textarea>
                <p class="ayuda">Podés escribir solo el filtro o el comando completo db.pokemon.find({...}).</p>
            </section>
            <div class="vista-previa">
                <div>
                    <p class="etiqueta">MONGODB</p>
                    <pre id="previa-mongo" class="codigo"></pre>
                </div>
                <div id="previa-sql-caja">
                    <p class="etiqueta">SQL EQUIVALENTE · MODELO RELACIONAL</p>
                    <pre id="previa-sql" class="codigo sql"></pre>
                    <p id="previa-tablas" class="ayuda"></p>
                </div>
            </div>
            <div class="acciones">
                <button type="button" id="ejecutar" class="btn">▶ EJECUTAR CONSULTA</button>
                <button type="button" id="entregar" class="btn btn-entregar">ENTREGAR RESULTADOS</button>
            </div>
            <div id="resultados" class="resultados"></div>`;

        const contenedor = document.getElementById("condiciones");
        const cajaElem = document.getElementById("elem-match");
        const textarea = document.getElementById("filtro-texto");

        function pedido() {
            if (estado.modo === "texto") return { modo: "texto", texto: textarea.value };
            return { modo: "visual", condiciones: estado.condiciones, elem_match: [...estado.elemMatch] };
        }

        function pintarCondiciones() {
            contenedor.innerHTML = "";
            estado.condiciones.forEach((condicion, i) => {
                const meta = catalogo.campos.find((c) => c.campo === condicion.campo);
                const operadores = operadoresPara(meta);
                if (!operadores.some((o) => o.op === condicion.operador)) condicion.operador = "$eq";

                const fila = document.createElement("div");
                fila.className = "condicion";
                fila.innerHTML = `
                    <select class="c-campo" aria-label="Campo">
                        ${catalogo.campos.map((c) => `<option value="${esc(c.campo)}" ${c.campo === condicion.campo ? "selected" : ""}>${esc(c.etiqueta)}</option>`).join("")}
                    </select>
                    <select class="c-operador" aria-label="Operador">
                        ${operadores.map((o) => `<option value="${o.op}" ${o.op === condicion.operador ? "selected" : ""}>${esc(o.op)}  ${esc(o.etiqueta)}</option>`).join("")}
                    </select>
                    <span class="c-valor-caja"></span>
                    <button type="button" class="c-quitar" aria-label="Quitar condición">✕</button>`;

                const cajaValor = fila.querySelector(".c-valor-caja");
                cajaValor.appendChild(inputValor(meta, condicion));

                fila.querySelector(".c-campo").addEventListener("change", (e) => {
                    condicion.campo = e.target.value;
                    condicion.valor = "";
                    pintarCondiciones();
                    actualizarPrevia();
                });
                fila.querySelector(".c-operador").addEventListener("change", (e) => {
                    condicion.operador = e.target.value;
                    if (condicion.operador === "$exists") condicion.valor = "true";
                    pintarCondiciones();
                    actualizarPrevia();
                });
                fila.querySelector(".c-quitar").addEventListener("click", () => {
                    estado.condiciones.splice(i, 1);
                    pintarCondiciones();
                    actualizarPrevia();
                });
                contenedor.appendChild(fila);
            });
            pintarElemMatch();
        }

        function inputValor(meta, condicion) {
            let elemento;
            const lista = ["$in", "$nin"].includes(condicion.operador);
            if (condicion.operador === "$exists" || (meta.tipo === "booleano" && !lista)) {
                elemento = document.createElement("select");
                elemento.innerHTML = '<option value="true">true</option><option value="false">false</option>';
                if (condicion.valor === "" || condicion.valor === undefined) condicion.valor = "true";
                elemento.value = String(condicion.valor);
            } else if (meta.opciones && !lista) {
                elemento = document.createElement("select");
                elemento.innerHTML = '<option value="">— elegí —</option>' +
                    meta.opciones.map((o) => `<option value="${esc(o)}">${esc(o)}</option>`).join("");
                elemento.value = condicion.valor;
            } else {
                elemento = document.createElement("input");
                elemento.type = meta.tipo === "entero" && !lista ? "number" : "text";
                elemento.inputMode = meta.tipo === "entero" ? "numeric" : "text";
                elemento.placeholder = lista ? "valor1, valor2" : (meta.tipo === "entero" ? "número" : "valor");
                elemento.value = condicion.valor ?? "";
                const sugerencias = catalogo.valores[meta.campo] || (meta.opciones || []);
                if (sugerencias.length) {
                    const id = `lista-${meta.campo.replaceAll(".", "-")}`;
                    if (!document.getElementById(id)) {
                        const datalist = document.createElement("datalist");
                        datalist.id = id;
                        datalist.innerHTML = sugerencias.map((v) => `<option value="${esc(v)}">`).join("");
                        document.body.appendChild(datalist);
                    }
                    elemento.setAttribute("list", id);
                }
            }
            elemento.className = "c-valor";
            elemento.setAttribute("aria-label", "Valor");
            const actualizar = () => {
                condicion.valor = elemento.value;
                actualizarPrevia();
            };
            elemento.addEventListener("input", actualizar);
            elemento.addEventListener("change", actualizar);
            return elemento;
        }

        function pintarElemMatch() {
            const conteo = {};
            estado.condiciones.forEach((c) => {
                const meta = catalogo.campos.find((m) => m.campo === c.campo);
                if (meta.grupo) conteo[meta.grupo] = (conteo[meta.grupo] || 0) + 1;
            });
            [...estado.elemMatch].forEach((g) => { if ((conteo[g] || 0) < 2) estado.elemMatch.delete(g); });
            cajaElem.innerHTML = Object.entries(conteo).filter(([, n]) => n >= 2).map(([grupo, n]) => `
                <label class="elem-opcion">
                    <input type="checkbox" data-grupo="${esc(grupo)}" ${estado.elemMatch.has(grupo) ? "checked" : ""}>
                    Las ${n} condiciones sobre <code>${esc(grupo)}</code> deben cumplirse en el MISMO elemento
                    del array (<code>$elemMatch</code>)
                </label>`).join("");
            cajaElem.querySelectorAll("input").forEach((check) => {
                check.addEventListener("change", () => {
                    if (check.checked) estado.elemMatch.add(check.dataset.grupo);
                    else estado.elemMatch.delete(check.dataset.grupo);
                    actualizarPrevia();
                });
            });
        }

        let temporizador = null;
        let secuencia = 0;
        function actualizarPrevia() {
            clearTimeout(temporizador);
            temporizador = setTimeout(async () => {
                const numero = ++secuencia;
                try {
                    const previa = await API.post("/api/consultas/previsualizar", pedido());
                    if (numero !== secuencia) return;
                    document.getElementById("previa-mongo").textContent = previa.comando;
                    const cajaSql = document.getElementById("previa-sql-caja");
                    if (previa.sql) {
                        cajaSql.classList.remove("hidden");
                        document.getElementById("previa-sql").textContent = previa.sql;
                        document.getElementById("previa-tablas").textContent =
                            `Tablas involucradas: ${previa.tablas.join(", ")}`;
                    } else {
                        cajaSql.classList.add("hidden");
                    }
                } catch (error) {
                    if (numero !== secuencia) return;
                    document.getElementById("previa-mongo").textContent = `// ${error.error || "Consulta incompleta"}`;
                }
            }, 250);
        }

        cuerpo.querySelectorAll(".tab").forEach((tab) => {
            tab.addEventListener("click", async () => {
                const nuevoModo = tab.dataset.modo;
                if (nuevoModo === estado.modo) return;
                if (nuevoModo === "texto" && !textarea.value.trim()) {
                    try {
                        const previa = await API.post("/api/consultas/previsualizar", pedido());
                        textarea.value = JSON.stringify(previa.filtro, null, 2);
                    } catch (error) { /* se deja vacío */ }
                }
                estado.modo = nuevoModo;
                cuerpo.querySelectorAll(".tab").forEach((t) => t.classList.toggle("activa", t === tab));
                cuerpo.querySelector('[data-panel="visual"]').classList.toggle("hidden", estado.modo !== "visual");
                cuerpo.querySelector('[data-panel="texto"]').classList.toggle("hidden", estado.modo !== "texto");
                actualizarPrevia();
            });
        });
        textarea.addEventListener("input", actualizarPrevia);

        document.getElementById("agregar-condicion").addEventListener("click", () => {
            if (estado.condiciones.length >= 8) return;
            estado.condiciones.push({ campo: "estadisticas.velocidad", operador: "$gt", valor: "" });
            pintarCondiciones();
            actualizarPrevia();
        });

        document.getElementById("ejecutar").addEventListener("click", async () => {
            limpiarFeedback();
            const caja = document.getElementById("resultados");
            caja.innerHTML = '<p class="cargando">Ejecutando en MongoDB...</p>';
            try {
                const r = await API.post("/api/consultas/buscar", pedido());
                const mas = r.total > r.documentos.length ? ` (se muestran ${r.documentos.length})` : "";
                caja.innerHTML = `
                    <p class="resultado-resumen"><strong>${r.total}</strong> documento${r.total === 1 ? "" : "s"} encontrado${r.total === 1 ? "" : "s"}${mas}</p>
                    <p class="resultado-plan">${textoPlan(r.plan)}</p>
                    <div class="poke-grid">${r.documentos.map(tarjetaPokemon).join("")}</div>`;
                caja.querySelectorAll(".poke-card").forEach((boton) => {
                    boton.addEventListener("click", () => {
                        const doc = r.documentos.find((d) => String(d.numero) === boton.dataset.numero);
                        verDocumento(doc);
                    });
                });
            } catch (error) {
                caja.innerHTML = "";
                mostrarError(error.error || "La consulta falló.");
            }
        });

        document.getElementById("entregar").addEventListener("click", () => entregar(pedido()));

        pintarCondiciones();
        actualizarPrevia();
    }

    // ------------------------------------------------------------------
    // Misión de agregación: armar el pipeline con tarjetas
    // ------------------------------------------------------------------

    async function renderAgregacion() {
        const tarjetas = await API.get("/api/agregacion/tarjetas");
        const estado = { modo: "visual", pipeline: [] };

        cuerpo.innerHTML = `
            <div class="tabs" role="tablist">
                <button type="button" class="tab activa" data-modo="visual">TARJETAS</button>
                <button type="button" class="tab" data-modo="texto">ESCRIBIR PIPELINE</button>
            </div>
            <section data-panel="visual">
                <p class="etiqueta">ETAPAS DISPONIBLES · TOCÁ UNA PARA SUMARLA AL PIPELINE</p>
                <div class="paleta">${tarjetas.map((t) => `
                    <button type="button" class="tarjeta" data-id="${esc(t.id)}">
                        <code>${esc(t.texto)}</code>
                        <small>${esc(t.explicacion)}</small>
                    </button>`).join("")}
                </div>
                <p class="etiqueta">TU PIPELINE · SE EJECUTA DE ARRIBA HACIA ABAJO</p>
                <ol id="pipeline" class="pipeline"></ol>
            </section>
            <section data-panel="texto" class="hidden">
                <p class="etiqueta">PIPELINE EN JSON (LISTA DE ETAPAS)</p>
                <textarea id="pipeline-texto" class="editor" spellcheck="false" rows="8"
                    placeholder='[ { "$match": { "generacion": 1 } } ]'></textarea>
            </section>
            <div class="acciones">
                <button type="button" id="ejecutar" class="btn">▶ EJECUTAR PIPELINE</button>
                <button type="button" id="entregar" class="btn btn-entregar">ENTREGAR RESULTADO</button>
            </div>
            <div id="resultados" class="resultados"></div>`;

        const lista = document.getElementById("pipeline");
        const textarea = document.getElementById("pipeline-texto");

        function pedido() {
            return estado.modo === "texto"
                ? { modo: "texto", texto: textarea.value }
                : { modo: "visual", tarjetas: estado.pipeline };
        }

        function pintarPipeline() {
            if (!estado.pipeline.length) {
                lista.innerHTML = '<li class="vacio">Todavía no agregaste etapas.</li>';
                return;
            }
            lista.innerHTML = estado.pipeline.map((id, i) => {
                const t = tarjetas.find((x) => x.id === id);
                return `
                    <li class="etapa">
                        <span class="etapa-num">${i + 1}</span>
                        <code>${esc(t.texto)}</code>
                        <span class="etapa-botones">
                            <button type="button" data-accion="subir" data-i="${i}" aria-label="Subir">▲</button>
                            <button type="button" data-accion="bajar" data-i="${i}" aria-label="Bajar">▼</button>
                            <button type="button" data-accion="quitar" data-i="${i}" aria-label="Quitar">✕</button>
                        </span>
                    </li>`;
            }).join("");
            lista.querySelectorAll("button").forEach((boton) => {
                boton.addEventListener("click", () => {
                    const i = Number(boton.dataset.i);
                    const p = estado.pipeline;
                    if (boton.dataset.accion === "quitar") p.splice(i, 1);
                    if (boton.dataset.accion === "subir" && i > 0) [p[i - 1], p[i]] = [p[i], p[i - 1]];
                    if (boton.dataset.accion === "bajar" && i < p.length - 1) [p[i + 1], p[i]] = [p[i], p[i + 1]];
                    pintarPipeline();
                });
            });
        }

        cuerpo.querySelectorAll(".tarjeta").forEach((boton) => {
            boton.addEventListener("click", () => {
                if (estado.pipeline.length >= 8) return;
                estado.pipeline.push(boton.dataset.id);
                pintarPipeline();
            });
        });

        cuerpo.querySelectorAll(".tab").forEach((tab) => {
            tab.addEventListener("click", () => {
                if (tab.dataset.modo === estado.modo) return;
                estado.modo = tab.dataset.modo;
                if (estado.modo === "texto" && !textarea.value.trim() && estado.pipeline.length) {
                    textarea.value = JSON.stringify(
                        estado.pipeline.map((id) => tarjetas.find((t) => t.id === id).etapa), null, 2);
                }
                cuerpo.querySelectorAll(".tab").forEach((t) => t.classList.toggle("activa", t === tab));
                cuerpo.querySelector('[data-panel="visual"]').classList.toggle("hidden", estado.modo !== "visual");
                cuerpo.querySelector('[data-panel="texto"]').classList.toggle("hidden", estado.modo !== "texto");
            });
        });

        document.getElementById("ejecutar").addEventListener("click", async () => {
            limpiarFeedback();
            const caja = document.getElementById("resultados");
            caja.innerHTML = '<p class="cargando">Ejecutando el pipeline en MongoDB...</p>';
            try {
                const r = await API.post("/api/agregacion/ejecutar", pedido());
                caja.innerHTML = `
                    <p class="etiqueta">COMANDO EJECUTADO</p>
                    <pre class="codigo">${esc(r.comando)}</pre>
                    <p class="etiqueta">QUÉ SALIÓ DE CADA ETAPA</p>
                    ${r.etapas.map((e, i) => `
                        <details class="etapa-resultado" ${i === r.etapas.length - 1 ? "open" : ""}>
                            <summary><span class="etapa-num">${i + 1}</span> <code>${esc(e.operador)}</code>
                                → <strong>${e.cantidad}</strong> documento${e.cantidad === 1 ? "" : "s"}</summary>
                            <pre class="codigo json">${resaltarJSON(e.muestra)}${e.cantidad > e.muestra.length ? "\n..." : ""}</pre>
                        </details>`).join("")}
                    <p class="etiqueta">RESULTADO FINAL</p>
                    <pre class="codigo json">${resaltarJSON(r.resultado)}</pre>`;
            } catch (error) {
                caja.innerHTML = "";
                mostrarError(error.error || "El pipeline falló.");
            }
        });

        document.getElementById("entregar").addEventListener("click", () => entregar(pedido()));
        pintarPipeline();
    }

    // ------------------------------------------------------------------
    // Misión de registro: escribir una forma embebida ($push / $set posicional)
    // ------------------------------------------------------------------

    async function renderRegistro() {
        const datos = await API.get("/api/formas/avistamiento");
        const a = datos.avistamiento;
        const stats = catalogo.estadisticas;

        cuerpo.innerHTML = `
            <article class="ficha">
                <p class="ficha-titulo">FICHA DE AVISTAMIENTO · ${esc(a.forma.toUpperCase())}</p>
                <p class="ficha-relato">${esc(a.relato)}</p>
                <dl class="ficha-datos">
                    <dt>Pokémon base</dt><dd>#${esc(a.numero)} ${esc(a.pokemon)}</dd>
                    <dt>Nombre de la forma</dt><dd>${esc(a.forma)}</dd>
                    <dt>Tipos</dt><dd>${a.tipos.map(esc).join(" / ")}</dd>
                    <dt>Habilidad</dt><dd>${esc(a.habilidad)}</dd>
                    <dt>Estadísticas</dt><dd>${stats.map((s) => `${esc(s)}: ${esc(a.estadisticas[s])}`).join(" · ")}</dd>
                    <dt>Dato especial</dt><dd>${esc(a.dato_especial.descripcion)}: <strong>${esc(a.dato_especial.valor)}</strong>
                        <br><small>Ningún otro Pokémon tiene este campo. Guardalo con el nombre de campo que elijas.</small></dd>
                </dl>
                <button type="button" id="ver-doc-base" class="btn-sec">VER DOCUMENTO DE ${esc(a.pokemon.toUpperCase())}</button>
            </article>
            <div id="registro-zona"></div>`;

        document.getElementById("ver-doc-base").addEventListener("click", async () => {
            verDocumento(await API.get(`/api/pokemon/${a.numero}`));
        });

        if (datos.ya_registrada) pintarAgregarDato(a, datos.forma_existente);
        else pintarFormulario(a);
    }

    function pintarFormulario(a) {
        const zona = document.getElementById("registro-zona");
        const stats = catalogo.estadisticas;
        const opcionesTipo = catalogo.tipos.map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join("");
        zona.innerHTML = `
            <form id="form-forma" class="form-forma">
                <p class="etiqueta">NUEVA FORMA · SE GUARDA DENTRO DEL DOCUMENTO DEL POKÉMON</p>
                <label>Pokémon base
                    <select name="numero">
                        <option value="">— elegí —</option>
                        ${catalogo.pokemon.map((p) => `<option value="${p.numero}">#${p.numero} ${esc(p.nombre)}</option>`).join("")}
                    </select>
                </label>
                <label>nombre <input name="nombre" maxlength="40" autocomplete="off"></label>
                <div class="fila-doble">
                    <label>tipos[0] <select name="tipo1"><option value="">—</option>${opcionesTipo}</select></label>
                    <label>tipos[1] <select name="tipo2"><option value="">(ninguno)</option>${opcionesTipo}</select></label>
                </div>
                <fieldset class="stats">
                    <legend>estadisticas { }</legend>
                    ${stats.map((s) => `<label>${esc(s)} <input name="stat-${s}" type="number" min="1" max="255" inputmode="numeric"></label>`).join("")}
                </fieldset>
                <label>habilidad <input name="habilidad" maxlength="40" autocomplete="off"></label>
                <fieldset class="extras">
                    <legend>CAMPOS EXTRA (ESQUEMA FLEXIBLE)</legend>
                    <div id="extras"></div>
                    <button type="button" id="agregar-extra" class="btn-sec">+ AGREGAR CAMPO</button>
                </fieldset>
                <p class="etiqueta">OPERACIÓN QUE SE VA A EJECUTAR</p>
                <pre id="previa-forma" class="codigo"></pre>
                <button type="submit" class="btn btn-entregar">REGISTRAR FORMA ($push)</button>
            </form>`;

        const form = document.getElementById("form-forma");
        const extras = document.getElementById("extras");

        function filaExtra() {
            const fila = document.createElement("div");
            fila.className = "extra";
            fila.innerHTML = `
                <input class="extra-campo" placeholder="nombre_del_campo" maxlength="30" autocomplete="off" aria-label="Nombre del campo">
                <input class="extra-valor" placeholder="valor" maxlength="60" autocomplete="off" aria-label="Valor">
                <button type="button" class="c-quitar" aria-label="Quitar">✕</button>`;
            fila.querySelector(".c-quitar").addEventListener("click", () => { fila.remove(); previa(); });
            fila.querySelectorAll("input").forEach((i) => i.addEventListener("input", previa));
            extras.appendChild(fila);
        }

        function leer() {
            const f = new FormData(form);
            const tipos = [f.get("tipo1"), f.get("tipo2")].filter(Boolean);
            const estadisticas = {};
            stats.forEach((s) => { estadisticas[s] = f.get(`stat-${s}`); });
            return {
                numero: f.get("numero"),
                nombre: (f.get("nombre") || "").trim(),
                tipos,
                estadisticas,
                habilidad: (f.get("habilidad") || "").trim(),
                extras: [...extras.querySelectorAll(".extra")].map((fila) => ({
                    campo: fila.querySelector(".extra-campo").value,
                    valor: fila.querySelector(".extra-valor").value,
                })),
            };
        }

        function previa() {
            const d = leer();
            const forma = { nombre: d.nombre, tipos: d.tipos, estadisticas: {} };
            stats.forEach((s) => { forma.estadisticas[s] = Number(d.estadisticas[s]) || null; });
            forma.habilidad = d.habilidad;
            d.extras.filter((e) => e.campo.trim()).forEach((e) => {
                const valor = e.valor.trim();
                forma[e.campo.trim().toLowerCase().replaceAll(" ", "_")] = /^-?\d+([.,]\d+)?$/.test(valor) ? Number(valor.replace(",", ".")) : valor;
            });
            forma.registrada_por = window.POKELAB.nombre;
            document.getElementById("previa-forma").textContent =
                `db.pokemon.updateOne(\n  { numero: ${d.numero || "?"}, "formas.nombre": { $ne: ${JSON.stringify(d.nombre)} } },\n` +
                `  { $push: { formas: ${JSON.stringify(forma, null, 2).replaceAll("\n", "\n    ")} } }\n)`;
        }

        form.addEventListener("input", previa);
        form.addEventListener("change", previa);
        document.getElementById("agregar-extra").addEventListener("click", () => { filaExtra(); previa(); });
        filaExtra();
        previa();

        form.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            limpiarFeedback();
            try {
                const r = await API.post("/api/formas", leer());
                mostrarResultado(r);
                mostrarEscritura(r);
            } catch (error) {
                if (error.estado === 409) {
                    mostrarError(error.error);
                    pintarAgregarDato(a, error.forma_existente);
                } else {
                    mostrarError(error.error || "No se pudo registrar la forma.");
                }
            }
        });
    }

    function pintarAgregarDato(a, formaExistente) {
        const zona = document.getElementById("registro-zona");
        zona.innerHTML = `
            <div class="form-forma">
                <p class="etiqueta">ESTA FORMA YA ESTÁ REGISTRADA (POR ${esc(formaExistente?.registrada_por || "otro investigador")})</p>
                <pre class="codigo json">${resaltarJSON(formaExistente)}</pre>
                <p>Sumale un dato de campo NUEVO que todavía no tenga (por ejemplo <code>lugar_avistamiento</code>,
                   <code>clima</code> o <code>altura_m</code>). Se modifica solo ese elemento del array con el
                   operador posicional <code>$</code>.</p>
                <div class="extra">
                    <input id="dato-campo" placeholder="nombre_del_campo" maxlength="30" autocomplete="off" aria-label="Nombre del campo">
                    <input id="dato-valor" placeholder="valor" maxlength="60" autocomplete="off" aria-label="Valor">
                </div>
                <p class="etiqueta">OPERACIÓN QUE SE VA A EJECUTAR</p>
                <pre id="previa-dato" class="codigo"></pre>
                <button type="button" id="agregar-dato" class="btn btn-entregar">AGREGAR DATO ($set posicional)</button>
            </div>`;
        const campo = document.getElementById("dato-campo");
        const valor = document.getElementById("dato-valor");
        const previa = () => {
            const nombre = campo.value.trim().toLowerCase().replaceAll(" ", "_") || "campo";
            document.getElementById("previa-dato").textContent =
                `db.pokemon.updateOne(\n  { numero: ${a.numero}, "formas.nombre": ${JSON.stringify(a.forma)} },\n` +
                `  { $set: { "formas.$.${nombre}": ${JSON.stringify(valor.value.trim())} } }\n)`;
        };
        campo.addEventListener("input", previa);
        valor.addEventListener("input", previa);
        previa();
        document.getElementById("agregar-dato").addEventListener("click", async () => {
            limpiarFeedback();
            try {
                const r = await API.post("/api/formas/dato", { campo: campo.value, valor: valor.value });
                mostrarResultado(r);
                mostrarEscritura(r);
            } catch (error) {
                mostrarError(error.error || "No se pudo agregar el dato.");
            }
        });
    }

    function mostrarEscritura(resultado) {
        const zona = document.getElementById("registro-zona");
        zona.innerHTML = `
            <p class="etiqueta">OPERACIÓN EJECUTADA EN MONGODB</p>
            <pre class="codigo">${esc(resultado.comando)}</pre>
            <button type="button" id="ver-resultado" class="btn-sec">VER EL DOCUMENTO ACTUALIZADO</button>`;
        document.getElementById("ver-resultado").addEventListener("click", () => verDocumento(resultado.documento, true));
    }

    // ------------------------------------------------------------------
    // Misión de índices: comparar planes de ejecución con explain()
    // ------------------------------------------------------------------

    async function renderIndices() {
        const info = await API.get("/api/indices/planes");
        cuerpo.innerHTML = `
            <p class="etiqueta">CONSULTA A OPTIMIZAR</p>
            <pre class="codigo">db.pokemon.find(${esc(info.filtro)})</pre>
            <p class="etiqueta">ÍNDICES QUE EXISTEN EN LA COLECCIÓN pokemon</p>
            <p class="lista-indices">${info.indices.map((i) => `<code>${esc(i)}</code>`).join(" ")}</p>
            <p class="etiqueta">PLANES DE EJECUCIÓN · EJECUTÁ CADA UNO CON hint() Y COMPARÁ</p>
            <div class="tabla-scroll">
                <table class="tabla planes">
                    <thead><tr><th></th><th>Plan</th><th>Etapas</th><th>Docs examinados</th><th>Claves examinadas</th><th>Devueltos</th><th></th></tr></thead>
                    <tbody>${info.planes.map((p) => `
                        <tr data-plan="${esc(p.id)}">
                            <td><input type="radio" name="plan" value="${esc(p.id)}" aria-label="Elegir ${esc(p.etiqueta)}"></td>
                            <td>${esc(p.etiqueta)}</td>
                            <td class="p-etapas">—</td>
                            <td class="p-docs">—</td>
                            <td class="p-claves">—</td>
                            <td class="p-devueltos">—</td>
                            <td><button type="button" class="btn-sec p-ejecutar">EJECUTAR</button></td>
                        </tr>`).join("")}
                    </tbody>
                </table>
            </div>
            <pre id="comando-plan" class="codigo hidden"></pre>
            <div class="acciones">
                <button type="button" id="entregar" class="btn btn-entregar">ENTREGAR ELECCIÓN</button>
            </div>`;

        cuerpo.querySelectorAll("tr[data-plan]").forEach((fila) => {
            fila.querySelector(".p-ejecutar").addEventListener("click", async () => {
                limpiarFeedback();
                try {
                    const r = await API.post("/api/indices/probar", { plan: fila.dataset.plan });
                    if (!r.disponible) {
                        mostrarError("Este servidor de MongoDB no permite explain(). Usá MongoDB local o Atlas.");
                        return;
                    }
                    fila.querySelector(".p-etapas").textContent = (r.etapas || []).join(" → ");
                    fila.querySelector(".p-docs").textContent = r.docs_examinados;
                    fila.querySelector(".p-claves").textContent = r.claves_examinadas;
                    fila.querySelector(".p-devueltos").textContent = r.devueltos;
                    fila.classList.add("probado");
                    const comando = document.getElementById("comando-plan");
                    comando.textContent = r.comando;
                    comando.classList.remove("hidden");
                } catch (error) {
                    mostrarError(error.error || "No se pudo ejecutar el plan.");
                }
            });
        });

        document.getElementById("entregar").addEventListener("click", () => {
            const elegido = cuerpo.querySelector('input[name="plan"]:checked');
            if (!elegido) {
                mostrarError("Marcá el plan que elegís en la primera columna.");
                return;
            }
            entregar({ plan: elegido.value });
        });
    }

    return { abrir, verDocumento };
})();
