"""
Seed demo data into Appwrite collections.
Usage: python seed.py
"""
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from config import APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY, APPWRITE_DATABASE_ID
from auth import hash_password
import json

client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)

DB = APPWRITE_DATABASE_ID


def seed():
    print("[*] Seeding demo data...\n")

    # ─── Demo Users ──────────────────────────────────────
    users = [
        {
            "id": "user_alice",
            "username": "alice_quantum",
            "email": "alice@scrolluforward.com",
            "display_name": "Dr. Alice Chen",
            "bio": "Quantum physicist | AI researcher | Making the complex simple.",
            "iq_score": 2850,
            "knowledge_rank": "Master",
            "interest_tags": json.dumps(["physics", "ai", "mathematics"]),
            "followers_count": 14200,
            "following_count": 342,
            "posts_count": 87,
            "streak_days": 45,
            "badges": json.dumps(["verified_expert", "top_contributor", "streak_master"]),
        },
        {
            "id": "user_marcus",
            "username": "marcus_history",
            "email": "marcus@scrolluforward.com",
            "display_name": "Prof. Marcus Webb",
            "bio": "Ancient civilizations historian | Author of 'Lost Empires'",
            "iq_score": 1890,
            "knowledge_rank": "Expert",
            "interest_tags": json.dumps(["history", "ancient_civilizations", "philosophy"]),
            "followers_count": 8900,
            "following_count": 210,
            "posts_count": 62,
            "streak_days": 30,
            "badges": json.dumps(["verified_expert", "article_master"]),
        },
        {
            "id": "user_elena",
            "username": "elena_nature",
            "email": "elena@scrolluforward.com",
            "display_name": "Elena Rodriguez",
            "bio": "Marine biologist | National Geographic contributor",
            "iq_score": 3200,
            "knowledge_rank": "Master",
            "interest_tags": json.dumps(["nature", "biology", "space"]),
            "followers_count": 22000,
            "following_count": 156,
            "posts_count": 124,
            "streak_days": 60,
            "badges": json.dumps(["verified_expert", "viral_creator", "grandmaster_streak"]),
        },
    ]

    for u in users:
        uid = u.pop("id")
        u["password_hash"] = hash_password("demo123")
        u["avatar_url"] = ""
        try:
            db.create_document(DB, "users", uid, u)
            print(f"  [OK] User: {u['display_name']}")
        except Exception as e:
            print(f"  [!!] User {u['display_name']}: {e}")

    # ─── Demo Content ────────────────────────────────────
    content_items = [
        {
            "title": "Quantum Entanglement Explained in 60 Seconds",
            "body": "Quantum entanglement is one of the most fascinating phenomena in physics. When two particles become entangled, measuring one instantly affects the other, regardless of distance. Einstein called it 'spooky action at a distance.' Recent experiments have confirmed that entanglement is real and is now the basis for quantum computing and quantum cryptography.",
            "content_type": "reel",
            "domain": "physics",
            "author_id": "user_alice",
            "author_username": "alice_quantum",
            "citations": json.dumps(["https://arxiv.org/abs/quantum-entanglement-2024"]),
            "tags": json.dumps(["quantum", "physics", "science"]),
            "quality_score": 95,
            "likes_count": 4200,
            "views_count": 28000,
        },
        {
            "title": "The Lost Library of Alexandria: What We Actually Know",
            "body": "The Library of Alexandria has been mythologized as holding all human knowledge, but what do we actually know? Founded by Ptolemy I around 295 BCE, the library was part of the Mouseion, a research institution. It likely held between 40,000 to 400,000 scrolls. The destruction wasn't a single event but a gradual decline over centuries, involving Julius Caesar's fire in 48 BCE, religious conflicts, and the Arab conquest in 642 CE. Modern scholarship suggests that the library's significance lies not in its destruction but in what it represented: humanity's first attempt at creating a universal repository of knowledge.\n\nRecent archaeological discoveries at the site have revealed new insights into the library's organizational system, which resembled modern cataloging methods. The head librarian Callimachus created the Pinakes, often considered the world's first library catalog.",
            "content_type": "article",
            "domain": "history",
            "author_id": "user_marcus",
            "author_username": "marcus_history",
            "citations": json.dumps(["https://doi.org/10.1093/library-alexandria", "https://pubmed.ncbi.nlm.nih.gov/ancient-texts"]),
            "tags": json.dumps(["history", "ancient_civilizations", "library"]),
            "quality_score": 92,
            "likes_count": 8900,
            "views_count": 42000,
        },
        {
            "title": "Deep-Sea Creatures That Produce Their Own Light",
            "body": "Bioluminescence in the deep ocean is more common than we thought. Over 75% of deep-sea organisms produce their own light through chemical reactions. From the anglerfish's lure to the flashlight fish's photophores, these creatures have evolved remarkable ways to hunt, communicate, and survive in complete darkness.",
            "content_type": "reel",
            "domain": "nature",
            "author_id": "user_elena",
            "author_username": "elena_nature",
            "citations": json.dumps(["https://doi.org/10.1038/bioluminescence-deep-sea"]),
            "tags": json.dumps(["nature", "biology", "ocean"]),
            "quality_score": 90,
            "likes_count": 12400,
            "views_count": 65000,
        },
        {
            "title": "GPT-5 Architecture Leaked: What It Means for AGI",
            "body": "Recent reports suggest that OpenAI's next-generation model incorporates a novel mixture-of-experts architecture with 8T parameters. Sources familiar with the development say the model demonstrates unprecedented reasoning capabilities, including mathematical proof generation and multi-step scientific hypothesis testing. This represents a significant step toward artificial general intelligence.",
            "content_type": "news",
            "domain": "ai",
            "author_id": "user_alice",
            "author_username": "alice_quantum",
            "citations": json.dumps(["https://arxiv.org/abs/gpt5-architecture-analysis"]),
            "tags": json.dumps(["ai", "technology", "agi"]),
            "quality_score": 85,
            "likes_count": 15600,
            "views_count": 89000,
        },
        {
            "title": "How Neural Networks Actually Learn: A Visual Guide",
            "body": "Neural networks learn through backpropagation, but what does that really mean? At each layer, the network transforms input data through weighted connections. During training, the error is calculated at the output and propagated backward, adjusting weights to minimize loss. Think of it as a sculptor refining a statue — each pass removes a bit more material until the shape emerges. The key insight is that deep networks can learn hierarchical representations: edges → textures → patterns → objects.",
            "content_type": "reel",
            "domain": "ai",
            "author_id": "user_alice",
            "author_username": "alice_quantum",
            "citations": json.dumps(["https://arxiv.org/abs/neural-network-visual-guide"]),
            "tags": json.dumps(["ai", "technology", "machine_learning"]),
            "quality_score": 93,
            "likes_count": 7800,
            "views_count": 35000,
        },
        {
            "title": "The Roman Empire's Concrete Was Better Than Ours",
            "body": "Roman concrete (opus caementicium) has survived 2,000+ years, while modern concrete cracks within decades. Recent research reveals the secret: volcanic ash (pozzolana) mixed with seawater created a self-healing material. When cracks form, seawater reacts with the volcanic minerals to grow new crystals that fill the gaps. Engineers are now studying this to create more sustainable modern concrete and reduce the massive carbon footprint of cement production.",
            "content_type": "article",
            "domain": "history",
            "author_id": "user_marcus",
            "author_username": "marcus_history",
            "citations": json.dumps(["https://doi.org/10.1126/roman-concrete-2023"]),
            "tags": json.dumps(["history", "engineering", "ancient_civilizations"]),
            "quality_score": 91,
            "likes_count": 11200,
            "views_count": 54000,
        },
        {
            "title": "CRISPR Gene Editing Cures Sickle Cell Disease",
            "body": "In a landmark clinical trial, CRISPR-Cas9 gene editing has effectively cured sickle cell disease in 29 out of 30 patients. The therapy, called exa-cel, edits patients' own stem cells to produce functional fetal hemoglobin, bypassing the defective gene. This marks the first FDA-approved CRISPR therapy and opens the door to treating thousands of genetic diseases.",
            "content_type": "news",
            "domain": "biology",
            "author_id": "user_elena",
            "author_username": "elena_nature",
            "citations": json.dumps(["https://pubmed.ncbi.nlm.nih.gov/crispr-sickle-cell"]),
            "tags": json.dumps(["biology", "technology", "genetics"]),
            "quality_score": 96,
            "likes_count": 18900,
            "views_count": 120000,
        },
        {
            "title": "The Mathematics Behind Black Holes",
            "body": "Black holes are described by just three numbers: mass, charge, and spin (the 'no-hair theorem'). Einstein's field equations predict a singularity at the center, but quantum mechanics suggests something more complex. The event horizon isn't a physical surface — it's the boundary beyond which light cannot escape. Hawking showed that black holes actually radiate energy (Hawking radiation), meaning they slowly evaporate over astronomical timescales.",
            "content_type": "reel",
            "domain": "physics",
            "author_id": "user_alice",
            "author_username": "alice_quantum",
            "citations": json.dumps(["https://arxiv.org/abs/black-hole-mathematics"]),
            "tags": json.dumps(["physics", "space", "mathematics"]),
            "quality_score": 94,
            "likes_count": 9500,
            "views_count": 47000,
        },
    ]

    for item in content_items:
        item.setdefault("thumbnail_url", "")
        item.setdefault("media_url", "")
        item.setdefault("author_avatar", "")
        item.setdefault("saves_count", 0)
        item.setdefault("comments_count", 0)
        try:
            db.create_document(DB, "content", ID.unique(), item)
            print(f"  [OK] Content: {item['title'][:50]}...")
        except Exception as e:
            print(f"  [!!] Content: {e}")

    # ─── Demo Discussions ────────────────────────────────
    discussions = [
        {
            "title": "Is quantum computing overhyped?",
            "description": "Let's have a fact-based discussion about the realistic timeline for practical quantum computing. Please cite sources.",
            "domain": "physics",
            "creator_id": "user_alice",
            "creator_username": "alice_quantum",
            "creator_avatar": "",
            "tags": json.dumps(["quantum", "technology", "debate"]),
            "comments_count": 24,
            "participants_count": 15,
        },
        {
            "title": "Underrated ancient civilizations",
            "description": "Which civilizations deserve more attention in mainstream history education? Discuss with evidence.",
            "domain": "history",
            "creator_id": "user_marcus",
            "creator_username": "marcus_history",
            "creator_avatar": "",
            "tags": json.dumps(["history", "ancient_civilizations", "education"]),
            "comments_count": 42,
            "participants_count": 28,
        },
        {
            "title": "Climate change: latest data and solutions",
            "description": "A citations-required thread on the most recent climate science data and viable solutions. No politics, only peer-reviewed science.",
            "domain": "nature",
            "creator_id": "user_elena",
            "creator_username": "elena_nature",
            "creator_avatar": "",
            "tags": json.dumps(["nature", "climate", "science"]),
            "comments_count": 56,
            "participants_count": 38,
        },
    ]

    for disc in discussions:
        try:
            db.create_document(DB, "discussions", ID.unique(), disc)
            print(f"  [OK] Discussion: {disc['title']}")
        except Exception as e:
            print(f"  [!!] Discussion: {e}")

    print("\n[OK] Seeding complete!")
    print("[*] Start the server with: uvicorn main:app --reload")


if __name__ == "__main__":
    seed()
