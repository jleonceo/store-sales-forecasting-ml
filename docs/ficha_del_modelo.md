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
- **Variables:** 70 por serie, elegidas entre 101. Son ventas y precios de días anteriores, medias móviles, calendario, eventos y marcas de rachas sin venta.
- **Hiperparámetros:** búsqueda de 10 combinaciones por serie, con validación temporal de 3 cortes de 8 días y semilla fija.
- **Datos de entrenamiento:** ventas del 01/01/2013 al 30/11/2015, que son 21.280 días de serie y 614.451 unidades.
- **Previsión a varios días:** recursiva. Cada día previsto pasa a ser la venta de ese día para prever el siguiente.

La explicación completa está en [02_variables.md](02_variables.md) y [03_modelo_y_validacion.md](03_modelo_y_validacion.md).

## Cuánto acierta

El error es error absoluto medio, en unidades. La referencia es prever la venta del mismo día de la semana anterior.

| Medida | Modelo | Referencia |
|---|---|---|
| Un día vista, prueba final del 16/12/2015 | 5,20 | 9,10 |
| Ocho días vista desde 12 fechas de 2015, por serie y día | 9,19 | 10,68 |
| Ocho días vista, total de las dos tiendas, del 24 al 31/12/2015 | 114,50 | 123,25 |
| Ocho días vista, por serie y día, del 24 al 31/12/2015 | 10,01 | 10,05 |

En la prueba desde 12 fechas el modelo tiene menos error que la referencia en los 8 días del horizonte. Su error sube de 7,86 unidades el primer día a cerca de 10 el octavo. El detalle está en [04_evaluacion.md](04_evaluacion.md).

## Límites

- **Días sin venta.** Es donde más se equivoca. Cuando un producto deja de venderse o la tienda cierra, el modelo sigue previendo venta. En la semana de Navidad de 2015, el error en los días sin venta fue de 18,16 unidades, frente a 7,56 en los días con venta. Sin el dato de inventario no puede saber si un cero es falta de demanda o falta de producto.
- **Tendencia a prever de más.** El sesgo medio es de 1,21 unidades en la prueba desde 12 fechas y de 4,76 en la semana de Navidad.
- **Producto a producto en semanas atípicas.** Del 24 al 31/12/2015 iguala a la referencia, sin mejorarla. La ventaja de esa semana está en el total.
- **Festivos de cierre.** El 25/12/2015 previó 443 unidades en el total y se vendió 1. El evento está en el calendario, pero la historia solo contiene dos días de Navidad de los que aprender.
- **Frecuencia de reentreno.** En la simulación se entrenó una vez, con datos hasta el 30/11/2015. Cada cuánto conviene reentrenar no está medido.
- **Alcance probado.** 20 series de un departamento de alimentación en dos tiendas de un mismo estado, con datos de 2013 a 2015. No está medido con otros productos, otras tiendas ni otro periodo.
- **Una sola prueba final.** Diciembre de 2015 es un mes. Sus cifras dicen cómo fue ese mes y no garantizan el siguiente.
- **Precio.** Usa el precio semanal de los días anteriores. No ve una promoción anunciada para la semana que viene.
- **Productos nuevos.** Una serie necesita historia para tener modelo. No hay previsión para un producto que acaba de entrar.

## Mantenimiento

- **Reentreno.** `produccion/reentrenar.py` entrena un modelo candidato y solo sustituye al que está en uso si no valida peor.
- **Seguimiento.** Cada previsión se compara con la venta real cuando existe. El error queda registrado por mañana junto al de la referencia.
- **Vuelta atrás.** `produccion/volver_atras.py` restaura el modelo anterior.
- **Versiones.** Los modelos solo se cargan con las versiones de scikit-learn y pandas con que se entrenaron, fijadas en `requirements.txt`.

El proceso completo está en [06_produccion.md](06_produccion.md).

## Fuente de las cifras

Las cifras de acierto y de sesgo están en `informes/resultados.json`. El error en los días con y sin venta procede del análisis de evaluación previo a este repositorio, hecho con el mismo modelo.
