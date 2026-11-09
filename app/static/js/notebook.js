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
                <li>Consultas y filtros</li>
                <li>Inserción y actualización</li>
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

// Cerrar el cuaderno
closeNotebook.addEventListener("click", () => {
    notebookPanel.classList.add("hidden");
});

// Cerrar con Escape
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        notebookPanel.classList.add("hidden");
    }
});

// Cargar la primera página
showPage();