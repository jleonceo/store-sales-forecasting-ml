# Ficha del modelo

## Qué hace

Prevé las unidades que se venderán cada día de los 8 siguientes, para cada uno de 10 productos de alimentación en 2 tiendas. Son 20 series y 20 modelos, uno por tienda y producto. La previsión de una tienda y la del total se obtienen sumando las de sus productos, así que los tres niveles cuadran.

## Para qué sirve

Sirve de apoyo a las decisiones de compra y de reparto a tienda con una semana de antelación. Está pensado para ejecutarse cada mañana, con las ventas cerradas hasta la víspera. Su mejor uso, con lo medido hasta ahora, es la previsión del día siguiente y la del total de las tiendas.

## Qué necesita

- Las ventas diarias de cada serie hasta la víspera, sin huecos. Las variables miran hasta 15 días atrás y el proceso lee los 20 últimos.
- El calendario de los días que se van a prever: día de la semana, mes y evento, si lo hay.
- El precio semanal de cada producto en cada tienda.

El detalle de columnas, tipos y comprobaciones está en el [contrato de entrada](../produccion/contrato_entrada.md). Si los datos no lo cumplen, el proceso para y no deja previsión.

## Qué entrega

Una fila por serie y día previsto, con las unidades en números enteros y nunca por debajo de cero. Cada ejecución guarda además con qué datos y con qué modelo se hizo, para poder reconstruirla.

## Cómo está hecho

- **Algoritmo:** `HistGradientBoostingRegressor`, de scikit-learn, uno por serie.
- **Variables:** de 63 a 70 por serie, las que un árbol puede usar entre 100 candidatas. Son ventas y precios de días anteriores, medias móviles, la media de ventas del mes y del día de la semana, los días sin evento y marcas de rachas sin venta.
- **Hiperparámetros:** búsqueda de 10 combinaciones por serie más los valores por defecto, con validación temporal de 3 cortes de 8 días y semilla fija.
- **Datos de entrenamiento:** ventas del 01/01/2013 al 30/11/2015, que son 21.280 días de serie y 614.451 unidades.
- **Previsión a varios días:** recursiva. Cada día previsto pasa a ser la venta de ese día para prever el siguiente.

La explicación completa está en [02_variables.md](02_variables.md) y [03_modelo_y_validacion.md](03_modelo_y_validacion.md).

## Cuánto acierta

El error es error absoluto medio, en unidades. La referencia es prever la venta del mismo día de la semana anterior.

| Medida | Modelo | Referencia |
|---|---|---|
| Un día vista, las 31 mañanas de diciembre de 2015 | 7,45 | 10,43 |
| Ocho días vista desde 12 fechas de 2015, por serie y día | 8,87 | 10,68 |
| Ocho días vista, total de las dos tiendas, del 24 al 31/12/2015 | 112,75 | 123,25 |
| Ocho días vista, por serie y día, del 24 al 31/12/2015 | 9,61 | 10,05 |

En la prueba desde 12 fechas el modelo tiene menos error que la referencia en los 8 días del horizonte, y también menos que la media de los 7 últimos días (9,67) y que la media del mismo día en 4 semanas (10,10). Su error sube de 7,68 unidades el primer día a cerca de 10 el octavo. El detalle está en [04_evaluacion.md](04_evaluacion.md).

## Límites

- **Días sin venta.** Es donde más se equivoca. Cuando un producto deja de venderse o la tienda cierra, el modelo sigue previendo venta. En la semana de Navidad de 2015, el error en los días sin venta fue de 16,76 unidades, frente a 7,46 en los días con venta. Sin el dato de inventario no puede saber si un cero es falta de demanda o falta de producto.
- **Tendencia a prever de más.** El sesgo medio es de 1,22 unidades en la prueba desde 12 fechas y de 4,83 en la semana de Navidad.
- **Producto a producto en semanas atípicas.** Del 24 al 31/12/2015 queda algo por delante de la referencia, pero la diferencia cabe en el azar. La ventaja clara de esa semana está en el total.
- **Festivos de cierre.** El 25/12/2015 previó 423 unidades en el total y se vendió 1. La historia solo tiene dos días de Navidad, y un evento de 2 días no se puede aprender con una variable propia.
- **Frecuencia de reentreno.** En la simulación se entrenó una vez, con datos hasta el 30/11/2015. Cada cuánto conviene reentrenar no está medido.
- **Alcance probado.** 20 series de un departamento de alimentación en dos tiendas de un mismo estado, con datos de 2013 a 2015. No está medido con otros productos, otras tiendas ni otro periodo.
- **Una sola prueba final.** Diciembre de 2015 es un mes. Sus cifras dicen cómo fue ese mes y no garantizan el siguiente.
- **Precio.** Usa el precio semanal de los días anteriores. Al prever varios días seguidos, toma como conocido el precio de los días previstos, porque la tienda fija sus precios por semanas.
- **Productos nuevos.** Una serie necesita historia para tener modelo. No hay previsión para un producto que acaba de entrar.

## Mantenimiento

- **Reentreno.** `produccion/reentrenar.py` entrena un modelo candidato y solo sustituye al que está en uso si no valida peor frente a la referencia.
- **Seguimiento.** Cada previsión se compara con la venta real cuando existe. El error queda registrado por mañana junto al de la referencia.
- **Vuelta atrás.** `produccion/volver_atras.py` restaura el modelo anterior.
- **Versiones.** Los modelos solo se cargan con las versiones de scikit-learn y pandas con que se entrenaron, fijadas en `requirements.txt`.

El proceso completo está en [06_produccion.md](06_produccion.md).

## Fuente de las cifras

Las cifras de acierto, de sesgo y del error en los días con y sin venta están en `informes/resultados.json` e `informes/backtest.json`.
