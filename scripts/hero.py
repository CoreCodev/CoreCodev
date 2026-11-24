"""hero.py - Banner pixel-art (escritorio + gato) con tarjeta de stats, en un solo SVG."""
from datetime import datetime, timedelta, timezone

P = 5  # tamaño de cada "pixel" de la escena

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# (x, y, w, h, color) en unidades de pixel
SCENE = [
    (0, 0, 112, 60, "#150f2e"),                       # pared
    (0, 52, 112, 8, "#0d0a1f"),                       # suelo
    # ventana con ciudad nocturna
    (30, 5, 24, 24, "#2a2250"), (31, 6, 22, 22, "#1b1f4b"),
    (42, 5, 1, 24, "#2a2250"), (30, 16, 24, 1, "#2a2250"),
    (35, 8, 2, 2, "#f4e9a8"),                          # luna
    (32, 20, 4, 8, "#0e1030"), (37, 17, 5, 11, "#0e1030"), (44, 14, 4, 14, "#0e1030"), (49, 19, 4, 9, "#0e1030"),
    (38, 19, 1, 1, "#ffd36b"), (39, 22, 1, 1, "#00f0ff"), (45, 17, 1, 1, "#ffd36b"), (46, 21, 1, 1, "#ff4fb8"),
    (50, 22, 1, 1, "#00f0ff"), (33, 23, 1, 1, "#ffd36b"),
    # ventana 2
    (58, 5, 14, 24, "#2a2250"), (59, 6, 12, 22, "#1b1f4b"),
    (60, 22, 4, 6, "#0e1030"), (65, 18, 5, 10, "#0e1030"), (66, 20, 1, 1, "#ffd36b"), (61, 24, 1, 1, "#ff4fb8"),
    # estante con libros
    (3, 14, 22, 1, "#8a4b1f"),
    (4, 8, 2, 6, "#ff4fb8"), (6, 9, 2, 5, "#00f0ff"), (8, 7, 2, 7, "#ffb347"), (10, 9, 2, 5, "#7c5cff"),
    (16, 11, 4, 3, "#3b2a5e"), (17, 8, 2, 3, "#3ddc84"), (16, 10, 4, 1, "#3ddc84"), (20, 12, 3, 2, "#c4623a"),
    # segundo estante
    (3, 26, 22, 1, "#8a4b1f"), (5, 22, 3, 4, "#2a2250"), (6, 23, 1, 2, "#00f0ff"), (12, 21, 5, 5, "#2a2250"), (13, 22, 3, 3, "#ffb347"),
    # reloj neón
    (84, 8, 20, 9, "#0b0820"), (84, 8, 20, 1, "#ff4fb8"), (84, 16, 20, 1, "#ff4fb8"), (83, 9, 1, 7, "#ff4fb8"), (104, 9, 1, 7, "#ff4fb8"),
    (84, 4, 20, 1, "#ff4fb8"),
    # escritorio
    (22, 46, 76, 3, "#b5651d"), (22, 49, 76, 11, "#7a3e12"), (26, 51, 14, 7, "#5e2e0c"), (80, 51, 14, 7, "#5e2e0c"),
    # monitor
    (28, 24, 38, 22, "#0b0820"), (29, 25, 36, 19, "#102a4c"),
    (32, 27, 10, 1, "#ff4fb8"), (34, 29, 14, 1, "#00f0ff"), (34, 31, 8, 1, "#ffd36b"), (36, 33, 16, 1, "#3ddc84"),
    (32, 35, 6, 1, "#7c5cff"), (34, 37, 12, 1, "#00f0ff"), (32, 39, 9, 1, "#ff4fb8"), (50, 28, 10, 1, "#7c5cff"), (50, 31, 7, 1, "#ffd36b"),
    (45, 44, 4, 2, "#1a1a2e"),
    # persona de espaldas
    (38, 31, 12, 12, "#2a1a1a"), (39, 30, 10, 2, "#2a1a1a"),            # pelo
    (36, 43, 16, 17, "#5a5fc0"), (34, 46, 3, 8, "#4a4fa8"), (51, 46, 3, 8, "#4a4fa8"),
    (32, 56, 24, 4, "#1a1a2e"),                                         # respaldo
    # teclado + ratón
    (34, 45, 14, 1, "#2a2250"), (52, 45, 3, 1, "#2a2250"),
    # gato naranja
    (72, 38, 11, 8, "#f28c28"), (72, 35, 3, 3, "#f28c28"), (80, 35, 3, 3, "#f28c28"), (73, 36, 1, 1, "#ff9ec4"),
    (74, 40, 1, 1, "#150f2e"), (79, 40, 1, 1, "#150f2e"), (76, 42, 2, 1, "#ff9ec4"),
    (72, 43, 11, 1, "#ffd9a8"), (83, 42, 4, 1, "#f28c28"), (86, 39, 1, 4, "#f28c28"),
    # planta
    (94, 40, 7, 6, "#c4623a"), (95, 39, 5, 1, "#8a3f1d"),
    (96, 30, 3, 9, "#2fa84f"), (93, 33, 3, 5, "#3ddc84"), (99, 32, 3, 6, "#3ddc84"), (95, 28, 2, 3, "#3ddc84"),
]


def _scene() -> str:
    rects = "".join(
        f'<rect x="{x*P}" y="{y*P}" width="{w*P}" height="{h*P}" fill="{c}"/>' for x, y, w, h, c in SCENE
    )
    return f'<g shape-rendering="crispEdges">{rects}</g>'


def _heatmap(days: list, x0: int, y0: int, cols: int = 15, rows: int = 4) -> str:
    """Mini calendario con las últimas cols*rows jornadas (más reciente al final)."""
    last = days[-cols * rows:]
    out = []
    for i, d in enumerate(last):
        n = d.get("contributionCount", 0)
        color = "#1b2a2f" if n == 0 else "#0e8f5a" if n < 3 else "#1fd37c" if n < 6 else "#7dffb8"
        out.append(f'<rect x="{x0 + (i % cols) * 14}" y="{y0 + (i // cols) * 14}" width="11" height="11" rx="2" fill="{color}"/>')
    return "".join(out)


def _stat(icon: str, x: int, y: int, value, label: str, color: str) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="15">{icon}</text>'
        f'<text x="{x+28}" y="{y}" fill="#e8e6ff" font-size="15" font-weight="700">{value:,}</text>'
        f'<text x="{x+28+len(f"{value:,}")*9+8}" y="{y}" fill="#8f8bb8" font-size="12">{label}</text>'
    )


def render_hero_svg(profile: dict, stats: dict, languages: list, colors: dict) -> str:
    top_lang = (languages[0]["name"] if languages else "Dev")[:2].upper()
    lima = (datetime.now(timezone.utc) - timedelta(hours=5)).strftime("%H:%M")
    days = stats.get("contribution_days", [])
    contributions = sum(d.get("contributionCount", 0) for d in days)

    # tarjeta: x 580..880
    cx = 580
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300" viewBox="0 0 900 300" font-family="{FONT}" role="img" aria-label="Perfil de {profile["name"]}">
  <defs>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="900" height="300" rx="16" fill="#0a0a0f"/>
  <rect x="0.5" y="0.5" width="899" height="299" rx="16" fill="none" stroke="{colors["primary"]}" stroke-opacity="0.35"/>
  <clipPath id="sc"><rect x="12" y="12" width="560" height="276" rx="12"/></clipPath>
  <g clip-path="url(#sc)" transform="translate(12 -0)">{_scene()}</g>
  <text x="{(84+10)*P+12}" y="{13*P+3}" fill="#ff4fb8" font-size="17" font-weight="700" text-anchor="middle" filter="url(#glow)">{lima}</text>

  <rect x="{cx}" y="12" width="308" height="276" rx="12" fill="#12121a" stroke="#1e1e2e"/>
  <text x="{cx+20}" y="52" fill="#ffffff" font-size="19" font-weight="700">SEBASTIAN RABANAL</text>
  <rect x="{cx+248}" y="30" width="40" height="28" rx="6" fill="{colors["primary"]}" fill-opacity="0.18" stroke="{colors["primary"]}"/>
  <text x="{cx+268}" y="49" fill="{colors["primary"]}" font-size="13" font-weight="700" text-anchor="middle">{top_lang}</text>
  <text x="{cx+20}" y="74" fill="#8f8bb8" font-size="12">Ing. de Sistemas · UNAC</text>
  {_stat("★", cx+20, 112, stats.get("total_stars", 0), "stars", "#ffd36b")}
  {_stat("◆", cx+20, 142, contributions, "contributions", "#7dffb8")}
  {_stat("▣", cx+20, 172, stats.get("total_repos", 0), "repositories", colors["primary"])}
  {_stat("●", cx+20, 202, stats.get("followers", 0), "followers", "#ff4fb8")}
  {_heatmap(days, cx+20, 222)}
</svg>'''
