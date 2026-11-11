# Producción

El modelo se entrega como un proceso por lotes que se ejecuta cada mañana: comprueba los datos del día, prevé los 8 días siguientes y deja la previsión con su registro. Un flujo de GitHub Actions lo ejecuta sobre las 31 mañanas de diciembre de 2015 y las 31 terminan bien. Diciembre ya se usó en la prueba final del modelo, así que esta simulación demuestra el funcionamiento del proceso y no es una prueba nueva de su acierto.

## Las piezas

Todo vive en `produccion/` y se apoya en el paquete `src/forecast/`. Las rutas, las fechas y la tolerancia del reentreno están en `produccion/config.json`; los scripts no llevan ninguna escrita.

| Script | Qué hace |
|---|---|
| `reentrenar.py` | Entrena los 20 modelos con las ventas hasta una fecha y decide si pasan a ser los que se usan. |
| `prever.py --dia` | La ejecución de una mañana: comprueba los datos y prevé 8 días desde ese día. |
| `evaluar.py --dia` | Compara la previsión de una mañana con la venta real que ya exista. |
| `simular_diciembre.py` | Encadena los tres sobre las 31 mañanas de diciembre y escribe el informe del despliegue. |
| `volver_atras.py` | Restaura el modelo anterior. |

## Una mañana

`prever.py --dia 2015-12-24` reproduce lo que se sabría esa mañana. Antes de nada borra las ventas del día 24 en adelante, de modo que el proceso no puede usar una venta que todavía no existe. Después hace cuatro cosas:

1. **Comprueba los datos del día** contra el [contrato de entrada](../produccion/contrato_entrada.md): están las 20 series, ninguna tiene una venta vacía antes del día, todas traen la venta de la víspera y llegan el calendario y el precio del propio día. Si algo falla, para sin dejar previsión, anota el motivo en el registro de ejecuciones y termina con error.
2. **Carga los modelos en uso.** Si la versión de scikit-learn o de pandas no es la del entrenamiento, para y pide reentrenar.
3. **Prevé los 8 días** de forma recursiva y escribe `produccion/salidas/<día>/prevision.csv`, con una fila por serie y día.
4. **Deja constancia.** `resumen.json` guarda las filas de entrada, la huella de esos datos, el modelo usado, la duración y el estado. `ejecuciones.csv` añade una fila por ejecución, haya ido bien o mal.

Si una mañana se ejecuta dos veces, la carpeta anterior se archiva antes de escribir la nueva. Ninguna salida se pisa.

## Medir cada previsión

`evaluar.py` añade a cada previsión la venta real y la referencia de la semana anterior, y escribe `evaluacion.json` con el error en total, por día y por serie. Las previsiones cuyo día todavía no tiene venta real quedan sin medir y se cuentan aparte. El proceso nunca calcula un error con una venta que no existe, y `tests/probar_evaluar.py` lo comprueba con un caso calculado a mano.

## Reentreno

Reentrenar no pisa el modelo en uso. `reentrenar.py` entrena en una carpeta de candidato y compara su error de validación con el del modelo vigente:

- Si el candidato no valida peor, pasa a vigente y el anterior se guarda en `modelos/anteriores/`. Cada modelo se valida en sus últimos días de entrenamiento, que cambian de un reentreno a otro, así que la comparación divide cada error por el de la regla en esos mismos días: lo que se compara es cuánto mejora cada modelo a la regla, con una tolerancia de 0,01.
- Si valida peor, el vigente sigue en uso y el candidato se queda aparte para revisarlo.

Cada modelo guardado lleva un manifiesto con la fecha hasta la que se entrenó, las versiones de las librerías, la huella de las dos bases y la validación de cada serie. La carpeta `modelos/` no se sube al repositorio: se regenera al reentrenar.

## Vuelta atrás

`python produccion/volver_atras.py` restaura como vigente el último modelo de `modelos/anteriores/`. El que se retira tampoco se borra: se guarda con la marca `_retirado` y no cuenta en la siguiente vuelta atrás, que restaura el modelo anterior a ese. El código se vuelve atrás con git, a la versión etiquetada que se quiera recuperar.

## Avisos

- **Por error.** Si una ejecución falla, el flujo de GitHub Actions falla y GitHub avisa por correo a quien lo lanzó.
- **Por ausencia.** Al acabar, la simulación comprueba que estén todas las mañanas de la ventana en estado correcto. Si falta alguna, termina con error y el flujo también.

## Simulación de diciembre

`simular_diciembre.py` reentrena una vez con las ventas hasta el 30/11/2015 y ejecuta después las mañanas del 01/12 al 31/12, una detrás de otra. Cada mañana conoce un día más de ventas y rehace su previsión con los mismos modelos. Al final mide todas las previsiones y escribe `produccion/salidas/registro.csv`, con una fila por mañana, e `informes/despliegue.json`.

El informe del despliegue recoge tres comprobaciones de principio a fin:

- **No falta ninguna mañana.** De las 31 esperadas se hicieron 31. Suman 4.400 previsiones, todas medidas.
- **La mañana del 24/12 da las cifras esperadas.** Da 9,61 frente a 10,05 de la referencia, las mismas que guarda `tests/cifras_de_referencia.json`, recalculadas aparte desde las bases sin el paquete del repositorio.
- **Un día nuevo cambia la previsión.** Entre la mañana del 23 y la del 24 hay 140 previsiones para los mismos días. De ellas, 98 cambian al conocerse la venta del 23.

Desde el 25/12 la base ya no trae calendario ni precio para los 8 días completos, porque los datos acaban el 31/12. El proceso prevé los días que hay, de 7 a 1, y lo anota como aviso en el resumen de esa mañana.

## El flujo en GitHub Actions

`.github/workflows/produccion.yml` ejecuta la simulación en un servidor de GitHub, con Ubuntu y Python 3.13. Se lanza a mano desde la pestaña Actions, con el botón Run workflow, y también se ejecuta cuando cambia el código de `produccion/` o de `src/`. Cada ejecución deja tres cosas:

- el resultado, en verde o en rojo, con su fecha en el historial;
- el registro de las 31 mañanas, como tabla en el resumen de la ejecución;
- las salidas y el manifiesto del modelo, como artefacto descargable con el nombre `salidas-produccion`.

Ese historial es la prueba del despliegue que cualquiera puede consultar. El segundo flujo, `ci.yml`, ejecuta `ejecutar_todo.py` en cada cambio: las pruebas, la simulación, los resultados y la comprobación de las cifras.

## Límites

- La simulación usa un mes que ya sirvió de prueba final. Demuestra que el proceso funciona día a día y no mide de nuevo el modelo.
- En las 31 mañanas, la previsión a 8 días tuvo menos error que la referencia en 15. Las mañanas en que la referencia quedó por delante se concentran entre el 10 y el 23 de diciembre. El modelo no se reentrena durante el mes.
- El flujo se lanza a mano o al cambiar el código. No hay una ejecución diaria programada, porque los datos son históricos.
- Los datos de cada mañana salen de las dos bases del repositorio. La conexión con un sistema de ventas real no está construida.

## Fuente de las cifras

Las cifras de la simulación están en `informes/despliegue.json`, en `informes/resultados.json` (bloque `simulacion`) y en `produccion/salidas/registro.csv`. La tolerancia del reentreno está en `produccion/config.json`.
