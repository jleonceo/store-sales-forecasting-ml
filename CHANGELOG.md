# Cambios

## 1.1 · 11/11/2026

Una revisión externa del código encontró errores en la primera versión. Ninguno hacía falsas las cifras publicadas, que eran las de ese modelo medidas bien, pero dos limitaban el modelo y tres dejaban el proceso de producción por debajo de lo que prometía. Todos tienen ahora una prueba que los provoca.

**Modelo**
- La media de ventas del mes no distinguía los meses. El suavizado pedía 100 días para dar peso a un valor, y una serie tiene como mucho 93 días de un mismo mes en tres años. Ahora pide 20 días, con un suavizado más gradual.
- La preselección dejaba entrar columnas que ningún árbol podía usar: eventos de 2 o 3 días al año y columnas constantes. Ahora entran solo las variables que un árbol puede usar, de 63 a 70 por serie.
- La media del día de la semana entraba dos veces, por su número y por su nombre. Ahora entra una.
- La búsqueda de hiperparámetros no podía elegir los valores por defecto del algoritmo. Ahora son siempre uno de los candidatos.

Con los cambios del modelo, la prueba desde 12 fechas de 2015 baja de 9,19 a 8,87 unidades por serie y día, frente a 10,68 de la regla de la semana anterior.

**Producción**
- El contrato de entrada dejaba pasar una venta vacía a mitad de la historia y una serie sin ninguna venta. Ahora para.
- El reentreno comparaba el error de dos modelos medido en días distintos. Ahora compara cuánto mejora cada uno a la regla en sus propios días.
- Dos vueltas atrás seguidas restauraban el modelo recién retirado. Ahora restauran el anterior.

**Medidas nuevas**
- La prueba desde 12 fechas compara también con dos reglas más exigentes, la media de los 7 últimos días y la media del mismo día en 4 semanas, y mide el error al sumar las tiendas.
- Los resultados recogen diciembre entero, mañana a mañana, además de los dos días de la prueba final.
- La prueba de las portadas comprueba también los recuentos y los porcentajes.

**Documentación**
- Diciembre se consultó en el experimento para decidir no incorporar dos correcciones de datos. La documentación decía que no había intervenido en ninguna decisión, y ya lo dice.
- El experimento publica su columna de diciembre completa.

## 1.0 · 11/11/2026

Primera versión publicada.
