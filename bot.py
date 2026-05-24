"""
Telegram Content Bot - Canal adulte bilingue FR/EN
Génère et poste automatiquement du contenu via Claude Haiku
"""

import os
import json
import random
import logging
import schedule
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
import anthropic

from vaultx_sites import get_random_site

# ─── CONFIG ────────────────────────────────────────────────────────────────────

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
POSTS_PER_DAY = int(os.getenv("POSTS_PER_DAY", "4"))
INCLUDE_VAULTX_LINKS = os.getenv("INCLUDE_VAULTX_LINKS", "true").lower() == "true"
VAULTX_BASE_URL = os.getenv("VAULTX_BASE_URL", "https://vaultxxx.netlify.app")

LOG_FILE = "posts_log.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── TYPES DE CONTENU ──────────────────────────────────────────────────────────

CONTENT_TYPES = [
    "teaser_fr",
    "teaser_en",
    "spotlight_fr",    # Post avec lien VaultX
    "spotlight_en",    # Post avec lien VaultX
    "engagement_fr",   # Question / interaction
    "engagement_en",
    "promo_1xbet_fr",  # Promo code 1XBET
    "promo_1xbet_en",
]

PROMPTS = {
    "teaser_fr": """
Génère un post Telegram court et accrocheur en français (2-4 phrases max).
Objectif : créer de la curiosité et l'envie irrésistible de cliquer.
Ton : mystérieux, intrigant, confidentiel — comme si tu révélais un secret.
Pas de hashtags. Pas de liens. Juste le texte brut.
2-3 emojis intégrés naturellement.

Exemples du style exact attendu :
- "Certains soirs, une seule image change tout. Ce soir, c'est ce soir. 🔥"
- "Tu sais ce sentiment quand tu tombes sur quelque chose et tu peux plus t'arrêter ? Exactement ça. 👀"
- "Le contenu qu'on ne montre pas partout. Pour ceux qui savent. 😏"
""",
    "teaser_en": """
Generate a short, catchy Telegram post in English (2-4 sentences max).
Goal: create curiosity and an irresistible urge to click.
Tone: mysterious, intriguing, confidential — like revealing a secret.
No hashtags. No links. Just raw text.
2-3 emojis integrated naturally.

Examples of the exact style expected:
- "Some nights, one click changes everything. Tonight's that night. 🔥"
- "You know that feeling when you find something and can't stop? Exactly that. 👀"
- "The content they don't show everywhere. For those who know. 😏"
""",
    "spotlight_fr": """
Génère un post Telegram promotionnel en français (2-3 phrases max).
Tu présentes un répertoire de sites dans la niche : {category}.
Le répertoire s'appelle VaultX et contient 2418 sites triés et vérifiés gratuitement.

Style : copywriting direct, chiffres concrets, bénéfice immédiat.
Ton : confidentiel, exclusif, comme une recommandation entre amis.
Termine EXACTEMENT par : "👉 Explorer : {link}"
1-2 emojis dans le corps. Pas de hashtags.

Style cible : "2 418 sites {category}. Triés. Vérifiés. Gratuits. Tout au même endroit. 🎯"
""",
    "spotlight_en": """
Generate a promotional Telegram post in English (2-3 sentences max).
You're presenting a site directory in the niche: {category}.
The directory is called VaultX and contains 2,418 free, sorted, verified sites.

Style: direct copywriting, concrete numbers, immediate benefit.
Tone: confidential, exclusive, like a recommendation between friends.
End EXACTLY with: "👉 Explore: {link}"
1-2 emojis in the body. No hashtags.

Target style: "2,418 {category} sites. Sorted. Verified. Free. All in one place. 🎯"
""",
    "engagement_fr": """
Génère une mini-question ou accroche interactive pour un canal Telegram (max 2 phrases).
Objectif : faire réagir et créer de la conversation.
Ton : complice, fun, légèrement taquin.
Pas de liens. Pas de hashtags. 2 emojis max.

Formats acceptés :
- Question de préférence simple ("Nuit ou journée ? 🌙")
- Affirmation suivie d'une question courte
- Sondage de style ou d'ambiance

Génère UN seul post. Pas d'explication autour.
""",
    "engagement_en": """
Generate a mini-question or interactive hook for a Telegram channel (max 2 sentences).
Goal: get reactions and start conversations.
Tone: playful, fun, slightly teasing.
No links. No hashtags. Max 2 emojis.

Accepted formats:
- Simple preference question ("Night or day? 🌙")
- Statement followed by a short question
- Style or mood poll

Generate ONE single post. No surrounding explanation.
""",
    "promo_1xbet_fr": """
Génère un post Telegram promotionnel en français (3-4 phrases max) pour 1XBET.
Code promo : PSP86 — il donne accès à des bonus de bienvenue et promotions exclusives.

Style : copywriting percutant, bénéfice immédiat, sentiment d'opportunité à ne pas manquer.
Ton : confidentiel, entre amis, comme si tu partageais un bon plan.
Termine EXACTEMENT par : "👉 Code promo : PSP86"
2-3 emojis intégrés naturellement. Pas de hashtags.

Varie les angles à chaque fois : bonus de bienvenue, paris sportifs, casino, jackpots, cashback, freebets.
Exemple de style : "Les meilleurs matchs du week-end arrivent. Avec 1XBET et le code PSP86, ton premier dépôt est boosté dès maintenant. Ne rate pas ça. 🎯\n👉 Code promo : PSP86"

Génère UN seul post. Pas d'explication autour.
""",
    "promo_1xbet_en": """
Generate a promotional Telegram post in English (3-4 sentences max) for 1XBET.
Promo code: PSP86 — unlocks welcome bonuses and exclusive promotions.

Style: punchy copywriting, immediate benefit, sense of opportunity not to be missed.
Tone: confidential, between friends, like sharing a good deal.
End EXACTLY with: "👉 Promo code: PSP86"
2-3 emojis integrated naturally. No hashtags.

Vary the angle each time: welcome bonus, sports betting, casino, jackpots, cashback, freebets.
Example style: "Big matches this weekend. With 1XBET and code PSP86, your first deposit gets a boost right now. Don't sleep on this. 🎯\n👉 Promo code: PSP86"

Generate ONE single post. No surrounding explanation.
""",
}

# ─── GÉNÉRATION DE CONTENU ─────────────────────────────────────────────────────

def generate_content(content_type: str) -> str:
    """Génère un post via Claude Haiku."""
    site = None
    prompt = PROMPTS[content_type]

    if "spotlight" in content_type and INCLUDE_VAULTX_LINKS:
        site = get_random_site()
        link = f"{VAULTX_BASE_URL}/go/{site['domain']}"
        prompt = prompt.format(category=site["category"], link=link)
    elif "spotlight" in content_type and not INCLUDE_VAULTX_LINKS:
        # Pas de lien activé : switcher vers un teaser classique
        lang = "fr" if "_fr" in content_type else "en"
        content_type = f"teaser_{lang}"
        prompt = PROMPTS[content_type]

    REFUSAL_MARKERS = [
        "je ne peux pas", "i can't", "i cannot", "i'm unable", "je suis incapable",
        "je suis désolé", "i'm sorry", "i apologize", "désolé, je ne", "sorry, i",
        "je ne suis pas en mesure", "not able to", "unable to fulfill",
        "i'm not able", "this request", "cette demande"
    ]

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()

        # Filtre anti-refus
        text_lower = text.lower()
        if any(marker in text_lower for marker in REFUSAL_MARKERS):
            log.warning(f"Refus détecté ({content_type}), contenu ignoré.")
            return None, content_type, site

        # Nettoyer les headers markdown qui ne s'affichent pas bien dans Telegram
        text = text.replace("# ", "").replace("## ", "").replace("### ", "")

        log.info(f"Contenu généré ({content_type}) : {text[:80]}...")
        return text, content_type, site

    except Exception as e:
        log.error(f"Erreur génération Claude : {e}")
        return None, content_type, site


# ─── ENVOI TELEGRAM ────────────────────────────────────────────────────────────

def send_to_telegram(text: str) -> bool:
    """Envoie un message dans le canal Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log.info(f"Message envoyé dans {TELEGRAM_CHANNEL_ID}")
        return True
    except requests.RequestException as e:
        log.error(f"Erreur Telegram : {e}")
        return False


# ─── LOGGING DES POSTS ────────────────────────────────────────────────────────

def log_post(text: str, content_type: str, site: dict, success: bool):
    """Enregistre chaque post dans le fichier de logs."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "content_type": content_type,
        "site": site["domain"] if site else None,
        "text": text,
        "success": success
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ─── CYCLE PRINCIPAL ──────────────────────────────────────────────────────────

def pick_content_type() -> str:
    """Choisit le type de contenu selon une rotation équilibrée."""
    # 40% teasers, 40% spotlights (si VaultX activé), 20% engagement
    weights = {
        "teaser_fr": 15,
        "teaser_en": 15,
        "spotlight_fr": 15 if INCLUDE_VAULTX_LINKS else 0,
        "spotlight_en": 15 if INCLUDE_VAULTX_LINKS else 0,
        "engagement_fr": 10,
        "engagement_en": 10,
        "promo_1xbet_fr": 10,
        "promo_1xbet_en": 10,
    }
    types = [k for k, v in weights.items() if v > 0]
    w = [weights[k] for k in types]
    return random.choices(types, weights=w, k=1)[0]


def post_job():
    """Job exécuté à chaque publication planifiée."""
    log.info("--- Lancement d'une publication ---")
    content_type = pick_content_type()
    text, actual_type, site = generate_content(content_type)

    if not text:
        log.warning("Aucun contenu généré, skip.")
        return

    success = send_to_telegram(text)
    log_post(text, actual_type, site, success)

    if success:
        log.info("Publication réussie.")
    else:
        log.warning("Échec de publication.")


# ─── PLANIFICATION ────────────────────────────────────────────────────────────

def setup_schedule():
    """Configure les horaires de publication."""
    # Calcule les heures optimales selon le nombre de posts/jour
    # Heures de pointe pour un canal adulte : matin, midi, soir, nuit
    all_slots = ["08:00", "12:30", "19:00", "22:30", "00:30"]
    slots = all_slots[:POSTS_PER_DAY]

    for slot in slots:
        schedule.every().day.at(slot).do(post_job)
        log.info(f"Publication planifiée à {slot}")


# ─── DÉMARRAGE ────────────────────────────────────────────────────────────────

def validate_config():
    """Vérifie que les variables d'environnement sont bien définies."""
    missing = []
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("sk-ant-X"):
        missing.append("ANTHROPIC_API_KEY")
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("7XXXXXXXXXX"):
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHANNEL_ID or TELEGRAM_CHANNEL_ID == "@toncanal":
        missing.append("TELEGRAM_CHANNEL_ID")

    if missing:
        log.error(f"Variables manquantes dans .env : {', '.join(missing)}")
        log.error("Configure le fichier .env avant de lancer le bot.")
        return False
    return True


if __name__ == "__main__":
    log.info("=== Telegram Content Bot démarré ===")

    if not validate_config():
        exit(1)

    # Test immédiat : poster un message de test
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        log.info("Mode test : publication immédiate")
        post_job()
        exit(0)

    # Mode normal : planification
    setup_schedule()
    log.info(f"Bot actif. {POSTS_PER_DAY} posts/jour planifiés.")
    log.info("Ctrl+C pour arrêter.")

    while True:
        schedule.run_pending()
        time.sleep(30)
