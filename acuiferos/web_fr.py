"""The French page, docs/fr/index.html: the figures, the departments, the lowest piezometers and the
method. The interactive map and each piezometer's curve stay on the Spanish page, which it links."""
from __future__ import annotations

from datetime import datetime
from html import escape

from .config import (COMPLETE_SHARE, DISCORDANT_LOW_SHARE, DOCS_DIR, MIN_DEPARTMENT_POINTS, MIN_REFERENCE_YEARS,
                     NORMAL_P, REFRESH_MONTHS, SURFACE_FULL_KM, SURFACE_MAX_KM)
from .footer import footer_nav
from .ips import CLASSES, class_of
from .logo import LOGO_SVG, favicon_link
from .report import Department, Report
from .web import ACCENT, ACCENT_DARK, COMMON_CSS, CSS, LOWEST_ROWS, REPO, _cls_range

MONTHS = ("janvier février mars avril mai juin juillet août septembre octobre novembre décembre").split()
# The BRGM bulletin's own wording for the seven classes.
LABELS = {"very_low": "Très bas", "low": "Bas", "mod_low": "Modérément bas", "normal": "Autour de la normale",
          "mod_high": "Modérément haut", "high": "Haut", "very_high": "Très haut"}
RESTRICTIONS = {"": "Pas de restriction", "vigilance": "Vigilance", "alerte": "Alerte",
                "alerte_renforcee": "Alerte renforcée", "crise": "Crise"}
FLAGS = {"low_unrestricted": "Niveaux bas sans restriction",
         "restricted_normal": "Restriction forte avec niveaux normaux"}


def _n(x: int) -> str:
    return f"{x:,}".replace(",", " ")


def _dec(x: float, d: int = 2) -> str:
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def _pct(x: float) -> str:
    return f"{round(100 * x)} %"


def month_name(m: str) -> str:
    return f"{MONTHS[int(m[5:7]) - 1]} {m[:4]}"


def _dept_row(d: Department) -> str:
    n = len(d.classified)
    restr = "—" if d.restriction is None else RESTRICTIONS[d.restriction]
    if n:
        low = f'{_n(d.low)} <span class="sub">{_pct(d.low_share)}</span>'
        med = LABELS[class_of(d.median_p)]
    else:
        low, med = "—", "—"
    flag = f'<span class="flag">{FLAGS[d.flag]}</span>' if d.flag else ""
    return (f'<tr data-flag="{d.flag}"><td>{escape(d.name)} <span class="sub">{escape(d.code)}</span></td>'
            f'<td>{escape(restr)}</td><td class="num">{_n(n)} <span class="sub">sur {_n(len(d.points))}</span></td>'
            f'<td class="num">{low}</td><td>{med}</td><td>{flag}</td></tr>')


def _lowest_rows(rep: Report) -> tuple[str, int]:
    low = sorted((p for p in rep.classified if p.now.cls == "very_low"), key=lambda p: (p.now.p, p.station["bss_id"]))
    rows = []
    for p in low[:LOWEST_ROWS]:
        s, r = p.station, p.now
        rec = " · minimum de la série" if r.record == "low" else ""
        rows.append(
            f'<tr><td><a href="../#{escape(s["bss_id"])}">{escape(s["commune"] or s["code_bss"])}</a>'
            f'<span class="sub">{escape(s["code_bss"])}</span></td>'
            f'<td>{escape(s["department_name"])}</td><td>{escape(s["water_body_name"] or "—")}</td>'
            f'<td class="num">{_dec(r.value)}</td><td class="num">{_n(r.years)}</td>'
            f'<td>{LABELS[r.cls]}{rec}</td></tr>')
    return "\n".join(rows), len(low)


def method_html(rep: Report) -> str:
    statuses = {k: sum(p.now.status == k for p in rep.points) for k in ("ok", "no_data", "incomplete", "short_record")}
    classes = "\n".join(
        f'<tr><td>{LABELS[key]}</td><td class="num">{_cls_range(i)}</td>'
        f'<td class="num">{_n(sum(p.now.cls == key for p in rep.classified))}</td></tr>'
        for i, (_, key, _label) in enumerate(CLASSES))
    month = MONTHS[int(rep.month[5:]) - 1]
    return f"""<section class="method" id="methode">
  <h2>Comment c'est calculé</h2>
  <ol>
    <li><b>Piézomètres.</b> Un piézomètre est un puits d'observation où l'on mesure le niveau de l'eau
    souterraine (la nappe). Hub'Eau publie le réseau de suivi des eaux souterraines de France (banque ADES, BRGM,
    le service géologique national). On suit les {_n(len(rep.points))} piézomètres ayant au moins une mesure
    dans les 45 derniers jours ; celui qui cesse de mesurer garde sa série et apparaît sans donnée.</li>
    <li><b>Mesures.</b> On télécharge le niveau journalier, en mètres au-dessus du niveau de la mer (NGF), de toute
    la série. On écarte les mesures que le producteur qualifie d'incorrectes et celles prises pendant un pompage ou
    influencées par un pompage proche (nature « dynamique » ou « influencée »). Plusieurs mesures d'un même jour
    comptent pour leur moyenne.</li>
    <li><b>Mois.</b> Le niveau d'un mois est la moyenne de ses jours mesurés. Le mois évalué est le dernier mois
    complet, {month_name(rep.month)}. Il ne compte que s'il a au moins {_pct(COMPLETE_SHARE)} des mesures que ce
    puits a d'habitude en un mois (la médiane des 24 mois précédents).</li>
    <li><b>Comparaison avec sa propre histoire.</b> Le niveau de {month} est classé parmi les mois de {month} de
    toutes les autres années de ce piézomètre ; il en faut au moins {MIN_REFERENCE_YEARS}. Le rang donne la
    probabilité empirique d'un niveau plus bas, rang / (n + 1), et cette probabilité donne la classe, avec les
    seuils du bulletin du BRGM. C'est l'idée de l'indicateur piézométrique standardisé (IPS) du BRGM, sans ajuster
    de loi. Un niveau plus bas que toutes les autres années est un « minimum de la série ».</li>
    <li><b>Carte interpolée</b> (page en espagnol). Chaque point de la carte prend la moyenne des probabilités des
    piézomètres classés à moins de {SURFACE_MAX_KM} km, pondérée par l'inverse du carré de la distance. La couleur
    est pleine jusqu'à {SURFACE_FULL_KM} km du piézomètre le plus proche et s'estompe jusqu'à {SURFACE_MAX_KM} km.</li>
    <li><b>Départements.</b> Dans chaque département on compte les piézomètres classés et ceux qui sont « bas » ou
    « très bas ». On les compare au niveau de restriction sécheresse en vigueur pour les eaux souterraines selon
    VigiEau (le plus élevé des zones du département), lu chaque jour.</li>
    <li><b>Indices.</b> Avec au moins {MIN_DEPARTMENT_POINTS} piézomètres classés, on signale « niveaux bas sans
    restriction » si {_pct(DISCORDANT_LOW_SHARE)} ou plus sont bas ou très bas et qu'il n'y a pas de restriction
    sur les eaux souterraines au-delà de la vigilance ; et « restriction forte avec niveaux normaux » en alerte
    renforcée ou en crise quand la médiane des piézomètres est autour de la normale ou plus haute (probabilité
    au-dessus de {_dec(NORMAL_P)}). Ce sont des indices à regarder, pas des verdicts : le préfet décide avec plus
    de données (débits, usages, arrêté-cadre).</li>
    <li><b>Signaux.</b> <a href="../signals.json">signals.json</a> liste chaque piézomètre « bas » ou « très bas »,
    avec sa commune (code INSEE), la date de sa dernière mesure et les mètres par rapport à l'habituel du mois, dans
    le format commun des projets frères (<a href="https://github.com/Asensio94/estado-iba/blob/main/CONTRATO.md">CONTRATO.md</a>
    d'État des IBA, type <code>groundwater_level</code>). Ce sont les mêmes classes que sur cette page : pas d'autre seuil.</li>
  </ol>
  <h3>Classes</h3>
  <table class="params"><thead><tr><th>Classe</th><th class="num">Probabilité</th><th class="num">Piézomètres en {month_name(rep.month)}</th></tr></thead>
  <tbody>
{classes}
  </tbody></table>
  <h3>Piézomètres sans classe</h3>
  <table class="params"><tbody>
    <tr><th>Classés</th><td class="num">{_n(statuses['ok'])}</td></tr>
    <tr><th>Sans mesure dans le mois</th><td class="num">{_n(statuses['no_data'])}</td></tr>
    <tr><th>Mois incomplet</th><td class="num">{_n(statuses['incomplete'])}</td></tr>
    <tr><th>Moins de {MIN_REFERENCE_YEARS} ans de référence</th><td class="num">{_n(statuses['short_record'])}</td></tr>
  </tbody></table>
  <h3>Validation</h3>
  <p>Comparé au bulletin de situation hydrogéologique du BRGM du 1<sup>er</sup> octobre 2026 (septembre 2026), tel
  que l'a cité la presse spécialisée :</p>
  <table class="params"><thead><tr><th>Septembre 2026</th><th class="num">Ici</th><th class="num">BRGM</th></tr></thead><tbody>
    <tr><td>Sous la normale (probabilité 0,40 ou moins)</td><td class="num">64,3 %</td><td class="num">66 %</td></tr>
    <tr><td>La même chose un an plus tôt (mêmes piézomètres)</td><td class="num">30,7 %</td><td class="num">31 %</td></tr>
    <tr><td>Niveau en baisse par rapport à août</td><td class="num">75,4 %</td><td class="num">81 %</td></tr>
  </tbody></table>
  <p>Le BRGM utilise une sélection de points de référence et ajuste une loi à chaque mois ; ici entrent tous les
  piézomètres ayant 15 ans de référence et on utilise le rang des valeurs, sans ajustement. La baisse est mesurée
  ici entre moyennes mensuelles, et par le BRGM sur la fin du mois.</p>
  <h3>Limites</h3>
  <ul>
    <li>Les mesures des derniers mois sont brutes : le producteur peut les corriger en les validant. Les
    {REFRESH_MONTHS} derniers mois sont relus chaque jour.</li>
    <li>VigiEau donne le niveau le plus élevé des zones d'alerte du département, qui ne coïncident pas avec les
    nappes ; un département peut avoir une zone en crise et le reste sans restriction.</li>
    <li>La restriction est celle du jour et le niveau celui du dernier mois complet.</li>
    <li>Les nappes lentes (la craie du bassin parisien) et rapides (les karsts) ne réagissent pas de la même façon
    à la pluie ; la classe dit comment chacune est par rapport à elle-même, pas laquelle va le plus mal.</li>
    <li>Une série en baisse depuis longtemps (une nappe qui descend d'année en année à cause des prélèvements)
    reste « très bas » mois après mois : la classe compare avec toutes les années de la série.</li>
    <li>Les départements d'outre-mer sont dans le tableau mais pas sur la carte.</li>
  </ul>
</section>"""


def render_fr(rep: Report, now: datetime) -> None:
    classified = rep.classified
    n_low = sum(p.now.cls in ("very_low", "low") for p in classified)
    records = sum(p.now.record == "low" for p in classified)
    flagged = [d for d in rep.departments if d.flag]
    yoy = rep.low_share_vs_year_ago()
    yoy_txt = (f"<small>il y a un an, {_pct(yoy[1])} (sur les {_n(yoy[2])} classés alors et aujourd'hui)</small>"
               if yoy else "")
    lowest, n_very_low = _lowest_rows(rep)
    month = MONTHS[int(rep.month[5:]) - 1]
    more = f" ; voici les {LOWEST_ROWS} dont la probabilité est la plus basse" if n_very_low > LOWEST_ROWS else ""

    html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nappes de France</title>
<meta name="description" content="Le niveau des eaux souterraines de France face à sa propre histoire, et face aux restrictions sécheresse en vigueur.">
<link rel="alternate" hreflang="es" href="../">
{favicon_link(ACCENT, ACCENT_DARK)}
<style>
{COMMON_CSS}
{CSS}
</style>
</head>
<body>
<header class="site-header">
  <h1>{LOGO_SVG}Nappes de <span>France</span></h1>
  <p class="lede">Chaque piézomètre de France (un puits d'observation où l'on mesure le niveau de l'eau souterraine)
  comparé à lui-même : le niveau de {month_name(rep.month)} est-il bas ou haut par rapport au même mois des autres
  années, et son département a-t-il des restrictions sécheresse sur les eaux souterraines ? Données Hub'Eau (BRGM)
  et VigiEau.</p>
  <p class="lang" lang="es"><a href="../" hreflang="es">Versión en español</a></p>
  <div class="figures">
    <div><b>{_n(len(classified))}</b><span>piézomètres classés</span><small>sur {_n(len(rep.points))} actifs</small></div>
    <div><b>{_pct(n_low / len(classified)) if classified else "—"}</b><span>bas ou très bas en {month}</span>{yoy_txt}</div>
    <div><b>{_n(records)}</b><span>au minimum de leur série</span><small>pour un mois de {month}</small></div>
    <div><b>{_n(len(flagged))}</b><span>départements avec indice</span><small>niveaux et restriction ne concordent pas</small></div>
  </div>
</header>
<main>
  <p class="note">La carte interactive (niveau interpolé, piézomètres et restrictions) et la fiche de chaque
  piézomètre avec sa courbe sont pour l'instant sur la <a href="../">page en espagnol</a>.</p>
  <h2>Départements</h2>
  <div class="wrap"><table class="t" id="deps">
    <thead><tr><th>Département</th><th>Restriction eaux souterraines</th><th class="num">Classés</th>
    <th class="num">Bas ou très bas</th><th>Médiane</th><th>Indice</th></tr></thead>
    <tbody>
{chr(10).join(_dept_row(d) for d in rep.departments if d.points)}
    </tbody>
  </table></div>

  <h2>Les plus bas de {month_name(rep.month)}</h2>
  <p class="note">{_n(n_very_low)} piézomètres « très bas »{more}. Chaque nom ouvre sa courbe sur la page en espagnol.</p>
  <div class="wrap"><table class="t">
    <thead><tr><th>Piézomètre</th><th>Département</th><th>Masse d'eau</th><th class="num">Niveau<br><abbr title="mètres au-dessus du niveau de la mer (nivellement général de la France)">m NGF</abbr></th>
    <th class="num">Années de<br>référence</th><th>Classe</th></tr></thead>
    <tbody>
{lowest}
    </tbody>
  </table></div>
</main>
{method_html(rep)}
<footer class="site-footer">
  <p class="principle">Données publiques, règles visibles et chaque chiffre relié à sa source. Des indices, pas des verdicts.</p>
  <p>Niveaux : <a href="https://hubeau.eaufrance.fr/page/api-piezometrie">Hub'Eau, API Piézométrie</a> (banque
  <a href="https://ades.eaufrance.fr/">ADES</a>, BRGM et producteurs), Licence Ouverte 2.0. Restrictions :
  <a href="https://vigieau.gouv.fr/">VigiEau</a>, ministère de la Transition écologique, Licence Ouverte 2.0.
  Contours des départements : IGN Admin Express via
  <a href="https://github.com/gregoiredavid/france-geojson">france-geojson</a>, Licence Ouverte.
  Données lues le {now:%d/%m/%Y à %H:%M} (heure de Paris).</p>
  <p>Code sur <a href="{REPO}">GitHub</a> (MIT) ; données propres CC BY 4.0.</p>
  {footer_nav("fr")}
</footer>
</body>
</html>
"""
    out = DOCS_DIR / "fr" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
