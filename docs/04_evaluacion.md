# Evaluación

El modelo se equivoca menos que la regla de la semana anterior en todas las medidas: en la validación a un día, en la prueba desde 12 fechas de 2015 y en la prueba final de diciembre. La ventaja es clara a un día vista, en el conjunto del año y al sumar las tiendas. En la semana de Navidad, producto a producto, el modelo queda por delante por poco y la diferencia no se distingue del azar. Todas las cifras son error absoluto medio en unidades; cómo se mide cada una está en [03_modelo_y_validacion.md](03_modelo_y_validacion.md).

## Resumen

| Medida | Modelo | Regla | Dónde gana el modelo |
|---|---|---|---|
| Validación a un día (noviembre de 2015) | 7,46 | 10,09 | 20 de 20 series |
| Ocho días desde 12 fechas de 2015 | 8,87 | 10,68 | 160 de 240 previsiones de 8 días |
| Diciembre de 2015, un día vista, las 31 mañanas | 7,45 | 10,43 | 20 de 31 mañanas |
| Prueba final, un día vista (16/12/2015) | 4,30 | 9,10 | 13 de 20 series |
| Prueba final, 8 días por serie (24 al 31/12/2015) | 9,61 | 10,05 | 12 de 20 series |
| Prueba final, 8 días en el total de las dos tiendas | 112,75 | 123,25 | |

## Prueba desde 12 fechas

Es la medida con más peso, porque repite el proceso entero 12 veces a lo largo de 2015 y prevé 8 días seguidos, como en el uso real. El modelo baja el error de 10,68 a 8,87 unidades por serie y día. El intervalo del 95 % de esa diferencia, remuestreando los 240 bloques de serie y origen, va de -2,54 a -1,12 unidades. Remuestreando solo los 12 orígenes, que es más prudente porque las 20 series de una misma fecha comparten semanas, va de -2,77 a -0,90. Ninguno de los dos incluye el cero.

La regla de la semana anterior es la que usaría un responsable de compras, pero no es la más difícil de batir. Con la misma información en cada origen, el modelo gana también a dos reglas más exigentes:

| Regla | Error | Intervalo de la diferencia, por origen | Orígenes que gana el modelo |
|---|---|---|---|
| Lo mismo que la semana anterior | 10,68 | -2,77 a -0,90 | 10 de 12 |
| Media del mismo día en las 4 semanas anteriores | 10,10 | -2,35 a -0,30 | 8 de 12 |
| Media de los 7 últimos días | 9,67 | -1,63 a -0,19 | 10 de 12 |

El error crece con el horizonte, como cabe esperar de una previsión que se alimenta de sus propias previsiones. Aun así, el modelo queda por debajo de la regla en los 8 días.

| Día del horizonte | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Modelo | 7,68 | 7,36 | 7,96 | 9,05 | 9,07 | 9,74 | 10,49 | 9,64 |
| Regla | 9,81 | 8,67 | 10,75 | 10,15 | 11,10 | 10,84 | 12,76 | 11,34 |

Las dos fechas de origen en que pierde son las de finales de septiembre y de octubre, por menos de una unidad.

Sumando las 20 series de cada día, el total de las dos tiendas da 82,86 unidades de error frente a 89,75 de la regla. En `CA_3` el modelo queda casi igualado (73,90 frente a 75,53) y en `CA_4` gana (23,05 frente a 27,86).

El sesgo medio es de 1,22 unidades por serie y día: el modelo tiende a prever algo por encima de la venta real. En el total del año suma 55.480 unidades previstas frente a 53.133 vendidas, un 4,4 % de más. Para quien compra, eso es un pequeño colchón de existencias.

## Validación de noviembre

A un día vista, el modelo mejora la regla en las 20 series. La más ajustada es `CA_3 · FOODS_3_586` (12,61 frente a 12,75). La serie con más venta, `CA_3 · FOODS_3_090`, es la de mayor mejora en unidades: 29,51 frente a 44,96.

## Diciembre, mañana a mañana

La simulación de producción prevé cada mañana de diciembre de 2015 con los modelos entrenados hasta el 30/11. A un día vista, en las 31 mañanas, el modelo se equivoca 7,45 unidades frente a 10,43 de la regla y gana en 20 de 31.

A 8 días, en las 24 mañanas con los 8 días medidos, el modelo y la regla quedan cerca por serie: 9,72 frente a 9,87. En el total de las dos tiendas la diferencia es mayor: 74,82 frente a 89,07, y el modelo gana en 19 de las 24 mañanas.

Por día del horizonte, el modelo gana los días 1 a 3 y el 8, y la regla gana los días 4 a 7. Las mañanas se solapan, así que es un indicio y no una medida independiente.

## Prueba final a un día

El 16/12/2015, con los modelos entrenados hasta el 30/11 y sin reentrenar, el error medio de las 20 series fue de 4,30 unidades frente a 9,10 de la regla. El intervalo del 95 % de la diferencia va de -9,10 a -1,40 unidades. Es un solo día y 20 previsiones, así que el intervalo es ancho, pero queda entero por debajo de cero. Ese día es uno de los 31 de la tabla anterior, y la cifra del mes entero es la más representativa.

## Prueba final a 8 días

La previsión del 24 al 31/12 se hizo con las ventas conocidas hasta el 23/12. Por serie y día, el modelo queda por delante: 9,61 frente a 10,05 unidades. El intervalo de la diferencia va de -1,94 a 1,02 e incluye el cero, así que con esta semana no se puede decir que uno sea mejor que el otro a ese nivel.

Al sumar las series, la ventaja del modelo se ve en el total:

| Nivel | Modelo | Regla |
|---|---|---|
| Total de las dos tiendas | 112,75 | 123,25 |
| Tienda `CA_3` | 82,62 | 102,75 |
| Tienda `CA_4` | 32,88 | 28,75 |
| Tienda y producto | 9,61 | 10,05 |

La tienda grande, `CA_3`, concentra la mejora. En `CA_4` la regla queda por delante.

Dos hechos explican la mayor parte del error de esa semana:

- **El día de Navidad.** El 25/12/2015 las dos tiendas vendieron 1 unidad entre los 20 productos. El modelo previó 423 y la regla, 409. Ese día el error por serie fue de 21,10 unidades para el modelo y 20,40 para la regla, el más alto de la semana para los dos.
- **Un producto que deja de venderse.** En `CA_4`, `FOODS_3_090` no vendió nada desde el 03/12: la regla repite ese cero y acierta todos los días, mientras que el modelo siguió previendo venta, con 24,50 unidades de error.

Los dos casos tienen la misma raíz, los días sin venta. En los 123 días con venta, el error del modelo fue de 7,46 unidades, con un sesgo de 1,24. En los 37 días sin venta fue de 16,76 y todo él por exceso: el modelo previó venta donde no la hubo.

## Límites

- La prueba final es un mes: sus cifras dicen cómo fue ese diciembre. Diciembre se consultó además en el experimento (documento 05), así que no es una prueba ciega del todo.
- Los intervalos de la prueba final remuestrean previsiones sueltas. Las de una misma serie se parecen entre sí, así que el intervalo real es algo más ancho.
- Las causas apuntadas para el 25/12 y para `FOODS_3_090` son una interpretación de las ventas. Los datos no dicen si la tienda cerró ni si el producto se quedó sin existencias.

## Fuente de las cifras

Todas las cifras de este documento salen de `informes/resultados.json` y de `informes/backtest.json`, que regeneran `scripts/resultados.py` y `scripts/backtest.py`. El error por día de la semana de Navidad está en `produccion/salidas/2015-12-24/evaluacion.json`, y las ventas de diciembre de `FOODS_3_090`, en `datos/diciembre_2015.db`.
