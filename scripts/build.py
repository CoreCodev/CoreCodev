#!/usr/bin/env python3
"""
build.py - Motor principal: consume GitHub API y genera SVGs dinámicos con temática cyberpunk.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from hero import render_hero_svg


def load_config() -> dict:
    """Carga la configuración del proyecto."""
    config_path = Path("data/config.json")
    with open(config_path) as f:
        return json.load(f)


def load_profile() -> dict:
    """Carga los datos del perfil."""
    profile_path = Path("data/profile.json")
    with open(profile_path) as f:
        return json.load(f)


def get_github_token() -> str:
    """Obtiene el token de GitHub desde variable de entorno."""
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ADVERTENCIA: No se encontró token GH_PAT. Usando API sin auth (limitado).")
    return token


def github_graphql(query: str, token: str = None, variables: dict = None) -> dict:
    """Ejecuta una query GraphQL contra la API de GitHub."""
    config = load_config()
    url = config["github"]["graphql_url"]
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "CoreCodev-README-Builder",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            if result.get("errors"):
                print(f"Error GraphQL: {result['errors']}")
            return result
    except urllib.error.HTTPError as e:
        print(f"Error GraphQL {e.code}: {e.read().decode()}")
        return {}


def fetch_github_stats(username: str, token: str = None) -> dict:
    """Obtiene estadísticas del usuario vía GraphQL."""
    query = """
    query($login: String!) {
      user(login: $login) {
        name
        avatarUrl
        bio
        location
        followers { totalCount }
        following { totalCount }
        repositories(first: 100, isFork: false, orderBy: {field: UPDATED_AT, direction: DESC}) {
          totalCount
          nodes {
            name
            stargazerCount
            forkCount
            primaryLanguage { name }
          }
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
      }
    }
    """
    data = github_graphql(query, token, {"login": username})
    if not data or "data" not in data:
        return {}
    user = data["data"].get("user", {})

    # Contar estrellas totales
    repos = user.get("repositories", {}).get("nodes", [])
    total_stars = sum(r.get("stargazerCount", 0) for r in repos)

    contrib = user.get("contributionsCollection", {})
    calendar = contrib.get("contributionCalendar", {})

    return {
        "name": user.get("name"),
        "avatar_url": user.get("avatarUrl"),
        "bio": user.get("bio"),
        "location": user.get("location"),
        "followers": user.get("followers", {}).get("totalCount", 0),
        "following": user.get("following", {}).get("totalCount", 0),
        "total_repos": user.get("repositories", {}).get("totalCount", 0),
        "total_stars": total_stars,
        "total_commits": contrib.get("totalCommitContributions", 0),
        "contribution_days": [
            day
            for week in calendar.get("weeks", [])
            for day in week.get("contributionDays", [])
        ],
    }


def fetch_languages(username: str, token: str = None) -> dict:
    """Obtiene lenguajes más usados del usuario."""
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(first: 100, isFork: false, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            languages(first: 10) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
      }
    }
    """
    data = github_graphql(query, token, {"login": username})
    if not data or "data" not in data:
        return {}

    lang_bytes = {}
    repos = data["data"]["user"]["repositories"]["nodes"]
    for repo in repos:
        for edge in repo.get("languages", {}).get("edges", []):
            name = edge["node"]["name"]
            lang_bytes[name] = lang_bytes.get(name, 0) + edge["size"]

    total = sum(lang_bytes.values())
    langs = []
    for name, size in sorted(lang_bytes.items(), key=lambda x: -x[1])[:10]:
        color = "#00f0ff"
        for repo in repos:
            for edge in repo.get("languages", {}).get("edges", []):
                if edge["node"]["name"] == name:
                    color = edge["node"].get("color", color)
                    break
        langs.append({
            "name": name,
            "percent": round(size / total * 100, 1),
            "color": color,
        })
    return langs


def render_languages_svg(languages: list, profile: dict) -> str:
    """Renderiza SVG dedicado a lenguajes con barras animadas."""
    config = load_config()
    c = config["theme"]["colors"]
    anim = config["animations"]

    bars = ""
    max_langs = min(len(languages), 12)
    bar_height = 32
    for i, lang in enumerate(languages[:max_langs]):
        y = 60 + i * (bar_height + 10)
        width = lang["percent"] * 4.5
        color = lang.get("color", c["primary"])
        name = lang["name"]
        pct = lang["percent"]

        bars += f'''
    <text x="20" y="{y+18}" fill="{c["text"]}" font-size="12" font-family="monospace">{name}</text>
    <rect x="180" y="{y}" width="450" height="{bar_height-8}" rx="4" fill="{c["border"]}"/>
    <rect x="180" y="{y}" width="0" height="{bar_height-8}" rx="4" fill="{color}" filter="url(#glow)">
      <animate attributeName="width" from="0" to="{width}" dur="{anim["bar_duration"]}s" begin="{i*0.15}s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.2 1"/>
    </rect>
    <text x="640" y="{y+18}" fill="{color}" font-size="11" font-family="monospace" text-anchor="end" opacity="0">
      {pct}%
      <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{anim["bar_duration"]+i*0.15}s" fill="freeze"/>
    </text>'''

    total_height = 80 + max_langs * (bar_height + 10) + 20
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="{total_height}" viewBox="0 0 700 {total_height}" font-family="JetBrains Mono, Fira Code, monospace">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c["background"]}"/>
      <stop offset="100%" stop-color="{c["surface"]}"/>
    </linearGradient>
  </defs>
  <rect width="700" height="{total_height}" fill="url(#bg)" rx="12"/>
  <text x="20" y="35" fill="{c["primary"]}" font-size="16" font-family="monospace" font-weight="bold">$ {profile["username"]}/stack</text>
  <line x1="20" y1="50" x2="680" y2="50" stroke="{c["border"]}" stroke-width="1"/>
  {bars}
  <text x="20" y="{total_height-10}" fill="{c["text_dim"]}" font-size="9" font-family="monospace">{len(languages)} languages tracked</text>
</svg>'''
    return svg


def render_activity_svg(stats: dict) -> str:
    """Renderiza SVG con heatmap de contribuciones."""
    config = load_config()
    c = config["theme"]["colors"]

    days = stats.get("contribution_days", [])
    if not days:
        # SVG placeholder
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="150" viewBox="0 0 700 150">
  <rect width="700" height="150" fill="{c["background"]}" rx="12"/>
  <text x="350" y="80" fill="{c["text_dim"]}" font-size="14" text-anchor="middle" font-family="monospace">Loading contribution data...</text>
</svg>'''

    # Construir heatmap
    cell_size = 12
    gap = 2
    cols = 53
    rows = 7

    rects = ""
    for i, day in enumerate(days):
        col = i // 7
        row = i % 7
        x = 40 + col * (cell_size + gap)
        y = 50 + row * (cell_size + gap)
        count = day.get("contributionCount", 0)
        opacity = min(0.2 + count * 0.15, 1.0)
        color = day.get("color", c["primary"])

        rects += f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="2" fill="{color}" opacity="{opacity}"/>'

    total_contributions = sum(d.get("contributionCount", 0) for d in days)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="180" viewBox="0 0 700 180" font-family="JetBrains Mono, Fira Code, monospace">
  <rect width="700" height="180" fill="{c["background"]}" rx="12"/>
  <text x="20" y="30" fill="{c["primary"]}" font-size="14" font-family="monospace" font-weight="bold">$ git log --oneline</text>
  <text x="680" y="30" fill="{c["text_dim"]}" font-size="10" text-anchor="end" font-family="monospace">{total_contributions} contributions</text>
  {rects}
  <text x="20" y="170" fill="{c["text_dim"]}" font-size="9" font-family="monospace">Last 52 weeks</text>
</svg>'''
    return svg


def main():
    print("🚀 CoreCodev README Builder")
    print("=" * 50)

    config = load_config()
    profile = load_profile()

    token = get_github_token()
    username = config["github"]["username"]

    print(f"\n📡 Fetching stats for @{username}...")
    stats = fetch_github_stats(username, token)
    print(f"   Commits: {stats.get('total_commits', 0):,}")
    print(f"   Repos: {stats.get('total_repos', 0)}")
    print(f"   Stars: {stats.get('total_stars', 0)}")
    print(f"   Followers: {stats.get('followers', 0)}")

    print(f"\n📊 Fetching languages...")
    languages = fetch_languages(username, token)
    print(f"   Found {len(languages)} languages")

    # Merge stats into profile
    profile["stats"].update({
        "total_commits": stats.get("total_commits", 0),
        "total_repos": stats.get("total_repos", 0),
        "total_stars": stats.get("total_stars", 0),
        "followers": stats.get("followers", 0),
        "following": stats.get("following", 0),
    })

    # Fallback: si la API no devolvió datos, usar languages del profile
    if not languages and profile.get("languages"):
        c = config["theme"]["colors"]
        profile_langs = profile["languages"]
        # Convertir formato {name: percent} a lista ordenada
        languages = [
            {"name": name, "percent": pct, "color": c["primary"]}
            for name, pct in sorted(profile_langs.items(), key=lambda x: -x[1])
        ]
        print(f"   Usando languages del profile.json como fallback")

    # Fallback: si no hay stats, usar valores del profile
    if stats.get("total_commits", 0) == 0:
        stats["total_commits"] = profile.get("stats", {}).get("total_commits", 0)
        stats["total_repos"] = profile.get("stats", {}).get("total_repos", 0)
        stats["total_stars"] = profile.get("stats", {}).get("total_stars", 0)
        stats["followers"] = profile.get("stats", {}).get("followers", 0)
        print(f"   Usando stats del profile.json como fallback")

    # Fallback: datos de contribución simulados si la API no devolvió
    if not stats.get("contribution_days"):
        import random
        random.seed(42)  # Determinista para consistencia
        days = []
        for _ in range(364):
            days.append({
                "date": "2025-01-01",
                "contributionCount": random.randint(0, 8),
                "color": "#00f0ff",
            })
        stats["contribution_days"] = days
        print(f"   Usando contribution_days simulados como fallback")

    # Actualizar lenguajes con datos reales
    if languages:
        profile["languages_real"] = languages

    print(f"\n🎨 Rendering SVGs...")

    # Render main profile SVG
    main_svg = render_hero_svg(profile, stats, languages, config["theme"]["colors"])
    output_dir = Path(config["paths"]["output"])
    output_dir.mkdir(exist_ok=True)

    main_path = output_dir / "profile_card.svg"
    main_path.write_text(main_svg, encoding="utf-8")
    print(f"   ✅ {main_path}")

    # Render languages SVG
    if languages:
        lang_svg = render_languages_svg(languages, profile)
        lang_path = output_dir / "languages_card.svg"
        lang_path.write_text(lang_svg, encoding="utf-8")
        print(f"   ✅ {lang_path}")

    # Render activity SVG
    activity_svg = render_activity_svg(stats)
    activity_path = output_dir / "activity_card.svg"
    activity_path.write_text(activity_svg, encoding="utf-8")
    print(f"   ✅ {activity_path}")

    print(f"\n✅ Done! SVGs generated in {output_dir}/")
    print(f"   Commit and push to update your profile README.")


if __name__ == "__main__":
    main()
