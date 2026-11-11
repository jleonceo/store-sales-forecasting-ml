# Contrato de entrada

El proceso de cada mañana solo prevé si los datos que recibe cumplen este contrato. Si falta una columna, un tipo no es el suyo o falta alguna venta anterior al día, la ejecución para sin dejar previsión y anota el motivo. Así ninguna previsión sale de datos incompletos sin que quede constancia.

## Qué se entrega

Los datos llegan en una base SQLite con tres tablas, la misma forma que tienen `datos/ventas_2013_2015.db` y `datos/diciembre_2015.db`:

- `calendar`: una fila por día, con su código de día (`d`), la fecha, la semana comercial y el evento.
- `sales`: una fila por tienda y producto, con las unidades vendidas en una columna por día (`d_1768`, `d_1769`…).
- `sell_prices`: una fila por tienda, producto y semana comercial, con su precio.

El proceso une las tres en una tabla diaria, con una fila por tienda, producto y día. El contrato se comprueba sobre esa tabla.

## Columnas y tipos

| Columna | Tipo | Contenido |
|---|---|---|
| `store_id` | texto | Código de la tienda. |
| `item_id` | texto | Código del producto. |
| `date` | texto | Fecha del día, en formato `AAAA-MM-DD`. |
| `unidades` | número | Unidades vendidas ese día. Vacía en los días que todavía no tienen venta. |
| `wm_yr_wk` | número | Código de la semana comercial. |
| `weekday` | texto | Nombre del día de la semana. |
| `wday` | número | Número del día de la semana. |
| `month` | número | Mes. |
| `year` | número | Año. |
| `event_name_1` | texto | Nombre del evento del día. Un día sin evento llega vacío y se escribe como `Sin_evento`. |
| `event_type_1` | texto | Tipo del evento, con la misma regla. |
| `sell_price` | número | Precio de la semana para esa tienda y producto. No admite vacíos. |

## Comprobaciones al unir las tablas

Se hacen al leer la base, antes de mirar ningún día en concreto. Si una falla, el proceso se detiene con un error que dice cuál.

- El calendario no repite ningún código de día y la tabla de precios no repite ninguna combinación de tienda, producto y semana.
- Cada cruce conserva el número de filas y la suma de unidades.
- Todos los días tienen calendario.
- Todos los días de los datos nuevos tienen precio. En la historia de entrenamiento, las semanas sin precio se rellenaron con el precio más frecuente del producto. A los datos que llegan cada día no se les rellena nada.

## Comprobaciones de la mañana

Para la mañana de un día `D`, el proceso toma la tabla diaria con las ventas conocidas hasta `D - 1` y comprueba, en este orden:

1. **Columnas.** Están las 12 de la tabla anterior.
2. **Tipos.** Las columnas de texto no son numéricas y las numéricas no son texto.
3. **Una fila por serie y día.** Ninguna combinación de tienda, producto y fecha está repetida.
4. **Precio.** Ningún día llega sin precio.
5. **Días seguidos.** Ninguna serie tiene huecos entre su primer día y el último. Las variables cuentan días hacia atrás por filas: un hueco las desplazaría sin dar error.
6. **Series.** Llegan exactamente las series esperadas, que son 20 según `produccion/config.json`.
7. **Ninguna venta vacía antes de `D`.** Todos los días anteriores a `D` traen su venta, en todas las series. Un vacío a mitad de la historia cambiaría los retardos sin dar error, y una serie sin ninguna venta se colaría como si estuviera completa.
8. **Venta de la víspera.** La última venta conocida de todas las series es la del día `D - 1`. Si una serie se quedó en `D - 2`, la ejecución para.
9. **El propio día.** Llegan el calendario y el precio del día `D` para todas las series.

Si la base trae calendario y precio de menos de 8 días a partir de `D`, la ejecución no para: prevé los días que haya y lo deja escrito como aviso.

## Qué pasa si falla

- La ejecución termina con error y no escribe ninguna previsión para esa mañana.
- `produccion/salidas/ejecuciones.csv` recibe una fila con el día, el momento, el estado `ERROR` y el motivo. Por ejemplo: «llegan 19 series y se esperan 20».
- En GitHub Actions, el flujo falla y GitHub avisa por correo a quien lo lanzó.
- La previsión de la mañana anterior sigue en su carpeta, sin tocar.

## Qué entrega el proceso

Cuando el contrato se cumple, `produccion/salidas/<día>/prevision.csv` trae una fila por serie y día previsto, con estas columnas:

- `serie`: tienda y producto, unidos por « · ».
- `store_id` e `item_id`: los códigos de la tienda y del producto.
- `date`: el día previsto.
- `horizonte`: cuántos días por delante de la víspera está, de 1 a 8.
- `prevision`: unidades previstas, en número entero y sin bajar de cero.

## Dónde está en el código

- Las comprobaciones de la mañana están en `validar_entrada` y `comprobar_dia`, en `src/forecast/produccion.py`.
- Las comprobaciones al unir las tablas están en `src/forecast/datos.py`.
- `tests/probar_produccion.py` provoca cada fallo a propósito y comprueba que el proceso para: una columna que falta, un tipo cambiado, un día repetido, un día sin precio, una serie menos, una venta vacía a mitad de la historia, una serie sin ninguna venta, una venta de la víspera que no llega y un día sin calendario.
