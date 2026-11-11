# Evaluación

El modelo se equivoca menos que la regla de la semana anterior en las tres medidas: en la validación a un día, en la prueba desde 12 fechas de 2015 y en la prueba final de diciembre al sumar las dos tiendas. La ventaja es clara a un día vista y en el conjunto del año. En la semana de Navidad, producto a producto, el modelo y la regla quedan igualados. Todas las cifras son error absoluto medio en unidades; cómo se mide cada una está en [03_modelo_y_validacion.md](03_modelo_y_validacion.md).

## Resumen

| Medida | Modelo | Regla | Dónde gana el modelo |
|---|---|---|---|
| Validación a un día (noviembre de 2015) | 7,58 | 10,09 | 19 de 20 series |
| Ocho días desde 12 fechas de 2015 | 9,19 | 10,68 | 153 de 240 previsiones de 8 días |
| Prueba final, un día vista (16/12/2015) | 5,20 | 9,10 | 13 de 20 series |
| Prueba final, 8 días por serie (24 al 31/12/2015) | 10,01 | 10,05 | 12 de 20 series |
| Prueba final, 8 días en el total de las dos tiendas | 114,50 | 123,25 | |

## Prueba desde 12 fechas

Es la medida con más peso, porque repite el proceso entero 12 veces a lo largo de 2015 y prevé 8 días seguidos, como en el uso real. El modelo baja el error de 10,68 a 9,19 unidades por serie y día. El intervalo del 95 % de esa diferencia, calculado remuestreando los 240 bloques de serie y origen, va de -2,08 a -0,93 unidades y no incluye el cero.

El error crece con el horizonte, como cabe esperar de una previsión que se alimenta de sus propias previsiones. Aun así, el modelo queda por debajo de la regla en los 8 días.

| Día del horizonte | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Modelo | 7,86 | 7,33 | 8,42 | 9,30 | 9,21 | 10,46 | 10,95 | 9,98 |
| Regla | 9,81 | 8,67 | 10,75 | 10,15 | 11,10 | 10,84 | 12,76 | 11,34 |

Por fecha de origen, el modelo gana en 10 de las 12. Las dos en que pierde son las de finales de septiembre y de octubre, por menos de una unidad. El sesgo medio es de 1,21 unidades: el modelo tiende a prever algo por encima de la venta real.

## Validación de noviembre

A un día vista, el modelo mejora la regla en 19 de las 20 series. La excepción es `CA_3 · FOODS_3_586`, donde quedan casi igualados (13,05 frente a 12,75). La serie con más venta, `CA_3 · FOODS_3_090`, es también la de mayor mejora en unidades: 30,89 frente a 44,96.

El error en los propios días de entrenamiento es de 3,36 unidades, menos de la mitad que en la validación. El 16/12, ya en la prueba final y con datos que el modelo no había visto, el error fue de 5,20: 1,55 veces el de los días de entrenamiento.

## Prueba final a un día

El 16/12/2015, con los modelos entrenados hasta el 30/11 y sin reentrenar, el error medio de las 20 series fue de 5,20 unidades frente a 9,10 de la regla. El intervalo del 95 % de la diferencia va de -8,50 a -0,55 unidades. Es un solo día y 20 previsiones, así que el intervalo es ancho, pero queda entero por debajo de cero.

## Prueba final a 8 días

La previsión del 24 al 31/12 se hizo con las ventas conocidas hasta el 23/12. Por serie y día, el modelo y la regla quedan igualados: 10,01 frente a 10,05 unidades. El intervalo de la diferencia va de -1,41 a 1,53 e incluye el cero, así que con esta semana no se puede decir que uno sea mejor que el otro a ese nivel.

Al sumar las series, la ventaja del modelo aparece en el total:

| Nivel | Modelo | Regla |
|---|---|---|
| Total de las dos tiendas | 114,50 | 123,25 |
| Tienda `CA_3` | 85,88 | 102,75 |
| Tienda `CA_4` | 29,62 | 28,75 |
| Tienda y producto | 10,01 | 10,05 |

La tienda grande, `CA_3`, concentra la mejora. En `CA_4` la regla queda algo por delante.

Dos hechos explican la mayor parte del error de esa semana:

- **El día de Navidad.** El 25/12/2015 las dos tiendas vendieron 1 unidad entre los 20 productos. El modelo previó 443 y la regla, 409. Ese día el error por serie fue de 22,10 unidades para el modelo y 20,40 para la regla, el más alto de la semana para los dos.
- **Un producto que deja de venderse.** `FOODS_3_090` es la serie en que el modelo queda más lejos de la regla en las dos tiendas. En `CA_4` el producto no vendió nada desde el 03/12: la regla repite ese cero y acierta todos los días, mientras que el modelo siguió previendo venta, con 24,12 unidades de error.

Los dos casos tienen la misma raíz, que son los días sin venta. En los días con venta, el error del modelo fue de 7,56 unidades, con un sesgo de 0,73. En los días sin venta fue de 18,16 y todo él por exceso: el modelo previó venta donde no la hubo.

## Límites

- La prueba final es un mes: un día a un día vista y una semana a 8 días. Sus cifras dicen cómo fue ese diciembre.
- Los intervalos de la prueba final remuestrean filas sueltas. Las filas de una misma serie se parecen entre sí, así que el intervalo real es algo más ancho.
- Las causas apuntadas para el 25/12 y para `FOODS_3_090` son una interpretación de las ventas. Los datos no dicen si la tienda cerró ni si el producto se quedó sin existencias.

## Fuente de las cifras

Las cifras del resumen, de los niveles, del horizonte, del origen y del día a día del total están en `informes/resultados.json` e `informes/backtest.json`. Las ventas de diciembre de `FOODS_3_090` están en `datos/diciembre_2015.db`. El error por día de la semana de Navidad está en `produccion/salidas/2015-12-24/evaluacion.json`. La validación serie a serie está en el manifiesto que deja el entrenamiento en `modelos/vigente/`. Los intervalos de la prueba final, el error en los días de entrenamiento y el error por clase de día proceden del análisis de evaluación previo a este repositorio, hecho con el mismo modelo, que el código de aquí no regenera.
