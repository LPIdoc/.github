
import json
import os
import re
import urllib.request
from pathlib import Path

ORG = "LPIdoc"
README = Path("profile/README.md")

START = "<!-- REPOS:START -->"
END = "<!-- REPOS:END -->"


def get_repositories():
    """Obtiene todos los repositorios públicos de la organización."""
    repos = []
    page = 1

    while True:
        url = (
            f"https://api.github.com/orgs/{ORG}/repos"
            f"?type=public&per_page=100&page={page}"
        )

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "LPIdoc-profile-updater",
        }

        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        request = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)

        repos.extend(data)

        if len(data) < 100:
            break

        page += 1

    return sorted(
        (repo for repo in repos if repo["name"] != ".github"),
        key=lambda repo: repo["name"].lower(),
    )


def generate_index(repos):
    """Genera el índice en formato Markdown."""
    lines = []

    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        description = repo.get("description") or "Sin descripción."
        homepage = (repo.get("homepage") or "").strip()

        description = " ".join(description.split())
        description = description.replace("\\", "\\\\")
        description = re.sub(r"([*_`[\]])", r"\\\1", description)

        # Nombre y descripción
        line = f"- **{name}**: {description}"

        # Página web (si existe)
        if homepage:
            if not homepage.startswith(("https://", "http://")):
                homepage = "https://" + homepage

            line += f" · [🌐 Página web]({homepage})"

        # Enlace al repositorio (siempre)
        line += f" · [📁 Repositorio]({url})"

        lines.append(line)

    return "\n".join(lines) if lines else "_No hay repositorios públicos._"


def update_readme():
    content = README.read_text(encoding="utf-8")

    if START not in content or END not in content:
        raise ValueError("No se encontraron los marcadores del índice.")

    if content.index(START) > content.index(END):
        raise ValueError("Los marcadores están en orden incorrecto.")

    index = generate_index(get_repositories())

    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        re.DOTALL,
    )

    updated = pattern.sub(
        lambda _: f"{START}\n{index}\n{END}",
        content,
        count=1,
    )

    if updated != content:
        README.write_text(updated, encoding="utf-8")
        print("README actualizado.")
    else:
        print("El índice ya está actualizado.")


if __name__ == "__main__":
    update_readme()
