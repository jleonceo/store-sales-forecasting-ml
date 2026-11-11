# Datos y calidad

Los datos son tres años de ventas diarias de 10 productos de alimentación en 2 tiendas. Llegan en buen estado: sin duplicados, sin fechas que falten y sin ventas negativas. Los problemas que traen son de forma y de significado, y cada uno tiene una decisión escrita en este documento. El código que la aplica está en `src/forecast/datos.py`.

## Origen

Los datos proceden de la competición M5 de Kaggle, con ventas de Walmart: [M5 Forecasting - Accuracy](https://www.kaggle.com/competitions/m5-forecasting-accuracy). De ese conjunto se usa una parte: 10 productos del departamento de alimentación `FOODS_3` en las tiendas `CA_3` y `CA_4`, del 01/01/2013 al 31/12/2015.

El repositorio trae esa parte en dos bases SQLite, separadas a propósito:

- `datos/ventas_2013_2015.db` llega hasta el 30/11/2015. Con ella se construye, se entrena y se valida todo.
- `datos/diciembre_2015.db` contiene solo diciembre de 2015. Quedó apartada hasta la prueba final.

Los datos no contienen información de personas: solo tiendas, productos, fechas, unidades y precios.

## Las tres tablas

Cada base trae las mismas tres tablas. En la base de historia tienen este tamaño:

| Tabla | Filas | Qué es una fila |
|---|---|---|
| `calendar` | 1.064 | Un día, con su semana comercial, su día de la semana y hasta dos eventos. |
| `sales` | 20 | Una tienda y un producto, con las unidades vendidas en una columna por día. |
| `sell_prices` | 3.049 | El precio de un producto en una tienda durante una semana comercial. |

Para trabajar hace falta una sola tabla con una fila por tienda, producto y día. Se obtiene pasando las columnas de días de `sales` a filas y uniendo después el calendario por el código del día y el precio por tienda, producto y semana. El resultado son 21.280 filas, que es 20 series por 1.064 días, con 614.451 unidades vendidas.

Cada cruce se comprueba en el momento: si la tabla resultante gana o pierde una fila o una unidad, o si el maestro repite una clave, el proceso para. Así, un cambio en los datos de origen no puede multiplicar ventas sin que nadie lo vea.

## Qué se encontró y qué se hizo

**Columnas que no aportan.** Las tres tablas traen una columna `index` con el número de fila de la tabla de la que se extrajeron. `sales` trae además un identificador que repite tienda y producto, y tres columnas con un solo valor en las 20 filas (departamento, categoría y estado). Ninguna entra en la tabla diaria.

**Días sin evento.** El 92,01 % de los días no tiene evento y la columna llega vacía. Un día sin evento es un día normal, así que el vacío se escribe como `Sin_evento` y deja de contar como dato ausente. El segundo evento solo aparece en 3 días y no entra en el modelo.

**Semanas sin precio.** De los 3.060 precios que daría la rejilla completa de series por semanas faltan 11, todos del producto `FOODS_3_288`. Afectan a 71 días, todos anteriores a la primera venta de su serie y sin ninguna unidad vendida. Se rellenan con el precio más frecuente del producto y quedan marcados en la columna `sell_price_faltante`.

**Días sin ventas.** De los 21.280 días de serie, 3.004 tienen cero unidades. Un cero es un dato válido, pero no todos significan lo mismo. Por eso se separan en dos clases:

- 1.259 días pertenecen a rachas de más de 60 días seguidos a cero, repartidas en 5 series. Se interpretan como producto fuera de la tienda.
- 1.745 días son ceros sueltos, propios de una demanda intermitente.

Los datos no dicen la causa de ninguno de los dos. Las variables del modelo incluyen marcas de racha para que pueda distinguirlos ([02_variables.md](02_variables.md)).

**Los dos días de Navidad.** El 25/12/2013 y el 25/12/2014 las 20 series venden cero. Todas las series a cero el mismo día apunta a tienda cerrada, aunque los datos no lo confirman. Se dejan como ventas cero.

**Valores altos.** Las unidades van de 0 a 763 al día, con una mediana de 18. Medidos dentro de cada serie, solo 136 días destacan por dos métodos a la vez (rango intercuartílico y z robusto). Son días de mucha venta en series que venden mucho. No se tocan.

**Lo que está bien.** No hay filas repetidas ni claves repetidas en ninguna tabla. Las fechas llegan en formato año-mes-día, sin días que falten ni repetidos, y el año, el mes y el día de la semana coinciden con la fecha en todos los casos. Los precios van de 1,00 a 4,98 y ninguno es cero o negativo.

## Diciembre de 2015

La base de diciembre trae 620 filas, 20 series por 31 días, con 13.551 unidades. Pasa por los mismos cruces que la historia, con una diferencia: no se rellena ningún precio. A los datos nuevos se les exige traer precio en todos los días, y si falta alguno el proceso para.

Al juntar historia y diciembre se comprueba además que ninguna serie repite un día ni tiene huecos. Las variables cuentan días hacia atrás por filas: un hueco las desplazaría sin dar error.

## Límites

- El precio es el de la semana comercial. Si cambió dentro de la semana, no se ve.
- La separación entre producto fuera de la tienda y cero suelto usa un umbral de 60 días seguidos. Es una regla sobre las ventas: sin el dato de inventario no se puede comprobar.
- La licencia de uso de los datos es la que fije su fuente, enlazada arriba.

## Fuente de las cifras

Los recuentos de filas, unidades, precios rellenados y días sin ventas están en `informes/resultados.json`, bloque `datos`. `tests/probar_datos.py` los comprueba contra la base. El resto (porcentajes de días sin evento, rangos de unidades y precios, valores altos y semanas sin precio) procede del análisis de calidad hecho sobre la misma base antes de construir este repositorio, que el código de aquí no regenera.
