# Variables

El modelo de cada serie ve, para cada día, lo que se sabía la víspera: las ventas y los precios de los días anteriores, el calendario del propio día y unas marcas de rachas sin venta. Ninguna variable usa la venta del día que se prevé ni datos de otra serie. Este documento explica qué variables son, cómo se codifica el calendario y cómo se eligen las 70 que entran en cada modelo.

## Variables del historial

`src/forecast/variables.py` construye 67 variables por tienda, producto y día, todas con datos anteriores a ese día.

| Grupo | Cuántas | Qué recogen |
|---|---|---|
| Retardos de ventas | 15 | Las unidades vendidas cada uno de los 15 días anteriores. |
| Retardos de precio | 7 | El precio de cada uno de los 7 días anteriores. |
| Marcas de racha sin venta | 3 | Si la víspera cerraba una racha de 3, 7 o 15 días seguidos a cero. |
| Ventanas móviles | 42 | Mínimo, media y máximo de las ventas en ventanas de 2 a 15 días que acaban la víspera. |

Los retardos dan al modelo el nivel reciente de la serie y su patrón semanal: el retardo de 7 días es la venta del mismo día de la semana anterior, que es justo la regla con la que se compara. Las ventanas resumen ese nivel con menos ruido. Las marcas de racha existen por los días sin ventas: un cero aislado y el decimoquinto cero seguido piden previsiones distintas, y con las marcas el modelo puede aprender la diferencia.

Las primeras filas de cada serie no tienen 15 días de historia y sus variables quedarían vacías. Salen de la tabla de modelado: son 300 filas, 15 por serie. Quedan 20.980.

## Lo que no entra

- **El precio del propio día.** Solo entran los precios de días anteriores.
- **El segundo evento del calendario.** Aparece en 3 días de 1.064.
- **El año y el tipo de evento.** El año no se repite en el futuro y el tipo se deduce del nombre del evento.
- **Los códigos del día y de la semana comercial.** Sirven para cruzar las tablas y no describen la venta.

## Calendario

El calendario llega como categorías (el mes, el día de la semana, el nombre del evento) y un modelo de árboles necesita números. Dejar el mes como 1 a 12 le diría que diciembre es doce veces enero, así que cada columna se codifica según lo que es:

- **El evento** pasa a una columna por nombre, con un 1 el día que ocurre. Con los 30 eventos de la historia y el día sin evento, son 31 columnas.
- **El mes y el día de la semana** se sustituyen por la media de ventas de la serie en ese valor. La media se suaviza hacia la media general de la serie cuando un valor tiene pocos días. Dan 3 variables, porque el día de la semana llega con su nombre y con su número.

Las codificaciones se aprenden con los días de entrenamiento de cada serie y se guardan junto a su modelo. Al prever, un evento que la serie no había visto da ceros en todas las columnas de evento. Un mes o un día de la semana nuevos toman la media de la serie.

## Preselección

Con las 67 variables del historial, las 31 de evento y las 3 de media por valor, cada serie tiene 101 candidatas. Para cada serie se ordenan por información mutua con las ventas y entran las 70 primeras. Los empates se deshacen por nombre de variable, para que el orden sea siempre el mismo.

La selección se hace serie a serie porque las series no se parecen: en noviembre de 2015 una vendía más de cien unidades al día y otra menos de cinco. Aun así comparten buena parte: 43 variables entran en las 20 series y 100 de las 101 entran en alguna.

## Cómo se evita mirar el futuro

Una variable que use la venta del día que se prevé daría un error de validación muy bajo y un modelo inservible. Hay tres defensas:

1. Todas las ventanas y marcas se calculan sobre la venta desplazada un día, dentro de cada serie.
2. Al prever, la venta de los días que todavía no existen se borra antes de calcular nada. Cada previsión pasa a ser la venta de su día para el siguiente.
3. `tests/probar_variables.py` comprueba que cambiar la venta de un día no cambia ninguna variable de ese día, que un retardo no cruza de una serie a otra y que la marca de racha cuenta días seguidos.

## Límites

- La información mutua puntúa cada variable por separado. Dos variables casi iguales, como las medias de 14 y de 15 días, pueden entrar las dos.
- Las ventanas llegan a 15 días. El modelo no ve directamente lo que pasó el mismo mes del año anterior, salvo por la media de ventas del mes.

## Fuente de las cifras

Las 300 filas sin historia y las 20.980 de modelado están en `informes/resultados.json`, bloque `datos`. Los recuentos de variables salen del código (`RETARDOS`, `ROTURAS` y `VENTANAS` en `variables.py`; `N_VARIABLES` en `modelo.py`). Las cifras de variables compartidas entre series (43 y 100) y el número de eventos proceden del análisis de preselección previo a este repositorio, hecho con el mismo procedimiento.
