# Modelo y validación

Cada tienda y producto tiene su propio modelo, 20 en total. Todos se miden contra la misma referencia: repetir la venta del mismo día de la semana anterior. El error se mide de tres maneras, de la más rápida a la más exigente, y la última se reservó para una sola ejecución. Este documento explica el modelo, la búsqueda de hiperparámetros y qué dice cada medida. Los resultados están en [04_evaluacion.md](04_evaluacion.md).

## Un modelo por serie

Las 20 series tienen niveles y comportamientos distintos, así que cada una aprende por separado sus codificaciones del calendario, sus variables (de 63 a 70) y sus hiperparámetros. Añadir una serie es entrenar un modelo más con el mismo código. El coste es que una serie no aprovecha lo que enseñan las demás.

El algoritmo es `HistGradientBoostingRegressor`, de scikit-learn: árboles de decisión que se suman uno tras otro, cada uno corrigiendo el error de los anteriores. Trabaja bien con variables numéricas en escalas distintas y no pide normalizarlas. Se entrena sin parada temprana, con el número de árboles como un hiperparámetro más de la búsqueda.

## Búsqueda de hiperparámetros

Para cada serie se prueban 10 combinaciones al azar de esta rejilla, con semilla fija, más los valores por defecto del algoritmo (tasa 0,1, 100 árboles, 31 hojas, 20 días por hoja y sin regularización), que entran siempre para que la búsqueda nunca quede peor que no buscar:

| Hiperparámetro | Valores |
|---|---|
| Tasa de aprendizaje | 0,03 · 0,05 · 0,1 · 0,2 |
| Número de árboles | 100 · 200 · 400 |
| Hojas por árbol | 15 · 31 · 63 |
| Mínimo de días por hoja | 10 · 20 · 50 |
| Regularización L2 | 0 · 0,1 · 1 |

Cada combinación se puntúa con validación temporal: tres cortes consecutivos de 8 días al final de la serie, cada uno previsto con un modelo entrenado solo con los días anteriores. Gana la combinación con menor error medio en los tres cortes. Esa combinación se reentrena después con todos los días disponibles.

Hasta la versión del 11/11/2026, los valores por defecto estaban en la rejilla pero ninguno de los 10 candidatos sorteados los usaba, así que la búsqueda no podía elegirlos. La búsqueda se adoptó después de medirla contra ellos ([05_experimento.md](05_experimento.md)).

## Referencia y métrica

La referencia es la regla que aplicaría un responsable de compras sin modelo: prever para cada día la venta del mismo día de la semana anterior. Cuando se prevén 8 días desde un origen, la venta de la semana anterior de los últimos días todavía no se conoce. En ese caso la referencia usa la de dos semanas antes, para que compita con la misma información que el modelo.

La métrica es el error absoluto medio, en unidades por serie y día. Se eligió frente a un error en porcentaje porque el 14,1 % de los días de la historia vende cero. Con una venta real de cero, un porcentaje no se puede calcular.

## Tres medidas

**Validación a un día.** Es la que usa la búsqueda: los 24 últimos días de la historia, del 07/11 al 30/11/2015, en tres cortes de 8. Cada día se prevé con las ventas reales de los días anteriores, es decir, a un día vista. Es rápida y sirve para comparar combinaciones, pero no mide el uso real, que es prever 8 días seguidos.

**Prueba desde 12 fechas.** `scripts/backtest.py` toma 12 fechas de origen de 2015, una cada 28 días, del 18/01 al 22/11. En cada una repite el proceso entero con los días hasta esa fecha: codificación, preselección, búsqueda y entrenamiento de los 20 modelos. Después prevé los 8 días siguientes de forma recursiva y los compara con la venta real. Son 240 previsiones de 8 días, una por serie y origen, y ninguna toca diciembre.

**Prueba final.** Diciembre de 2015 vive en una base aparte y nunca se usó para entrenar ni para elegir hiperparámetros. Sí se miró antes de fijar el modelo: el experimento midió sus nueve configuraciones también en diciembre y esa medida pesó en la decisión de no incorporar dos correcciones de datos ([05_experimento.md](05_experimento.md)). Por eso no es una prueba ciega del todo. Con los modelos entrenados hasta el 30/11/2015 se midieron dos cosas: la previsión a un día vista del 16/12 y la previsión a 8 días del 24 al 31/12, hecha con las ventas conocidas hasta el 23/12.

## Previsión recursiva

Para prever 8 días, el modelo prevé primero el día siguiente al origen. Esa previsión se escribe como si fuera la venta de ese día, se recalculan las variables y se prevé el siguiente, hasta completar el horizonte. El modelo es siempre el mismo, entrenado a un día vista; lo que cambia es que desde el segundo día sus retardos contienen previsiones.

Cada previsión se acota en cero y se pasa a unidades enteras quitando los decimales. Cortar en lugar de redondear se midió en el experimento: en la prueba desde 12 fechas dio menos error en todas las configuraciones.

Los niveles superiores se obtienen sumando: la previsión de una tienda es la suma de sus productos y la del total, la suma de las tiendas. Por construcción, los tres niveles cuadran todos los días.

## Reproducibilidad

- La semilla es 42 en el modelo, en la búsqueda y en la información mutua. La búsqueda se ejecuta en un solo hilo.
- Las versiones de las librerías están fijadas en `requirements.txt`.
- Cada entrenamiento guarda un manifiesto con la fecha, las versiones, la huella de las dos bases y la validación de cada serie. Los modelos no se cargan si la versión de scikit-learn o de pandas ha cambiado.
- `tests/probar_resultados.py` compara las cifras que salen con las de `tests/cifras_de_referencia.json`, con una tolerancia de 0,05 unidades. Las de los datos y las de la regla vienen de otra implementación de la misma cadena; las del modelo se recalcularon aparte desde las bases, sin el paquete del repositorio. Sirven para saber si un cambio mueve las cifras sin querer.

## Límites

- En la validación a un día, las codificaciones del calendario y la preselección se ajustan con todos los días de la serie, también los de los tres cortes. El efecto se midió con los hiperparámetros por defecto y movió poco la cifra: 8,40 con ese ajuste y 8,29 ajustando solo con los días de entrenamiento de cada corte.
- La validación a un día es la que elige los hiperparámetros, así que su cifra es algo optimista. La prueba desde 12 fechas no tiene ninguno de los dos efectos, porque en cada origen se ajusta todo solo con el pasado.
- La prueba desde 12 fechas sirvió para elegir la configuración del modelo, y diciembre se consultó en el experimento. Ninguna de las tres medidas es del todo ciega; la que menos intervino es la prueba final.

## Fuente de las cifras

La rejilla, los cortes y la semilla salen de `src/forecast/modelo.py`; las fechas de origen, de `informes/backtest.json`. El porcentaje de días a cero procede del análisis de calidad previo a este repositorio, y las cifras 8,40 y 8,29, del experimento descrito en el documento 05.
