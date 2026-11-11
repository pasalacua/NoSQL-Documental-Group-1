const notebookButton = document.getElementById("notebook-button");
const notebookPanel = document.getElementById("notebook-panel");
const closeNotebook = document.getElementById("close-notebook");

const leftPage = document.getElementById("notebook-left");
const rightPage = document.getElementById("notebook-right");

const previousButton = document.getElementById("previous-page");
const nextPageButton = document.getElementById("next-page");
const pageIndicator = document.getElementById("page-indicator");

// Contenido de las páginas
const notebookPages = [
    {
        left: `
            <h2>CUADERNO DE INVESTIGACIÓN</h2>
            <h3>Índice</h3>
            <ul>
                <li>Documentos y colecciones</li>
                <li>Arrays y documentos anidados</li>
                <li>Consultas y operadores</li>
                <li>$elemMatch y agregación</li>
                <li>Inserción y actualización</li>
                <li>Índices y plan de ejecución</li>
                <li>MongoDB vs. SQL</li>
            </ul>
        `,
        right: `
            <h2>BASE DE DATOS</h2>
            <p>
                En este laboratorio utilizamos MongoDB,
                una base de datos NoSQL orientada a documentos.
            </p>
            <h3>¿Qué es MongoDB?</h3>
            <p>
                Es un sistema de gestión de bases de datos
                que almacena información en documentos BSON.
            </p>
        `
    },

    {
        left: `
            <h2>DOCUMENTOS</h2>
            <h3>¿Qué es un documento?</h3>
            <p>
                Es una estructura que almacena información
                mediante pares de clave y valor.
            </p>
            <p>
                Los documentos pueden contener otros documentos
                y arrays.
            </p>
        `,
        right: `
            <h2>COLECCIONES</h2>
            <h3>¿Cómo se organizan?</h3>
            <p>
                Una colección agrupa documentos relacionados.
            </p>
            <p>
                En POKÉLAB utilizaremos una colección llamada
                <strong>pokemon</strong>, donde cada Pokémon
                tendrá su propio documento.
            </p>
        `
    },

    {
        left: `
            <h2>ARRAYS</h2>
            <h3>Información agrupada</h3>
            <p>
                Los arrays permiten almacenar varios valores
                o documentos dentro de un mismo campo.
            </p>
            <p>
                Por ejemplo, un Pokémon puede tener varios tipos,
                habilidades o movimientos.
            </p>
        `,
        right: `
            <h2>DOCUMENTOS ANIDADOS</h2>
            <h3>Datos relacionados</h3>
            <p>
                Podemos incluir documentos dentro de otros
                documentos para representar información relacionada.
            </p>
            <p>
                En POKÉLAB, las estadísticas de un Pokémon
                estarán agrupadas dentro de un documento llamado
                <strong>estadisticas</strong>.
            </p>
        `
    },

    {
        left: `
            <h2>CONSULTAS</h2>
            <h3>find()</h3>
            <p>
                Para buscar documentos se usa un filtro con la misma
                forma que los documentos:
            </p>
            <p><code>db.pokemon.find({ tipos: "Agua" })</code></p>
            <h3>Notación de punto</h3>
            <p>
                Para entrar a un documento anidado o a un array de
                documentos se escribe la ruta entre comillas:
            </p>
            <p><code>{ "estadisticas.velocidad": 90 }</code></p>
            <p><code>{ "movimientos.nombre": "Surf" }</code></p>
        `,
        right: `
            <h2>OPERADORES</h2>
            <ul>
                <li><code>$eq</code> igual · <code>$ne</code> distinto</li>
                <li><code>$gt</code> mayor · <code>$gte</code> mayor o igual</li>
                <li><code>$lt</code> menor · <code>$lte</code> menor o igual</li>
                <li><code>$in</code> alguno de una lista</li>
                <li><code>$exists</code> el campo existe</li>
            </ul>
            <p>
                Varias condiciones en el mismo filtro se combinan
                con un Y lógico:
            </p>
            <p><code>{ tipos: "Fuego", "estadisticas.velocidad": { $gt: 90 } }</code></p>
        `
    },

    {
        left: `
            <h2>$elemMatch</h2>
            <h3>¿El mismo elemento?</h3>
            <p>
                En un array de documentos, dos condiciones sueltas
                pueden cumplirse con elementos DISTINTOS.
            </p>
            <p>
                <code>$elemMatch</code> exige que todas se cumplan
                en el MISMO elemento:
            </p>
            <p><code>{ habilidades: { $elemMatch: { nombre: "Sebo", oculta: true } } }</code></p>
        `,
        right: `
            <h2>AGREGACIÓN</h2>
            <h3>Pipeline</h3>
            <p>
                Una agregación es una lista de etapas. Cada etapa
                recibe documentos, los transforma y los pasa a la siguiente.
            </p>
            <ul>
                <li><code>$match</code> filtra</li>
                <li><code>$unwind</code> desarma un array</li>
                <li><code>$group</code> agrupa y calcula</li>
                <li><code>$sort</code> ordena · <code>$limit</code> recorta</li>
            </ul>
        `
    },

    {
        left: `
            <h2>ESCRITURAS</h2>
            <h3>Insertar y actualizar</h3>
            <ul>
                <li><code>insertOne</code> crea un documento</li>
                <li><code>$set</code> cambia o crea un campo</li>
                <li><code>$inc</code> suma a un número</li>
                <li><code>$push</code> agrega al final de un array</li>
                <li><code>$addToSet</code> agrega sin repetir</li>
                <li><code>$pull</code> saca de un array</li>
            </ul>
            <p>
                El operador posicional <code>formas.$.campo</code> modifica
                solo el elemento del array que coincidió con el filtro.
            </p>
        `,
        right: `
            <h2>ESQUEMA FLEXIBLE</h2>
            <p>
                Los documentos de una misma colección pueden tener
                campos distintos. Una Megaevolución guarda la piedra que
                necesita; una forma regional guarda su región.
            </p>
            <p>
                No hace falta modificar ninguna tabla: el campo nuevo
                se guarda en el documento que lo necesita.
            </p>
            <p>
                Si queremos reglas mínimas, MongoDB permite validar
                con <code>$jsonSchema</code>.
            </p>
        `
    },

    {
        left: `
            <h2>ÍNDICES</h2>
            <h3>Buscar sin leer todo</h3>
            <p>
                Sin índice, MongoDB recorre toda la colección
                (<code>COLLSCAN</code>). Con un índice salta directo a los
                documentos que sirven (<code>IXSCAN</code>).
            </p>
            <p>
                Un índice sobre un array (como <code>tipos</code>) es
                multiclave: guarda una entrada por cada elemento.
            </p>
            <p><code>.explain("executionStats")</code> muestra el plan elegido.</p>
        `,
        right: `
            <h2>MONGODB vs. SQL</h2>
            <ul>
                <li>Documento ↔ fila</li>
                <li>Colección ↔ tabla</li>
                <li>Documento embebido ↔ JOIN con otra tabla</li>
                <li>Campo nuevo ↔ ALTER TABLE</li>
                <li>Pipeline ↔ GROUP BY / ORDER BY</li>
            </ul>
            <p>
                Un Pokémon completo es UN documento en MongoDB, pero
                en SQL se reparte en varias tablas que hay que unir.
            </p>
        `
    }
];

let currentPage = 0;

// Mostrar la página actual
function showPage() {
    const page = notebookPages[currentPage];

    leftPage.innerHTML = page.left;
    rightPage.innerHTML = page.right;

    pageIndicator.textContent =
        `${currentPage + 1} / ${notebookPages.length}`;

    previousButton.disabled = currentPage === 0;
    nextPageButton.disabled = currentPage === notebookPages.length - 1;
}

// Página anterior
previousButton.addEventListener("click", () => {
    if (currentPage > 0) {
        currentPage--;
        showPage();
    }
});

// Página siguiente
nextPageButton.addEventListener("click", () => {
    if (currentPage < notebookPages.length - 1) {
        currentPage++;
        showPage();
    }
});

// Abrir el cuaderno
notebookButton.addEventListener("click", () => {
    notebookPanel.classList.remove("hidden");
});

// Permite abrir el cuaderno desde la terminal de consultas
window.Cuaderno = {
    abrir() {
        notebookPanel.classList.remove("hidden");
    },
};

// Cerrar el cuaderno
closeNotebook.addEventListener("click", () => {
    notebookPanel.classList.add("hidden");
});

// Navegación y cierre del cuaderno mediante teclado
document.addEventListener("keydown", (event) => {
    if (notebookPanel.classList.contains("hidden")) return;

    if (event.key === "Escape") {
        notebookPanel.classList.add("hidden");
        return;
    }

    if (event.key === "ArrowLeft") {
        event.preventDefault();

        if (currentPage > 0) {
            currentPage--;
            showPage();
        }
    }

    if (event.key === "ArrowRight") {
        event.preventDefault();

        if (currentPage < notebookPages.length - 1) {
            currentPage++;
            showPage();
        }
    }
});

// Cargar la primera página
showPage();