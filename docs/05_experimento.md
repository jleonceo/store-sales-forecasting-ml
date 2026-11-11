# Experimento

Antes de fijar el modelo se midieron nueve configuraciones con la misma prueba: 8 días de previsión desde 12 fechas de 2015. La que más bajó el error fue buscar los hiperparámetros de cada serie, que lo dejó en 9,19 unidades frente a 9,90 con los valores por defecto y 10,68 de la regla de la semana anterior. Esa es la configuración que implementa este repositorio. Este documento cuenta qué se probó, con qué regla se eligió y qué quedó sin incorporar.

## Por qué hizo falta

La primera versión del modelo usaba los hiperparámetros por defecto y se había medido a 8 días desde una sola fecha. Con una sola fecha, el resultado depende de cómo fue ese mes. El experimento cambió la medida antes que el modelo: 12 orígenes repartidos por 2015, cada uno con su propio entrenamiento, y diciembre fuera de la elección.

## Cómo se comparó

Todas las configuraciones se compararon con la misma medida: el error absoluto medio de los 8 días en los 12 orígenes de 2015.

## Qué se probó

- Hiperparámetros por defecto, como punto de partida.
- Búsqueda de hiperparámetros por serie: 10 combinaciones de una rejilla, con validación temporal.
- Competición entre seis algoritmos (regresión lineal, ridge, lasso, elastic net, bosque aleatorio y boosting), cada uno con su búsqueda, eligiendo el mejor de cada serie.
- Sin los días anteriores a la primera venta: entrenar cada serie desde que el producto empieza a venderse.
- Con una marca del verano de 2013, una variable que señala de julio a septiembre de 2013, cuando las ventas dan un salto.
- Las combinaciones de las dos últimas entre sí y con la búsqueda.

Cada configuración se midió además con dos formas de pasar la previsión a unidades enteras: quitar los decimales o redondear.

## Resultados en 2015

Error a 8 días por serie y día, quitando los decimales. La regla de la semana anterior da 10,68 en los mismos días.

| Configuración | Error | Intervalo del 95 % de la diferencia con la regla | Gana en (de 240) |
|---|---|---|---|
| Hiperparámetros por defecto | 9,90 | -1,41 a -0,19 | 151 |
| Sin los días anteriores a la primera venta | 9,67 | -1,59 a -0,40 | 154 |
| Con la marca de 2013 | 9,71 | -1,61 a -0,33 | 151 |
| Las dos anteriores juntas | 9,90 | -1,39 a -0,21 | 150 |
| **Búsqueda de hiperparámetros** | **9,19** | -2,08 a -0,93 | 153 |
| Competición entre algoritmos | 9,19 | -2,14 a -0,82 | 155 |
| Búsqueda, sin los días anteriores | 9,09 | -2,12 a -1,05 | 159 |
| Búsqueda, con la marca de 2013 | 9,06 | -2,21 a -1,02 | 156 |
| Búsqueda, con las dos | 9,06 | -2,33 a -0,93 | 155 |

Tres lecturas:

1. **Todas ganan a la regla.** El intervalo queda por debajo de cero en las nueve. Con varios orígenes, incluso el modelo por defecto mejora a la semana anterior.
2. **La búsqueda es el cambio que más aporta.** Baja el error de 9,90 a 9,19. La competición entre algoritmos empata con ella en 9,19. Con el empate se mantuvo un solo algoritmo.
3. **Quitar los decimales da menos error que redondear** en las nueve configuraciones. En la búsqueda, 9,19 frente a 9,34.

## Lo que no se incorporó

Con la búsqueda ya adoptada, las dos correcciones de datos se midieron encima. La mejor combinación da 9,06 frente a 9,19, una diferencia que no se distingue del azar: su intervalo incluye el cero. En diciembre, con cuatro orígenes y los modelos entrenados hasta el 30/11, el orden se invierte: la búsqueda sola da 9,55 y la búsqueda con las dos correcciones, 10,91. El modelo se quedó con la búsqueda sola, y las dos correcciones quedan medidas y sin incorporar.

## Una comprobación sobre la validación

El experimento midió también si la validación a un día estaba inflada por ajustar las codificaciones y la preselección con todos los días de la serie. Con los hiperparámetros por defecto, la validación dio 8,40 con ese ajuste y 8,29 ajustando solo con los días de entrenamiento de cada corte. El efecto existe en el diseño, pero no mejoraba la cifra.

## Cómo repetirlo

```bash
python scripts/backtest.py
```

Repite la prueba desde 12 fechas con la configuración adoptada y deja `informes/backtest.json` e `informes/backtest_previsiones.csv`, con las 1.920 previsiones. Tarda entre una y dos horas. `python ejecutar_todo.py --backtest` la incluye en la reproducción completa.

## Límites

- El repositorio reproduce la configuración adoptada. Las otras ocho se midieron antes de construirlo y su código no está aquí: sus cifras no se pueden regenerar con estos scripts.
- La prueba desde 12 fechas sirvió para elegir, así que el 9,19 no es una medida ciega. La medida ciega es la prueba final ([04_evaluacion.md](04_evaluacion.md)).
- Los orígenes están separados 28 días y caen siempre en el mismo día de la semana. Una previsión lanzada otro día de la semana no está medida.

## Fuente de las cifras

Las cifras de la configuración adoptada (9,19, 10,68, el intervalo y los 153 de 240) están en `informes/backtest.json`. Las de las demás configuraciones, las de diciembre con cuatro orígenes y las de la validación con y sin ajuste proceden del informe del experimento, anterior a este repositorio.
