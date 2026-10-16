"""The published page: index.html, the map layers and one small JSON per piezometer."""
from __future__ import annotations

import json
import shutil
from datetime import date, datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from . import vigieau
from .config import (COMPLETE_SHARE, DATA_DIR, DISCORDANT_LOW_SHARE, DOCS_DIR, MIN_DEPARTMENT_POINTS,
                     MIN_REFERENCE_YEARS, NORMAL_P, POINTS_DIR, REFRESH_MONTHS, SURFACE_FULL_KM,
                     SURFACE_MAX_KM)
from .ips import CLASSES, LABELS, band, class_of, classify, metres, months_before
from .logo import LOGO_SVG, favicon_link
from .report import Department, Point, Report, build

ACCENT, ACCENT_DARK = "#7f3b8c", "#d29be0"
COMMON_CSS = (Path(__file__).parent / "common.css").read_text(encoding="utf-8")
REPO = "https://github.com/Asensio94/acuiferos-francia"
ADES = "https://ades.eaufrance.fr/Fiche/PtEau?Code="
CHART_MONTHS = 36
LOWEST_ROWS = 40
MONTHS = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()

# Diverging: red below normal, blue above, a neutral gray in the middle (BRGM convention).
CLASS_COLORS = {"very_low": "#a8322d", "low": "#d9644a", "mod_low": "#f0a98c", "normal": "#bdb9b2",
                "mod_high": "#93b9dd", "high": "#4f86c0", "very_high": "#2a5592"}
FLAGS = {"low_unrestricted": "Niveles bajos sin restricción", "restricted_normal": "Restricción fuerte con niveles normales"}

SIBLINGS = [
    ("observatorio-alegaciones", "Observatorio de alegaciones"), ("vigia-incendios", "Vigía de incendios"),
    ("centinela-natura", "Centinela Natura"), ("vigilancia-humedales", "Vigilancia de humedales"),
    ("sub-nocte", "Sub Nocte"), ("riesgo-tendidos-aves", "Riesgo de tendidos para aves"),
    ("grafo-promotores", "Grafo de promotores"), ("cartera-cotizadas", "Cartera de las cotizadas"),
    ("cuaderno-campo", "Cuaderno de campo"), ("caudal-ecologico", "Caudal ecológico"),
    ("estado-iba", "Estado de las IBA"), ("acuiferos-francia", "Acuíferos de Francia"),
]

CSS = f""":root{{--accent:{ACCENT};--accent-dark:{ACCENT_DARK};
  --r0:transparent;--r1:#f3efe8;--r2:#e9e2d6;--r3:#ddd2c0;--r4:#cdbfa8}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--r1:#262320;--r2:#2f2b27;--r3:#3a352f;--r4:#474038}}}}
:root[data-theme="dark"]{{--r1:#262320;--r2:#2f2b27;--r3:#3a352f;--r4:#474038}}
main{{max-width:1440px;margin:0 auto;padding:0 16px}}
h2{{font:700 26px/1.1 var(--font-title);text-transform:uppercase;letter-spacing:.03em;margin:32px 0 8px}}
.figures small{{font:400 13px/1.3 var(--font-text);color:var(--muted);text-transform:none;letter-spacing:0}}
#map{{height:min(72vh,640px);border:1px solid var(--line);background:var(--paper)}}
.leaflet-container{{background:var(--paper);font:13px var(--font-text)}}
.leaflet-bar a,.leaflet-tooltip{{background:var(--paper);color:var(--ink);border-color:var(--line)}}
.dep{{stroke:var(--muted);stroke-width:.7;fill-opacity:1}}
.dep.r0{{fill:var(--r0)}}.dep.r1{{fill:var(--r1)}}.dep.r2{{fill:var(--r2)}}.dep.r3{{fill:var(--r3)}}.dep.r4{{fill:var(--r4)}}
.dep.rx{{fill:transparent}}
.hide-restr .dep{{fill:transparent!important}}
.leaflet-deps-pane svg{{max-width:none!important;max-height:none!important}}
.surf .dep{{fill:transparent!important}}
.legend[hidden]{{display:none}}
.view{{display:flex;flex-wrap:wrap;gap:6px 14px;margin:10px 0;font-size:14px;align-items:center}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 18px;margin:10px 0;font-size:14px;align-items:center}}
.legend span{{display:inline-flex;align-items:center;gap:6px}}
.sw{{width:12px;height:12px;border-radius:50%;display:inline-block;border:1px solid var(--line)}}
.sq{{width:14px;height:12px;display:inline-block;border:1px solid var(--muted)}}
.legend label{{display:inline-flex;gap:6px;align-items:center;cursor:pointer}}
.wrap{{overflow-x:auto}}
table.t{{width:100%;border-collapse:collapse;font-size:.92rem}}
.t th{{text-align:left;font-weight:600;color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;
  padding:8px 10px;border-bottom:2px solid var(--line);white-space:nowrap}}
.t td{{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
.t .num{{text-align:right;font-family:var(--font-data);font-variant-numeric:tabular-nums;white-space:nowrap}}
.t .sub{{display:block;color:var(--muted);font-size:.82rem}}
.t tr[hidden]{{display:none}}
tr:target td{{background:color-mix(in srgb,var(--accent) 10%,transparent)}}
.tools{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}}
.tools button{{font:inherit;font-size:.9rem;padding:6px 12px;border:1px solid var(--line);border-radius:999px;
  background:var(--paper);color:var(--ink);cursor:pointer}}
.tools button[aria-pressed="true"]{{background:var(--accent);border-color:var(--accent);color:var(--paper)}}
.flag{{font-weight:600}}
#ficha{{margin:16px 0}}
#ficha h3{{margin:0 0 4px;font:600 20px/1.2 var(--font-title);text-transform:uppercase;letter-spacing:.04em}}
#ficha dl{{display:grid;grid-template-columns:max-content 1fr;gap:2px 14px;font-size:14.5px;margin:10px 0}}
#ficha dt{{color:var(--muted)}}#ficha dd{{margin:0}}
svg.chart{{width:100%;height:auto;display:block;max-width:820px}}
.chart .band{{fill:var(--accent);opacity:.14}}
.chart .ext{{stroke:var(--muted);stroke-dasharray:1 3;fill:none;stroke-width:1}}
.chart .med{{stroke:var(--muted);stroke-dasharray:5 3;fill:none;stroke-width:1.2}}
.chart .line{{stroke:var(--ink);stroke-width:2;fill:none;stroke-linejoin:round}}
.chart .axis{{stroke:var(--line);stroke-width:1}}
.chart text{{fill:var(--muted);font:12px var(--font-data)}}
.chart .hit{{fill:transparent}}.chart .hit:hover{{fill:var(--ink);opacity:.06}}
.chart circle{{stroke:var(--paper);stroke-width:2}}
"""


def _n(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def _dec(x: float, d: int = 2) -> str:
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def _pct(x: float) -> str:
    return f"{round(100 * x)} %"


def month_name(m: str) -> str:
    return f"{MONTHS[int(m[5:7]) - 1]} de {m[:4]}"


def point_json(p: Point, month: str) -> dict:
    shown = list(reversed([month] + months_before(month, CHART_MONTHS - 1)))
    history = {m: v for m, v in p.series.items() if m < shown[0]}
    s = p.station
    r = p.now
    anomaly, depth = metres(p.series, r, s["altitude"])
    return {
        "id": s["bss_id"], "code": s["code_bss"], "commune": s["commune"], "insee": s["commune_insee"],
        "department": s["department"], "department_name": s["department_name"],
        "water_body": s["water_body_name"], "aquifer": s["aquifer"], "altitude": s["altitude"],
        "first": s["first"], "ades": ADES + s["code_bss"],
        "now": {"month": r.month, "status": r.status, "value": r.value, "days": r.days, "years": r.years,
                "p": r.p, "cls": r.cls, "record": r.record, "anomaly": anomaly, "depth": depth},
        "months": [[m, p.series[m][0], classify(p.series, m).cls] if m in p.series else [m, None, None]
                   for m in shown],
        "band": band(history), "band_until": int(shown[0][:4]) - 1,
    }


def write_points(rep: Report) -> None:
    if POINTS_DIR.exists():
        shutil.rmtree(POINTS_DIR)
    POINTS_DIR.mkdir(parents=True)
    compact = []
    for p in rep.points:
        s = p.station
        (POINTS_DIR / f"{s['bss_id']}.json").write_text(
            json.dumps(point_json(p, rep.month), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        if s["lat"] and s["lon"]:
            compact.append([s["bss_id"], float(s["lat"]), float(s["lon"]), p.now.cls or "", s["commune"],
                            p.now.record, round(p.now.p, 4) if p.now.cls else None,
                            *metres(p.series, p.now, s["altitude"])])
    (DOCS_DIR / "puntos.json").write_text(json.dumps(compact, ensure_ascii=False, separators=(",", ":")),
                                          encoding="utf-8")
    geo = json.loads((DATA_DIR / "departements.geojson").read_text(encoding="utf-8"))
    (DOCS_DIR / "departements.geojson").write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":")),
                                                   encoding="utf-8")


def _dept_row(d: Department) -> str:
    n = len(d.classified)
    restr = "—" if d.restriction is None else vigieau.LABELS[d.restriction]
    if n:
        median_cls = class_of(d.median_p)
        low = f'{_n(d.low)} <span class="sub">{_pct(d.low_share)}</span>'
        med = escape(LABELS[median_cls])
    else:
        low, med = "—", "—"
    flag = f'<span class="flag">{FLAGS[d.flag]}</span>' if d.flag else ""
    return (f'<tr id="d{escape(d.code)}" data-flag="{d.flag}"><td>{escape(d.name)} <span class="sub">{escape(d.code)}</span></td>'
            f'<td>{escape(restr)}</td><td class="num">{_n(n)} <span class="sub">de {_n(len(d.points))}</span></td>'
            f'<td class="num">{low}</td><td>{med}</td><td>{flag}</td></tr>')


def _lowest_rows(rep: Report) -> str:
    low = sorted((p for p in rep.classified if p.now.cls == "very_low"), key=lambda p: (p.now.p, p.station["bss_id"]))
    rows = []
    for p in low[:LOWEST_ROWS]:
        s, r = p.station, p.now
        rec = " · mínimo de la serie" if r.record == "low" else ""
        rows.append(
            f'<tr><td><a href="#{escape(s["bss_id"])}" data-open="{escape(s["bss_id"])}">{escape(s["commune"] or s["code_bss"])}</a>'
            f'<span class="sub">{escape(s["code_bss"])}</span></td>'
            f'<td>{escape(s["department_name"])}</td><td>{escape(s["water_body_name"] or "—")}</td>'
            f'<td class="num">{_dec(r.value)}</td><td class="num">{_n(r.years)}</td>'
            f'<td>{escape(LABELS[r.cls])}{rec}</td></tr>')
    return "\n".join(rows), len(low)


def method_html(rep: Report) -> str:
    statuses = {k: sum(p.now.status == k for p in rep.points) for k in ("ok", "no_data", "incomplete", "short_record")}
    classes = "\n".join(
        f"<tr><td>{escape(label)}</td><td class=\"num\">{_cls_range(i)}</td>"
        f"<td class=\"num\">{_n(sum(p.now.cls == key for p in rep.classified))}</td></tr>"
        for i, (_, key, label) in enumerate(CLASSES))
    return f"""<section class="method" id="metodo">
  <h2>Cómo se calcula</h2>
  <ol>
    <li><b>Piezómetros.</b> Hub'Eau publica la red de seguimiento de las aguas subterráneas de Francia (banco
    ADES, BRGM). Se siguen los {_n(len(rep.points))} piezómetros con alguna medida en los últimos 45 días; si uno deja de
    medir, conserva su serie y aparece sin dato.</li>
    <li><b>Medidas.</b> Se descarga el nivel diario en metros sobre el nivel del mar (NGF) de toda la serie. Se
    descartan las medidas que el productor califica de incorrectas y las tomadas con el pozo bombeando o
    influido por bombeos cercanos (naturaleza «dinámica» o «influida»). Varias medidas de un día cuentan como
    su media.</li>
    <li><b>Mes.</b> El nivel de un mes es la media de sus días con medida. El mes evaluado es el último completo,
    {month_name(rep.month)}. Solo cuenta si tiene al menos {_pct(COMPLETE_SHARE)} de las medidas que ese pozo suele
    tener al mes (la mediana de los 24 meses anteriores): así un pozo que se mide una vez al mes y una sonda
    diaria se juzgan cada uno a su ritmo.</li>
    <li><b>Comparación con su propia historia.</b> El nivel de {MONTHS[int(rep.month[5:]) - 1]} se ordena entre los
    {MONTHS[int(rep.month[5:]) - 1]} de todos los demás años de ese piezómetro; hacen falta al menos
    {MIN_REFERENCE_YEARS}. La posición da la probabilidad empírica de un nivel más bajo, rango / (n + 1), y esa
    probabilidad la clase, con los umbrales del boletín del BRGM. Un nivel por debajo de todos los demás años es
    «mínimo de la serie».</li>
    <li><b>Mapa interpolado.</b> Cada punto del mapa toma la media de la probabilidad de los piezómetros
    clasificados a menos de {SURFACE_MAX_KM} km, con más peso cuanto más cerca (inverso del cuadrado de la
    distancia), y se pinta con la clase de esa media. El color es pleno hasta {SURFACE_FULL_KM} km del piezómetro
    más cercano y se desvanece hasta {SURFACE_MAX_KM} km; más allá no se pinta nada.</li>
    <li><b>Departamentos.</b> En cada departamento se cuentan los piezómetros clasificados y cuántos están en
    «bajo» o «muy bajo». Se compara con el nivel de restricción por sequía en vigor para las aguas
    subterráneas según VigiEau (el más alto de las zonas del departamento), leído cada día.</li>
    <li><b>Indicios.</b> Con al menos {MIN_DEPARTMENT_POINTS} piezómetros clasificados, se marca
    «niveles bajos sin restricción» si {_pct(DISCORDANT_LOW_SHARE)} o más están bajos o muy bajos y no hay
    restricción en subterráneas más allá de la vigilancia; y «restricción fuerte con niveles normales» si hay
    alerta reforzada o crisis y la mediana de los piezómetros está en torno a lo normal o más alta
    (probabilidad por encima de {_dec(NORMAL_P)}). Son indicios para mirar, no veredictos: el prefecto decide con más
    datos (caudales, usos, el decreto marco).</li>
  </ol>
  <h3>Clases</h3>
  <table class="params"><thead><tr><th>Clase</th><th class="num">Probabilidad</th><th class="num">Piezómetros en {month_name(rep.month)}</th></tr></thead>
  <tbody>
{classes}
  </tbody></table>
  <h3>Qué piezómetros quedan sin clase</h3>
  <table class="params"><tbody>
    <tr><th>Clasificados</th><td class="num">{_n(statuses['ok'])}</td></tr>
    <tr><th>Sin medida en el mes</th><td class="num">{_n(statuses['no_data'])}</td></tr>
    <tr><th>Mes incompleto</th><td class="num">{_n(statuses['incomplete'])}</td></tr>
    <tr><th>Menos de {MIN_REFERENCE_YEARS} años de referencia</th><td class="num">{_n(statuses['short_record'])}</td></tr>
  </tbody></table>
  <h3>Validación</h3>
  <p>Contra el boletín de situación de las aguas subterráneas del BRGM del 1 de octubre de 2026 (septiembre de 2026),
  según lo citó la prensa especializada:</p>
  <table class="params"><thead><tr><th>Septiembre de 2026</th><th class="num">Aquí</th><th class="num">BRGM</th></tr></thead><tbody>
    <tr><td>Por debajo de lo normal (probabilidad 0,40 o menos)</td><td class="num">64,3 %</td><td class="num">66 %</td></tr>
    <tr><td>Lo mismo un año antes (mismos piezómetros)</td><td class="num">30,7 %</td><td class="num">31 %</td></tr>
    <tr><td>Nivel en descenso respecto a agosto</td><td class="num">75,4 %</td><td class="num">81 %</td></tr>
  </tbody></table>
  <p>El BRGM usa una selección de puntos de referencia y ajusta una distribución a cada mes; aquí entran todos
  los piezómetros con 15 años y se usa el orden de los valores, sin ajuste. El descenso se mide aquí como media
  de septiembre frente a media de agosto, y el BRGM lo mide sobre el final del mes.</p>
  <h3>Límites</h3>
  <ul>
    <li>Las medidas de los últimos meses son brutas: el productor puede corregirlas al validarlas. Cada día se
    vuelven a leer los últimos {REFRESH_MONTHS} meses.</li>
    <li>VigiEau da el nivel más alto de las zonas de alerta de cada departamento, que no coinciden con los
    acuíferos; un departamento puede tener una zona en crisis y el resto sin restricción.</li>
    <li>La restricción es la de hoy y el nivel es el del último mes completo: el decreto suele basarse en las
    medidas del mes anterior, pero puede ir por delante o por detrás.</li>
    <li>El mapa interpolado mezcla piezómetros de acuíferos distintos, superpuestos a veces, y dibuja
    transiciones suaves donde puede haber un límite brusco entre dos acuíferos. Sirve para ver la tendencia
    regional; para un sitio concreto, mejor los piezómetros.</li>
    <li>Los metros de la ficha son para entender cada pozo, no para comparar unos con otros. «Por debajo de lo
    habitual» es la distancia a la mediana del mismo mes en los demás años, y un metro no pesa igual en un
    acuífero kárstico, que oscila decenas de metros en un año corriente, que en uno aluvial, que oscila uno. Por
    eso las clases y el mapa usan la probabilidad.</li>
    <li>El nivel bajo el punto de medida es la altitud de Hub'Eau menos el nivel. Ese punto suele ser el brocal o
    la tapa del pozo, a veces algo por encima del suelo, y la altitud tiene la precisión con que se anotó. En un
    acuífero cautivo el nivel es una presión: dice hasta dónde subiría el agua en el pozo, no a qué profundidad
    está el acuífero, y puede quedar por encima del suelo (pozo surgente).</li>
    <li>No hay mapa en metros. La cota del agua interpolada entre acuíferos distintos dibujaría sobre todo el
    relieve, y la profundidad cambia demasiado en poca distancia, del valle a la meseta, para interpolarla.</li>
    <li>Los acuíferos lentos (la creta de la cuenca de París) y los rápidos (los kársticos) no responden igual a
    la lluvia; la clase dice cómo está cada uno respecto a sí mismo, no cuál está peor.</li>
    <li>Una serie con una tendencia larga (un acuífero que baja año tras año por las extracciones) queda
    en «muy bajo» mes tras mes: la clase compara con todos los años de la serie, también los de antes del
    descenso. La curva de la ficha lo muestra.</li>
    <li>Los departamentos de ultramar aparecen en la tabla pero no en el mapa.</li>
  </ul>
</section>"""


def _cls_range(i: int) -> str:
    lo = 0.0 if i == 0 else CLASSES[i - 1][0]
    hi = min(CLASSES[i][0], 1.0)
    return f"{_dec(lo)} – {_dec(hi)}"


def render(today: date | None = None) -> Path:
    now = datetime.now(ZoneInfo("Europe/Paris"))
    today = today or now.date()
    rep = build(today)
    DOCS_DIR.mkdir(exist_ok=True)
    write_points(rep)

    classified = rep.classified
    n_low = sum(p.now.cls in ("very_low", "low") for p in classified)
    records = sum(p.now.record == "low" for p in classified)
    flagged = [d for d in rep.departments if d.flag]
    yoy = rep.low_share_vs_year_ago()
    yoy_txt = f"<small>hace un año, {_pct(yoy[1])}</small>" if yoy else ""
    lowest, n_very_low = _lowest_rows(rep)
    restrictions = {d.code: vigieau.rank(d.restriction) if d.restriction is not None else -1 for d in rep.departments}
    classes_js = json.dumps({k: {"label": LABELS[k], "color": CLASS_COLORS[k], "upper": upper}
                             for upper, k, _ in CLASSES}, ensure_ascii=False)
    legend_cls = "".join(f'<span><i class="sw" style="background:{CLASS_COLORS[k]}"></i>{escape(label)}</span>'
                         for _, k, label in CLASSES)
    legend_restr = "".join(f'<span><i class="sq dep r{i}" style="fill:none;background:var(--r{i})"></i>{escape(label)}</span>'
                           for i, label in enumerate(vigieau.LABELS.values()))
    siblings = "\n".join(
        f'    <li{" aria-current=\"page\"" if slug == "acuiferos-francia" else ""}>'
        f'<a href="https://asensio94.github.io/{slug}/">{name}</a></li>' for slug, name in SIBLINGS)
    vig_day = date.fromisoformat(rep.vigieau_date) if rep.vigieau_date else None

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Acuíferos de Francia</title>
<meta name="description" content="El nivel de las aguas subterráneas de Francia frente a su propia historia, y frente a las restricciones por sequía en vigor.">
{favicon_link(ACCENT, ACCENT_DARK)}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
{COMMON_CSS}
{CSS}
</style>
</head>
<body>
<header class="site-header">
  <h1>{LOGO_SVG}Acuíferos de <span>Francia</span></h1>
  <p class="lede">Cada piezómetro de Francia comparado consigo mismo: si el nivel de {month_name(rep.month)} es bajo o alto
  frente al mismo mes de los demás años, y si su departamento tiene restricciones por sequía en las aguas
  subterráneas. Datos de Hub'Eau (BRGM) y VigiEau.</p>
  <div class="figures">
    <div><b>{_n(len(classified))}</b><span>piezómetros clasificados</span><small>de {_n(len(rep.points))} activos</small></div>
    <div><b>{_pct(n_low / len(classified)) if classified else "—"}</b><span>bajos o muy bajos en {MONTHS[int(rep.month[5:]) - 1]}</span>{yoy_txt}</div>
    <div><b>{_n(records)}</b><span>en el mínimo de su serie</span><small>para un mes de {MONTHS[int(rep.month[5:]) - 1]}</small></div>
    <div><b>{_n(len(flagged))}</b><span>departamentos con indicio</span><small>niveles y restricción no cuadran</small></div>
  </div>
</header>
<main>
  <h2>Mapa</h2>
  <div class="view" role="radiogroup" aria-label="Vista del mapa">Ver:
    <label><input type="radio" name="view" value="surf" checked> Nivel interpolado</label>
    <label><input type="radio" name="view" value="pts"> Piezómetros y restricciones</label>
  </div>
  <div class="legend" aria-label="Clase del nivel">{legend_cls}</div>
  <div id="map" class="surf" role="img" aria-label="Mapa del nivel de las aguas subterráneas por clase, interpolado entre piezómetros, y departamentos por restricción en aguas subterráneas"></div>
  <div class="legend" id="restr-legend" aria-label="Restricción VigiEau en aguas subterráneas" hidden>
    <label><input type="checkbox" id="restr" checked> Restricción en aguas subterráneas{f" ({vig_day.day} de {MONTHS[vig_day.month - 1]})" if vig_day else ""}:</label>{legend_restr}
  </div>
  <p class="note" id="map-note"></p>
  <section id="ficha" class="card" hidden aria-live="polite"></section>

  <h2>Departamentos</h2>
  <div class="tools" role="group" aria-label="Filtrar departamentos">
    <button type="button" data-flag="" aria-pressed="true">Todos</button>
    <button type="button" data-flag="any" aria-pressed="false">Con indicio ({_n(len(flagged))})</button>
  </div>
  <div class="wrap"><table class="t" id="deps">
    <thead><tr><th>Departamento</th><th>Restricción subterráneas</th><th class="num">Clasificados</th>
    <th class="num">Bajos o muy bajos</th><th>Mediana</th><th>Indicio</th></tr></thead>
    <tbody>
{chr(10).join(_dept_row(d) for d in rep.departments if d.points)}
    </tbody>
  </table></div>

  <h2>Los más bajos de {month_name(rep.month)}</h2>
  <p class="note">{_n(n_very_low)} piezómetros en «muy bajo»{f"; se muestran los {LOWEST_ROWS} con la probabilidad más baja" if n_very_low > LOWEST_ROWS else ""}.</p>
  <div class="wrap"><table class="t">
    <thead><tr><th>Piezómetro</th><th>Departamento</th><th>Masa de agua</th><th class="num">Nivel<br>m NGF</th>
    <th class="num">Años de<br>referencia</th><th>Clase</th></tr></thead>
    <tbody>
{lowest}
    </tbody>
  </table></div>
</main>
{method_html(rep)}
<footer class="site-footer">
  <p class="principle">Datos públicos, reglas a la vista y cada cifra enlazada a su fuente. Indicios, no veredictos.</p>
  <p>Niveles: <a href="https://hubeau.eaufrance.fr/page/api-piezometrie">Hub'Eau, API Piézométrie</a> (banco
  <a href="https://ades.eaufrance.fr/">ADES</a>, BRGM y productores), Licence Ouverte 2.0. Restricciones:
  <a href="https://vigieau.gouv.fr/">VigiEau</a>, Ministerio de la Transición Ecológica, Licence Ouverte 2.0.
  Contornos de departamento: IGN Admin Express vía
  <a href="https://github.com/gregoiredavid/france-geojson">france-geojson</a>, Licence Ouverte.
  Datos leídos el {now:%d/%m/%Y a las %H:%M} (hora de París).</p>
  <p>Código en <a href="{REPO}">GitHub</a> (MIT); datos propios CC BY 4.0.</p>
  <nav aria-label="Proyectos hermanos"><ul class="siblings">
{siblings}
  </ul></nav>
</footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
const CLS = {classes_js};
const RESTR = {json.dumps(restrictions)};
const MONTHS = {json.dumps(MONTHS)};
const fmt = (x, d = 2) => x == null ? '—' : x.toLocaleString('es-ES', {{minimumFractionDigits: d, maximumFractionDigits: d}});
// Metres for people: against the usual level of the month, and below the measuring point.
const vsNormal = a => a == null ? '' : Math.abs(a) < .005 ? 'en su nivel habitual'
  : fmt(Math.abs(a)) + ' m ' + (a < 0 ? 'por debajo' : 'por encima') + ' de lo habitual';
const below = d => d == null ? '' : d < 0 ? 'nivel ' + fmt(-d, 1) + ' m por encima del punto de medida'
  : 'nivel a ' + fmt(d, 1) + ' m bajo el punto de medida';
const monthName = m => MONTHS[+m.slice(5, 7) - 1] + ' de ' + m.slice(0, 4);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}})[c]);
const map = L.map('map', {{zoomSnap: .25, attributionControl: false}}).setView([46.6, 2.4], 5.5);
// Departments in their own pane under the points: the GeoJSON arrives after the points' canvas
// and would otherwise be drawn on top of it.
map.createPane('surf').style.zIndex = 300;
map.createPane('deps').style.zIndex = 350;
const geoReady = fetch('departements.geojson').then(r => r.json()).then(geo => {{
  const layer = L.geoJSON(geo, {{pane: 'deps', style: f => {{
    const r = RESTR[f.properties.code];
    return {{className: 'dep ' + (r == null || r < 0 ? 'rx' : 'r' + r), interactive: false}};
  }}}}).addTo(map);
  // A map drawn while its pane is hidden has no size, and fitting to it gives NaN.
  if (map.getSize().x > 0) map.fitBounds(layer.getBounds(), {{padding: [6, 6]}});
  return geo;
}});
const canvas = L.canvas({{padding: .5}});
const paper = getComputedStyle(document.body).getPropertyValue('--paper').trim() || '#fff';
const muted = getComputedStyle(document.body).getPropertyValue('--muted').trim() || '#888';
const dots = L.layerGroup();
const classOf = p => Object.keys(CLS).find(k => p < .5 ? p <= CLS[k].upper : p < CLS[k].upper) || 'very_high';
const pointsReady = fetch('puntos.json').then(r => r.json()).then(points => {{
  points.sort((a, b) => (a[3] ? 1 : 0) - (b[3] ? 1 : 0));
  for (const [id, lat, lon, cls, commune, record, , anomaly, depth] of points) {{
    const c = CLS[cls];
    L.circleMarker([lat, lon], {{renderer: canvas, radius: c ? 4 : 2.6, weight: c ? 1 : 1.2,
      color: c ? paper : muted, fillColor: c ? c.color : paper, fillOpacity: 1}})
      .bindTooltip(esc(commune) + ' · ' + (c ? c.label + (record === 'low' ? ' (mínimo de la serie)' : '') : 'sin clase')
        + [vsNormal(anomaly), below(depth)].filter(Boolean).map(t => '<br>' + t).join(''))
      .on('click', () => openPoint(id)).addTo(dots);
  }}
  return points;
}});

// Interpolated surface, drawn once into an image over metropolitan France. Each pixel takes the
// inverse-distance weighted probability of the classified piezometers within {SURFACE_MAX_KM} km,
// coloured by its class and faded with the distance to the nearest one, then clipped to the
// department outlines. Rows are spaced in Web Mercator so the image lines up with the map.
const SURF = {{full: {SURFACE_FULL_KM}, max: {SURFACE_MAX_KM}, west: -5.3, east: 9.7, south: 41.2, north: 51.2, width: 900}};
const SMOOTH = 25;  // km², softens the bull's-eye IDW draws around each well
const merc = lat => Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360));
function surface(points, geo) {{
  const {{full, max, west, east, south, north, width}} = SURF;
  const top = merc(north), bottom = merc(south);
  const height = Math.round(width * (top - bottom) / ((east - west) * Math.PI / 180));
  const cell = .5, grid = new Map();
  for (const [, lat, lon, , , , p] of points) {{
    if (p == null) continue;
    const k = Math.floor(lat / cell) + ',' + Math.floor(lon / cell);
    if (!grid.has(k)) grid.set(k, []);
    grid.get(k).push([lat, lon, p]);
  }}
  const rgb = Object.fromEntries(Object.entries(CLS).map(([k, c]) =>
    [k, [1, 3, 5].map(i => parseInt(c.color.slice(i, i + 2), 16))]));
  const off = document.createElement('canvas');
  off.width = width; off.height = height;
  const ctx = off.getContext('2d'), img = ctx.createImageData(width, height);
  for (let y = 0; y < height; y++) {{
    const lat = (2 * Math.atan(Math.exp(top - (y + .5) / height * (top - bottom))) - Math.PI / 2) * 180 / Math.PI;
    const kx = 111.32 * Math.cos(lat * Math.PI / 180), ky = 110.57, gy = Math.floor(lat / cell);
    for (let x = 0; x < width; x++) {{
      const lon = west + (x + .5) / width * (east - west), gx = Math.floor(lon / cell);
      let sw = 0, sp = 0, near = Infinity;
      for (let a = gy - 1; a <= gy + 1; a++) for (let b = gx - 1; b <= gx + 1; b++) {{
        for (const [plat, plon, p] of grid.get(a + ',' + b) || []) {{
          const d = Math.hypot((lon - plon) * kx, (lat - plat) * ky);
          if (d > max) continue;
          const w = 1 / (d * d + SMOOTH);
          sw += w; sp += w * p; near = Math.min(near, d);
        }}
      }}
      if (!sw) continue;
      const c = rgb[classOf(sp / sw)], o = (y * width + x) * 4;
      img.data[o] = c[0]; img.data[o + 1] = c[1]; img.data[o + 2] = c[2];
      img.data[o + 3] = 230 * (near <= full ? 1 : (max - near) / (max - full));
    }}
  }}
  ctx.putImageData(img, 0, 0);
  const out = document.createElement('canvas');
  out.width = width; out.height = height;
  const o = out.getContext('2d');
  const ring = r => r.forEach(([lon, lat], i) => {{
    const px = (lon - west) / (east - west) * width, py = (top - merc(lat)) / (top - bottom) * height;
    i ? o.lineTo(px, py) : o.moveTo(px, py);
  }});
  o.beginPath();
  for (const f of geo.features) {{
    const g = f.geometry;
    (g.type === 'Polygon' ? [g.coordinates] : g.coordinates).forEach(poly => poly.forEach(ring));
  }}
  o.clip('evenodd');
  o.drawImage(off, 0, 0);
  return L.imageOverlay(out.toDataURL(), [[south, west], [north, east]], {{pane: 'surf', interactive: false}});
}}
const NOTES = {{
  surf: 'Color de los piezómetros clasificados a menos de {SURFACE_MAX_KM} km, más pálido cuanto más lejos; sin color, ' +
        'sin piezómetro cerca. Acerca el mapa para ver los puntos y pulsa uno para ver su curva.',
  pts: 'Pulsa un punto para ver su curva. Los puntos huecos no tienen clase este mes (ver «Cómo se calcula»).'}};
let surf = null;
const view = () => document.querySelector('input[name=view]:checked').value;
const showDots = () => view() === 'pts' || map.getZoom() >= 8 ? dots.addTo(map) : dots.remove();
function setView() {{
  const v = view();
  document.getElementById('map').classList.toggle('surf', v === 'surf');
  document.getElementById('restr-legend').hidden = v !== 'pts';
  document.getElementById('map-note').textContent = NOTES[v];
  if (surf) v === 'surf' ? surf.addTo(map) : surf.remove();
  showDots();
}}
document.querySelectorAll('input[name=view]').forEach(i => i.addEventListener('change', setView));
map.on('zoomend', showDots);
setView();
Promise.all([pointsReady, geoReady]).then(([points, geo]) => {{ surf = surface(points, geo); setView(); }});
document.getElementById('restr').addEventListener('change', e =>
  document.getElementById('map').classList.toggle('hide-restr', !e.target.checked));

function metresLine(d) {{
  const n = d.now, m = MONTHS[+n.month.slice(5, 7) - 1];
  if (n.value == null) return '';
  const parts = ['Nivel medio: ' + fmt(n.value) + ' m sobre el nivel del mar'];
  if (n.anomaly != null) parts.push(vsNormal(n.anomaly) + ' para un mes de ' + m + ' (la mediana de los demás años)');
  if (n.depth != null) parts.push(below(n.depth) + (n.depth < 0
    ? ' (pozo surgente de un acuífero cautivo, o altitud mal anotada)' : ''));
  return '<p>' + parts.join('; ') + '.</p>';
}}

async function openPoint(id) {{
  const box = document.getElementById('ficha');
  const d = await fetch('p/' + id + '.json').then(r => r.ok ? r.json() : null);
  if (!d) return;
  history.replaceState(null, '', '#' + id);
  const n = d.now;
  const state = n.status === 'ok'
    ? `<b>${{CLS[n.cls].label}}</b>${{n.record === 'low' ? ', el más bajo de la serie' : n.record === 'high' ? ', el más alto de la serie' : ''}}: probabilidad ${{fmt(n.p, 2)}} entre ${{n.years}} años`
    : {{no_data: 'Sin medida en el mes', incomplete: `Mes incompleto (${{n.days}} días con medida)`,
       short_record: `Solo ${{n.years}} años de referencia (hacen falta {MIN_REFERENCE_YEARS})`}}[n.status];
  box.innerHTML = `<h3>${{esc(d.commune || d.code)}} <span class="note">(${{esc(d.department_name)}})</span></h3>
    <p>${{monthName(n.month)}}: ${{state}}.</p>
    ${{metresLine(d)}}
    ${{chart(d)}}
    <p class="note">Línea: media mensual. Banda: del percentil 10 al 90 de cada mes hasta ${{d.band_until}};
    discontinua, la mediana; punteadas, el mínimo y el máximo. Pasa el ratón por un mes para ver su valor.</p>
    <dl><dt>Código BSS</dt><dd><a href="${{esc(d.ades)}}">${{esc(d.code)}}</a></dd>
    <dt>Masa de agua</dt><dd>${{esc(d.water_body || '—')}}</dd>
    <dt>Acuífero</dt><dd>${{esc(d.aquifer || '—')}}</dd>
    <dt>Altitud</dt><dd>${{d.altitude ? fmt(+d.altitude) + ' m' : '—'}}</dd>
    <dt>Mide desde</dt><dd>${{esc(d.first || '—')}}</dd></dl>`;
  box.hidden = false;
  box.scrollIntoView({{behavior: 'smooth', block: 'nearest'}});
}}

function chart(d) {{
  const W = 820, H = 260, L0 = 56, R = 12, T = 12, B = 28;
  const ms = d.months, band = m => d.band[+m.slice(5, 7)];
  const vals = ms.flatMap(([m, v]) => [v, band(m)?.min, band(m)?.max]).filter(v => v != null);
  if (!vals.length) return '<p class="note">Sin datos para dibujar.</p>';
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * .06 || .5; lo -= pad; hi += pad;
  const x = i => L0 + i * (W - L0 - R) / (ms.length - 1), y = v => T + (hi - v) * (H - T - B) / (hi - lo);
  const path = (key) => {{
    let s = '', on = false;
    ms.forEach(([m], i) => {{ const b = band(m); const v = b ? b[key] : null;
      if (v == null) {{ on = false; return; }} s += (on ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1); on = true; }});
    return s;
  }};
  let area = '';
  const idx = ms.map((m, i) => i).filter(i => band(ms[i][0]));
  if (idx.length) area = 'M' + idx.map(i => x(i).toFixed(1) + ' ' + y(band(ms[i][0]).p90).toFixed(1)).join('L')
    + 'L' + idx.slice().reverse().map(i => x(i).toFixed(1) + ' ' + y(band(ms[i][0]).p10).toFixed(1)).join('L') + 'Z';
  let line = '', on = false;
  ms.forEach(([m, v], i) => {{ if (v == null) {{ on = false; return; }} line += (on ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1); on = true; }});
  const ticks = [0, 1, 2, 3].map(k => lo + pad + k * (hi - lo - 2 * pad) / 3);
  const yAxis = ticks.map(t => `<line class="axis" x1="${{L0}}" x2="${{W - R}}" y1="${{y(t)}}" y2="${{y(t)}}"/><text x="${{L0 - 6}}" y="${{y(t) + 4}}" text-anchor="end">${{fmt(t, 1)}}</text>`).join('');
  const xAxis = ms.map(([m], i) => m.endsWith('-01') ? `<text x="${{x(i)}}" y="${{H - 8}}" text-anchor="middle">${{m.slice(0, 4)}}</text>` : '').join('');
  const last = ms[ms.length - 1];
  const dot = last[1] != null ? `<circle cx="${{x(ms.length - 1)}}" cy="${{y(last[1])}}" r="5" fill="${{last[2] ? CLS[last[2]].color : muted}}"/>` : '';
  const w = (W - L0 - R) / (ms.length - 1);
  const hits = ms.map(([m, v, c], i) => `<rect class="hit" x="${{x(i) - w / 2}}" y="${{T}}" width="${{w}}" height="${{H - T - B}}"><title>${{monthName(m)}}: ${{v == null ? 'sin dato' : fmt(v) + ' m NGF' + (c ? ' · ' + CLS[c].label : '')}}</title></rect>`).join('');
  return `<svg class="chart" viewBox="0 0 ${{W}} ${{H}}" role="img" aria-label="Nivel mensual de los últimos ${{ms.length}} meses frente a su banda histórica">
    ${{yAxis}}<text x="4" y="${{T + 4}}">m NGF</text>
    <path class="band" d="${{area}}"/><path class="ext" d="${{path('min')}}"/><path class="ext" d="${{path('max')}}"/>
    <path class="med" d="${{path('p50')}}"/><path class="line" d="${{line}}"/>${{dot}}${{xAxis}}${{hits}}</svg>`;
}}

document.querySelectorAll('[data-open]').forEach(a => a.addEventListener('click', e => {{ e.preventDefault(); openPoint(a.dataset.open); }}));
if (location.hash.startsWith('#BSS')) openPoint(location.hash.slice(1));
document.querySelectorAll('.tools button').forEach(b => b.addEventListener('click', () => {{
  b.parentElement.querySelectorAll('button').forEach(o => o.setAttribute('aria-pressed', o === b));
  document.querySelectorAll('#deps tbody tr').forEach(tr => tr.hidden = b.dataset.flag === 'any' && !tr.dataset.flag);
}}));
</script>
</body>
</html>
"""
    out = DOCS_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
