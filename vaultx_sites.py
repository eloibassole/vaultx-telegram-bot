"""
Liste de sites VaultX à mettre en avant dans les posts.
Modifie cette liste avec tes vrais slugs depuis clicks.jsonl (les plus cliqués).
"""

FEATURED_SITES = [
    {"domain": "exemple1.com", "category": "Amateur"},
    {"domain": "exemple2.com", "category": "Asian"},
    {"domain": "exemple3.com", "category": "MILF"},
    {"domain": "exemple4.com", "category": "BBW"},
    {"domain": "exemple5.com", "category": "Latina"},
    {"domain": "exemple6.com", "category": "Redhead"},
    {"domain": "exemple7.com", "category": "Ebony"},
    {"domain": "exemple8.com", "category": "Teen (18+)"},
    {"domain": "exemple9.com", "category": "Mature"},
    {"domain": "exemple10.com", "category": "Couples"},
]

def get_random_site():
    """Retourne un site aléatoire depuis la liste."""
    import random
    return random.choice(FEATURED_SITES)
