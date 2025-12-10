# data/parser.py
from typing import List, Dict


def parse_table_sites(table) -> List[Dict]:
    """
    transforme le QTableWidget des sites en liste de dictionnaires.
    Chaque site : {'name': str, 'x': float, 'y': float, 'capacity': int}

    Args:
        table: QTableWidget contenant les données des sites

    Returns:
        Liste de dictionnaires représentant les sites
    """
    sites = []
    for row in range(table.rowCount()):
        try:
            #nom du site
            name_item = table.item(row, 0)
            name = name_item.text().strip() if name_item else ""
            if not name:
                continue  # Ignorer les lignes sans nom

            #coordonnée X
            x_item = table.item(row, 1)
            x = float(x_item.text()) if x_item and x_item.text().strip() else 0.0

            #coordonnée Y
            y_item = table.item(row, 2)
            y = float(y_item.text()) if y_item and y_item.text().strip() else 0.0

            #capacité (optionnelle)
            cap_item = table.item(row, 3)
            cap_text = cap_item.text().strip() if cap_item else ""
            capacity = int(cap_text) if cap_text and cap_text.isdigit() else 0

            sites.append({
                'name': name,
                'x': x,
                'y': y,
                'capacity': capacity
            })
        except (ValueError, AttributeError) as e:
            print(f"⚠Erreur parsing site ligne {row + 1}: {e}")
            continue

    return sites


def parse_table_zones(table) -> List[Dict]:
    """
    transforme le QTableWidget des zones en liste de dictionnaires.
    Chaque zone : {'name': str, 'x': float, 'y': float, 'population': int, 'priority': int}

    Args:
        table: QTableWidget contenant les données des zones

    Returns:
        Liste de dictionnaires représentant les zones
    """
    zones = []
    for row in range(table.rowCount()):
        try:
            #nom de la zone
            name_item = table.item(row, 0)
            name = name_item.text().strip() if name_item else ""
            if not name:
                continue  # Ignorer les lignes sans nom

            #coordonnée X
            x_item = table.item(row, 1)
            x = float(x_item.text()) if x_item and x_item.text().strip() else 0.0

            #coordonnée Y
            y_item = table.item(row, 2)
            y = float(y_item.text()) if y_item and y_item.text().strip() else 0.0

            #population
            pop_item = table.item(row, 3)
            pop_text = pop_item.text().strip() if pop_item else "0"
            population = int(pop_text) if pop_text.isdigit() else 0

            #priorité (optionnelle, par défaut = 1)
            prio_item = table.item(row, 4)
            prio_text = prio_item.text().strip() if prio_item else "1"
            priority = int(prio_text) if prio_text.isdigit() else 1

            zones.append({
                'name': name,
                'x': x,
                'y': y,
                'population': population,
                'priority': priority if priority > 0 else 1
            })
        except (ValueError, AttributeError) as e:
            print(f"⚠Erreur parsing zone ligne {row + 1}: {e}")
            continue

    return zones


def distance(site: Dict, zone: Dict) -> float:
    """
    calcule la distance Euclidienne entre un site et une zone.

    Args:
        site: Dictionnaire avec 'x' et 'y'
        zone: Dictionnaire avec 'x' et 'y'

    Returns:
        Distance en kilomètres
    """
    dx = site['x'] - zone['x']
    dy = site['y'] - zone['y']
    return (dx ** 2 + dy ** 2) ** 0.5