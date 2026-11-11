# Variables

El modelo de cada serie ve, para cada día, lo que se sabía la víspera: las ventas y los precios de los días anteriores, el calendario del propio día y unas marcas de rachas sin venta. Ninguna variable usa la venta del día que se prevé ni datos de otra serie. Este documento explica qué variables son, cómo se codifica el calendario y cuáles entran en cada modelo.

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
- **El mes y el día de la semana** se sustituyen por la media de ventas de la serie en ese valor. La media se suaviza hacia la media general de la serie cuando un valor tiene pocos días: con 20 días pesa la mitad y con 60 casi entera. Dan 2 variables. El día de la semana llega también con su nombre, que va uno a uno con su número, así que no entra: su media sería una copia.

Hasta la versión del 11/11/2026, el suavizado pedía 100 días para dar peso a un valor. Una serie tiene como mucho 93 días de un mismo mes en tres años, así que la media del mes salía casi igual a la media general y el modelo no distinguía los meses. El día de la semana, con unos 150 días por valor, sí funcionaba. Una prueba de `tests/probar_variables.py` comprueba ahora que la media del mes distingue los meses.

Las codificaciones se aprenden con los días de entrenamiento de cada serie y se guardan junto a su modelo. Al prever, un evento que la serie no había visto da ceros en todas las columnas de evento. Un mes o un día de la semana nuevos toman la media de la serie.

## Qué variables entran

Con las 67 variables del historial, las 31 de evento y las 2 de media por valor, cada serie tiene 100 candidatas. Entran las que un árbol puede usar, con los días de entrenamiento de cada serie:

- **Fuera las constantes.** Por ejemplo, los retardos de precio de un producto que nunca cambió de precio.
- **Fuera los eventos con menos días que la hoja más pequeña del modelo.** Casi todos los eventos caen 2 o 3 días en tres años, y ningún árbol con hojas de 10 días o más puede cortar por ellos. De los 31, solo queda la columna de los días sin evento.

Quedan entre 63 y 70 variables por serie, y 60 entran en las 20. Si un día quedaran más de 70, se ordenarían por información mutua con las ventas y entrarían las 70 primeras, con los empates deshechos por nombre.

Hasta la versión del 11/11/2026 se ordenaban siempre las 101 candidatas por información mutua y entraban las 70 primeras. La información mutua da a una columna constante o con 2 o 3 unos un valor de ruido del mismo tamaño que el corte, así que entraban columnas de evento que ningún árbol usaba y quedaban fuera variables útiles. `tests/probar_modelo.py` comprueba ahora que no entra ninguna columna así.

## Cómo se evita mirar el futuro

Una variable que use la venta del día que se prevé daría un error de validación muy bajo y un modelo inservible. Hay tres defensas:

1. Todas las ventanas y marcas se calculan sobre la venta desplazada un día, dentro de cada serie.
2. Al prever, la venta de los días que todavía no existen se borra antes de calcular nada. Cada previsión pasa a ser la venta de su día para el siguiente.
3. `tests/probar_variables.py` comprueba que cambiar la venta de un día no cambia ninguna variable de ese día, que un retardo no cruza de una serie a otra y que la marca de racha cuenta días seguidos.

El precio es la excepción: al prever varios días seguidos, desde el segundo día el retardo de un día del precio es el precio de un día posterior al origen. Se trata como conocido porque la tienda fija sus precios por semanas y los sabe de antemano.

## Límites

- Muchas variables se parecen entre sí, como las medias de 14 y de 15 días, y entran todas. El árbol elige entre ellas al cortar.
- Las ventanas llegan a 15 días. El modelo no ve directamente lo que pasó el mismo mes del año anterior, salvo por la media de ventas del mes.
- Un evento de 2 o 3 días al año, como Navidad, no se puede aprender con una columna propia. El 25/12, con la tienda casi cerrada, el modelo prevé venta normal (documento 04).

## Fuente de las cifras

Las 300 filas sin historia y las 20.980 de modelado están en `informes/resultados.json`, bloque `datos`. Los recuentos de variables salen del código (`RETARDOS`, `ROTURAS` y `VENTANAS` en `variables.py`; `N_VARIABLES` y `variables_utiles` en `modelo.py`). Las variables de cada serie (de 63 a 70, y 60 en las 20) son las que guarda cada modelo entrenado, en `modelos/vigente/`.
