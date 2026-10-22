# Acuíferos de Francia

Compara cada mes el nivel de los piezómetros de Francia (pozos de control donde se mide el nivel del agua
subterránea) con el mismo mes de todos los años de su serie
y coloca el departamento frente a la restricción por sequía en vigor para las aguas subterráneas.
Niveles de Hub'Eau (BRGM); restricciones de VigiEau. Web: https://asensio94.github.io/acuiferos-francia/

> **Estado: activo.** Se actualiza solo y sigue en desarrollo.

## Cómo funciona

1. **Piezómetros.** `acuiferos/hubeau.py` pide a la [API Piézométrie de Hub'Eau](https://hubeau.eaufrance.fr/page/api-piezometrie)
   los puntos con alguna medida en los últimos 45 días (unos 2 600). Un punto que deja de medir conserva
   su serie y su fila.
2. **Niveles diarios.** Para un punto nuevo se descarga toda su serie; después, cada día, los últimos tres
   meses, que el productor puede corregir al validarlos. Una consulta de Hub'Eau no devuelve más de
   20 000 filas, así que un tramo largo se parte por la mitad hasta que cabe. Se descartan las medidas
   calificadas de «Incorrecte» y las de naturaleza dinámica (`D`) o influida por bombeos (`I`).
3. **Media mensual.** Varias medidas de un día cuentan como su media, y el mes es la media de sus días
   (`data/monthly/<bss_id>.csv`). Un mes cuenta si tiene al menos dos tercios de las medidas que el pozo
   suele tener al mes (la mediana de los 24 meses anteriores).
4. **Índice.** Como el IPS del BRGM, el nivel del último mes completo se sitúa entre ese mismo mes de los
   demás años, con al menos 15 años. La probabilidad es la empírica, rango / (n + 1), sin ajustar ninguna
   curva, y se pasa a siete clases con los umbrales del boletín del BRGM (0,10, 0,20, 0,40, 0,60, 0,80 y
   0,90). Un nivel por debajo de todos los demás años es «mínimo de la serie».
5. **Mapa interpolado.** En el navegador, cada punto toma la media de la probabilidad de los piezómetros
   clasificados a menos de 30 km, ponderada por el inverso del cuadrado de la distancia, y se pinta con su
   clase. El color se desvanece de 10 a 30 km del piezómetro más cercano y se recorta al contorno de Francia.
6. **Restricciones.** `acuiferos/vigieau.py` guarda cada día el nivel más alto en vigor en cada departamento
   para las aguas subterráneas, superficiales y de abastecimiento (`data/vigieau.csv`).
7. **Indicios.** Con al menos tres piezómetros clasificados, un departamento se marca si la mitad o más
   están bajos o muy bajos y no tiene restricción más allá de la vigilancia, o si tiene alerta reforzada
   o crisis y la mediana de sus piezómetros está en torno a lo normal o más alta.
8. **Web.** `acuiferos/web.py` escribe `docs/index.html` (mapa, tabla de departamentos, los más bajos y el
   método), `docs/fr/index.html` (`acuiferos/web_fr.py`: lo mismo en francés salvo el mapa y las fichas, que
   enlaza en la página en español), `docs/puntos.json` para el mapa y una ficha JSON por piezómetro con sus 36 últimos meses y la
   banda histórica de cada mes, y el nivel en metros respecto a lo habitual y bajo el punto de medida.
9. **Señales.** `acuiferos/signals.py` escribe `docs/signals.json` para
   [Estado de las IBA](https://github.com/Asensio94/estado-iba), en el formato común de los proyectos hermanos
   ([CONTRATO.md](https://github.com/Asensio94/estado-iba/blob/main/CONTRATO.md), versión 2, país `FR`, tipo
   `groundwater_level`). Hay una señal por piezómetro cuyo último mes completo está en «bajo» o «muy bajo»
   (probabilidad 0,20 o menos), las mismas clases de la web: no hay otro umbral. Cada una lleva el código INSEE
   de su municipio, `precision: "punto"` con las coordenadas del pozo, la fecha de su última medida, el enlace a
   su ficha (`https://asensio94.github.io/acuiferos-francia/#<bss_id>`), la clase en `status` (`muy bajo` o
   `bajo`) y en `value` los metros respecto a la mediana de ese mes en los demás años (negativo: por debajo).
   En `details` van el mes evaluado, la probabilidad, los años de referencia, el nivel en m NGF, si es el
   mínimo de la serie y la masa de agua. Un test valida el fichero contra una copia del esquema de estado-iba
   (`tests/signals.schema.json`).

## Contraste / validación

Contra el boletín de situación de las aguas subterráneas del BRGM del 1 de octubre de 2026 (septiembre),
según lo citó la prensa especializada:

| Septiembre de 2026 | Aquí | BRGM |
|---|---|---|
| Por debajo de lo normal (probabilidad ≤ 0,40) | 64,3 % | 66 % |
| Lo mismo un año antes (mismos piezómetros) | 30,7 % | 31 % |
| Nivel en descenso respecto a agosto | 75,4 % | 81 % |

El BRGM usa una selección de puntos y ajusta una distribución a cada mes; aquí entran todos los
piezómetros con 15 años de referencia y se usa el orden. El descenso se mide aquí entre medias mensuales.
Pendiente: contrastar clase a clase con el mapa del boletín.

## Límites

- Los últimos meses son datos brutos y pueden cambiar al validarse.
- El BRGM ajusta una distribución a cada mes; aquí se usa el orden de los valores. Puede haber diferencias
  de una clase cerca de los umbrales.
- VigiEau da el nivel más alto de las zonas de cada departamento, que no coinciden con los acuíferos.
- La restricción es la de hoy y el nivel es el del último mes completo.
- Una serie con una tendencia larga de descenso queda en «muy bajo» mes tras mes, porque se compara con
  todos sus años, también los anteriores al descenso.
- El mapa interpolado mezcla acuíferos distintos y suaviza límites que pueden ser bruscos: da la tendencia
  regional, no el estado de un sitio concreto.
- Los metros de la ficha (distancia a la mediana del mes y nivel bajo el punto de medida) sirven para entender
  cada pozo, no para compararlos: un metro no pesa igual en un kárstico que en un aluvial. Por eso clases y
  mapa usan la probabilidad.
- El nivel bajo el punto de medida es altitud menos nivel: el punto suele ser el brocal, algo por encima del
  suelo, y en un acuífero cautivo el nivel es una presión que puede quedar por encima del suelo (surgente).
- No hay mapa en metros: la cota interpolada entre acuíferos dibujaría el relieve, y la profundidad cambia
  demasiado del valle a la meseta para interpolarla.
- Los departamentos de ultramar están en la tabla pero no en el mapa.

## Pendiente

- Contrastar clase a clase con el mapa del boletín del BRGM.
- Llevar el mapa y la ficha de cada piezómetro a la página en francés.
- Mostrar cuánto tiempo lleva cada departamento en cada nivel de restricción, con el histórico de
  `data/vigieau.csv` que se va acumulando.

## Uso

```bash
pip install -r requirements.txt
python -m acuiferos.cli geo        # contornos de departamento (una vez)
python -m acuiferos.cli vigieau    # restricciones de hoy
python -m acuiferos.cli fetch      # estaciones y series (la primera vez, unos 60 minutos)
python -m acuiferos.cli page       # docs/
python -m pytest -q
```

## Datos que se guardan

| Fichero | Contenido |
|---|---|
| `data/stations.csv` | Piezómetros: código BSS, municipio, departamento, coordenadas, masa de agua |
| `data/monthly/<bss_id>.csv` | Media mensual del nivel (m NGF) y días con medida |
| `data/latest.csv` | Última medida diaria de cada piezómetro |
| `data/vigieau.csv` | Nivel de restricción por departamento y día |
| `data/departements.geojson` | Contornos de departamento simplificados |

En la web (rama `gh-pages`, rehecha cada día) se publican además `puntos.json`, una ficha por piezómetro en
`p/<bss_id>.json` y `signals.json`.

## Fuentes y licencias

- Niveles: [Hub'Eau, API Piézométrie](https://hubeau.eaufrance.fr/page/api-piezometrie), banco
  [ADES](https://ades.eaufrance.fr/) (BRGM y productores), Licence Ouverte 2.0.
- Restricciones: [VigiEau](https://vigieau.gouv.fr/), Ministerio de la Transición Ecológica, Licence Ouverte 2.0.
- Contornos: IGN Admin Express vía [france-geojson](https://github.com/gregoiredavid/france-geojson), Licence Ouverte.
- Código: MIT. Datos propios (medias mensuales y clases): CC BY 4.0.

Forma parte de [Terra Aperta](https://asensio94.github.io/terra-aperta/), un conjunto de proyectos hermanos de
datos abiertos sobre naturaleza:
[Sub Nocte](https://github.com/Asensio94/sub-nocte) ·
[Vigía de incendios](https://github.com/Asensio94/vigia-incendios) ·
[Centinela Natura](https://github.com/Asensio94/centinela-natura) ·
[Estado de las IBA](https://github.com/Asensio94/estado-iba) ·
[Riesgo de tendidos para aves](https://github.com/Asensio94/riesgo-tendidos-aves) ·
[Observatorio de alegaciones](https://github.com/Asensio94/observatorio-alegaciones) ·
[Grafo de promotores](https://github.com/Asensio94/grafo-promotores) ·
[Vigilancia de humedales](https://github.com/Asensio94/vigilancia-humedales) ·
[Caudal ecológico](https://github.com/Asensio94/caudal-ecologico) ·
[Acuíferos de Francia](https://github.com/Asensio94/acuiferos-francia) ·
[Depuración y baño](https://github.com/Asensio94/depuracion-y-bano) ·
[Construir en zona inundable](https://github.com/Asensio94/zona-inundable)
