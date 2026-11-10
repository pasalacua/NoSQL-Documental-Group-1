# Guión de la experiencia práctica · POKÉLAB (Grupo 1 · MongoDB)

> Borrador para adaptar. Incluye la propuesta de media carilla que pide la consigna y el guión completo.

## Propuesta (media carilla)

**Objetivo.** Que el público opere una base de datos MongoDB real desde su celular y experimente
cómo se consultan y modifican documentos con estructura anidada.

**Concepto que se demuestra.** Modelo documental: documentos anidados y arrays de documentos
(notación de punto y `$elemMatch`), esquema flexible con documentos embebidos (`$push` y operador
posicional), pipeline de agregación y uso de índices por el planificador de consultas.

**Materiales.** Aplicación web POKÉLAB (Flask + MongoDB Atlas) desplegada en una notebook del grupo o
en un servidor; celulares del público; proyector con el panel del expositor (`/panel`).

**Secuencia.** 1) Los participantes entran a la URL y crean su investigador. 2) Cinco entrenadores
les hacen pedidos que solo se resuelven escribiendo consultas y escrituras sobre la colección
`pokemon`. 3) El panel proyectado muestra en vivo cuántos cayeron en cada error y qué documentos
escribieron. 4) Cierre de un minuto explicando qué pasó.

**Rol de la audiencia.** Son investigadores del laboratorio: construyen filtros, arman pipelines,
escriben documentos embebidos y eligen planes de ejecución. Nadie responde preguntas: cada acción
se ejecuta contra MongoDB y la base devuelve el resultado.

**Plan alternativo.** Si falla el Wi-Fi o Atlas: MongoDB local en la notebook y un hotspot del
celular de un integrante; si tampoco hay red, la notebook proyectada y el público dicta los filtros
por turnos.

## Por qué cumple el criterio central

Si la misma actividad se usara con Redis, Cassandra o Neo4j, no funcionaría sin cambiarla: los
pedidos dependen de consultar **dentro** de documentos (`estadisticas.velocidad`), de la semántica
de los arrays de documentos (`$elemMatch`), de embeber documentos con campos distintos en el mismo
array y de un pipeline que desarma arrays (`$unwind`). Son características propias del modelo
documental.

Respuestas a las preguntas de la consigna:

- **¿Qué hace distinta a esta tecnología?** Guarda cada entidad como un documento JSON/BSON
  autocontenido, con datos anidados y arrays, y permite consultar e indexar cualquier campo interno.
- **¿Qué decisión toma el motor que una persona puede tomar en la actividad?** Qué índice usar para
  resolver una consulta (planificador de consultas). En la misión del Ingeniero Plata el público
  compara los planes con `explain()` y elige; después ve que MongoDB eligió lo mismo.
  También, en `$elemMatch`, si dos condiciones deben cumplirse sobre el mismo elemento del array.
- **¿Qué dificultad aparecería con una base relacional?** El Pokémon se repartiría en 7 tablas y
  cada consulta necesitaría JOINs/EXISTS (la terminal muestra el SQL equivalente). Registrar una
  forma con un dato nuevo (`objeto_requerido`, `region`) exigiría `ALTER TABLE` o una tabla
  clave-valor.

## Guión minuto a minuto (≈ 9 minutos)

| Tiempo | Qué pasa | Quién |
|---|---|---|
| 0:00 | Se proyecta `/panel` con la URL. "Entren desde el celular y creen su investigador." | Expositor 1 |
| 1:00 | Todos resuelven al **Entrenador Rojo** (filtro con notación de punto). Muchos ponen `$gte 60` y el entrenador les dice que sobra Clefable. | Público |
| 3:00 | **Entrenadora Azul**: el panel muestra en vivo cuántos cayeron en la trampa de `$elemMatch`. Se comenta brevemente. | Público / Expositor 2 |
| 4:30 | **Entrenadora Amarilla** (pipeline) y **Entrenador Verde** (registrar una forma). En el panel aparecen las formas embebidas y los distintos nombres de campo elegidos. | Público |
| 7:00 | **Ingeniero Plata**: comparan `COLLSCAN` vs `IXSCAN`. | Público |
| 8:00 | Ranking en el panel y cierre de un minuto. | Expositor 3 |

Si el tiempo es corto, se priorizan Rojo, Azul y Verde (los tres conceptos centrales).

## Cierre de un minuto (texto sugerido)

"Lo que hicieron fue operar una base MongoDB real. Cada Pokémon es **un solo documento** con sus
estadísticas anidadas y sus movimientos en un array: por eso Rojo se resolvió con una sola consulta,
sin JOINs. La trampa de Azul es propia del modelo documental: con dos condiciones sueltas sobre un
array de documentos, MongoDB las puede cumplir con elementos distintos; `$elemMatch` obliga a que
sea el mismo. Cuando registraron formas, cada uno agregó un campo nuevo dentro del documento y
nadie tuvo que cambiar un esquema: eso es el esquema flexible, y el panel muestra su costo, porque
el mismo dato quedó guardado con nombres distintos. Y en la última misión tomaron la misma decisión
que toma el planificador de MongoDB: usar el índice que examina menos documentos."

## Checklist antes de exponer

- [ ] `.env` con la URI de Atlas (o MongoDB local) y `PANEL_PIN` cambiado.
- [ ] En Atlas: *Network Access* permite la IP desde donde corre el servidor.
- [ ] `python -m database.seed --todo` para empezar con la base limpia.
- [ ] `python run.py --prod` y probar la URL desde un celular en la misma red.
- [ ] Panel abierto en el proyector (`/panel`).
