// Comunicación con el servidor Flask (que a su vez habla con MongoDB).
const API = (() => {
    async function pedir(metodo, url, datos) {
        const opciones = { method: metodo, headers: {} };
        if (datos !== undefined) {
            opciones.headers["Content-Type"] = "application/json";
            opciones.body = JSON.stringify(datos);
        }
        let respuesta;
        try {
            respuesta = await fetch(url, opciones);
        } catch (error) {
            throw { estado: 0, error: "No hay conexión con el servidor del laboratorio." };
        }
        let cuerpo = {};
        try {
            cuerpo = await respuesta.json();
        } catch (error) {
            cuerpo = { error: `Respuesta inesperada del servidor (${respuesta.status})` };
        }
        if (respuesta.status === 401 && url.startsWith("/api/") && !url.startsWith("/api/panel")) {
            window.location.href = "/";
        }
        if (!respuesta.ok) {
            throw { estado: respuesta.status, ...cuerpo };
        }
        return cuerpo;
    }

    return {
        get: (url) => pedir("GET", url),
        post: (url, datos = {}) => pedir("POST", url, datos),
    };
})();

// Escapa texto antes de insertarlo como HTML (los nombres los escribe el público).
function esc(valor) {
    return String(valor ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

// Colorea un documento JSON para mostrarlo como en la consola de MongoDB.
function resaltarJSON(valor) {
    const texto = typeof valor === "string" ? valor : JSON.stringify(valor, null, 2);
    return esc(texto).replace(
        /(&quot;(?:[^&]|&(?!quot;))*?&quot;)(\s*:)?|\b(true|false|null)\b|(-?\d+(?:\.\d+)?)/g,
        (coincidencia, cadena, dosPuntos, literal, numero) => {
            if (cadena) {
                return dosPuntos
                    ? `<span class="j-clave">${cadena}</span>${dosPuntos}`
                    : `<span class="j-texto">${cadena}</span>`;
            }
            if (literal) return `<span class="j-literal">${literal}</span>`;
            return `<span class="j-numero">${numero}</span>`;
        }
    );
}
