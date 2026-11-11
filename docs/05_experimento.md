# Experimento

Antes de fijar el modelo se midieron nueve configuraciones con la misma prueba: 8 días de previsión desde 12 fechas de 2015. La que más bajó el error fue buscar los hiperparámetros de cada serie, que lo dejó en 9,19 unidades frente a 9,90 con los valores por defecto y 10,68 de la regla de la semana anterior. Esa es la configuración que implementa este repositorio. Este documento cuenta qué se probó, cómo se comparó y qué quedó sin incorporar.

Todo el experimento se hizo con la primera versión del código. Una revisión posterior encontró en ella dos errores que afectan a todas las configuraciones: la media de ventas del mes no distinguía los meses y la preselección dejaba entrar columnas que ningún árbol podía usar. Con los dos corregidos, la configuración adoptada baja de 9,19 a 8,87 en la misma prueba ([CHANGELOG.md](../CHANGELOG.md)). Las cifras de este documento son las de la primera versión y sirven para comparar las configuraciones entre sí.

## Por qué hizo falta

La primera versión del modelo usaba los hiperparámetros por defecto y se había medido a 8 días desde una sola fecha. Con una sola fecha, el resultado depende de cómo fue ese mes. El experimento cambió la medida antes que el modelo: 12 orígenes repartidos por 2015, cada uno con su propio entrenamiento. Diciembre se midió también, desde 4 orígenes, como contraste.

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

## Resultados en 2015 y en diciembre

Error a 8 días por serie y día, quitando los decimales. En 2015, desde 12 fechas, la regla de la semana anterior da 10,68. En diciembre, desde 4 fechas y con los modelos entrenados hasta el 30/11, da 10,90.

| Configuración | 2015 | Intervalo del 95 % de la diferencia con la regla, 2015 | Gana en (de 240) | Diciembre |
|---|---|---|---|---|
| Hiperparámetros por defecto | 9,90 | -1,41 a -0,19 | 151 | 9,27 |
| Sin los días anteriores a la primera venta | 9,67 | -1,59 a -0,40 | 154 | 8,90 |
| Con la marca de 2013 | 9,71 | -1,61 a -0,33 | 151 | 9,19 |
| Las dos anteriores juntas | 9,90 | -1,39 a -0,21 | 150 | 9,39 |
| **Búsqueda de hiperparámetros** | **9,19** | -2,08 a -0,93 | 153 | **9,55** |
| Competición entre algoritmos | 9,19 | -2,14 a -0,82 | 155 | 9,00 |
| Búsqueda, sin los días anteriores | 9,09 | -2,12 a -1,05 | 159 | 10,90 |
| Búsqueda, con la marca de 2013 | 9,06 | -2,21 a -1,02 | 156 | 10,58 |
| Búsqueda, con las dos | 9,06 | -2,33 a -0,93 | 155 | 10,91 |

La elección se hizo con 2015. En diciembre el orden cambia: la búsqueda, que es la que más baja el error en 2015, queda detrás de cinco configuraciones. Diciembre son 4 fechas y una sola serie mueve mucho la cifra (apartado siguiente), así que las dos columnas no se contradicen con seguridad, pero la ventaja de la búsqueda no se confirma en diciembre.

Tres lecturas:

1. **Todas ganan a la regla.** El intervalo queda por debajo de cero en las nueve. Con varios orígenes, incluso el modelo por defecto mejora a la semana anterior.
2. **La búsqueda es el cambio que más aporta en 2015.** Baja el error de 9,90 a 9,19. La competición entre algoritmos empata con ella en 9,19: el error absoluto suma lo mismo en las dos, aunque se reparte distinto por día del horizonte. Con el empate se mantuvo un solo algoritmo.
3. **Quitar los decimales da menos error que redondear** en las nueve configuraciones. En la búsqueda, 9,19 frente a 9,34.

## Lo que no se incorporó

Con la búsqueda ya adoptada, las dos correcciones de datos se midieron encima. La mejor combinación da 9,06 frente a 9,19, una diferencia que no se distingue del azar: su intervalo incluye el cero. En diciembre la búsqueda con las dos correcciones da 10,91 y la búsqueda sola, 9,55. Casi toda esa diferencia la pone una serie, `CA_3 · FOODS_3_090`, que deja de venderse a mitad de mes. El modelo se quedó con la búsqueda sola, y las dos correcciones quedan medidas y sin incorporar.

## Una comprobación sobre la validación

El experimento midió también si la validación a un día estaba inflada por ajustar las codificaciones y la preselección con todos los días de la serie. Con los hiperparámetros por defecto, la validación dio 8,40 con ese ajuste y 8,29 ajustando solo con los días de entrenamiento de cada corte. El efecto existe en el diseño, pero no mejoraba la cifra.

## Cómo repetirlo

```bash
python scripts/backtest.py
```

Repite la prueba desde 12 fechas con la configuración adoptada y deja `informes/backtest.json` e `informes/backtest_previsiones.csv`, con las 1.920 previsiones. Tarda entre una y dos horas. `python ejecutar_todo.py --backtest` la incluye en la reproducción completa.

## Límites

- El repositorio reproduce la configuración adoptada. Las otras ocho se midieron antes de construirlo y su código no está aquí: sus cifras no se pueden regenerar con estos scripts.
- La prueba desde 12 fechas sirvió para elegir, así que su cifra no es una medida ciega. Diciembre tampoco lo es del todo, porque se consultó en este experimento.
- Las nueve configuraciones se midieron con la primera versión del código, antes de corregir la media del mes y la preselección. No se han vuelto a medir con la versión corregida.
- Los orígenes están separados 28 días y caen siempre en el mismo día de la semana. Una previsión lanzada otro día de la semana no está medida.

## Fuente de las cifras

Las cifras de la versión corregida de la configuración adoptada están en `informes/backtest.json`. Las de las dieciocho combinaciones (nueve configuraciones por dos formas de redondear), con su error por día de horizonte, las de diciembre con cuatro orígenes y las de la validación con y sin ajuste están en [`informes/experimento.json`](../informes/experimento.json), que guarda el resultado del experimento tal como se ejecutó antes de construir este repositorio.
