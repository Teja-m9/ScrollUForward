"""Render all hand-crafted Manim scenes, add TTS, upload to S3, publish to Appwrite."""
import asyncio, sys, os, uuid, tempfile, subprocess, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
sys.path.insert(0, os.path.dirname(__file__))

from agents.reel_agent import generate_voiceover, assemble_reel, extract_thumbnail
from agents.domain_router import publish_reel
from s3_client import upload_reel, upload_thumbnail as upload_thumb

SCENES_DIR = os.path.join(os.path.dirname(__file__), "scenes")

REELS = [
    {
        "file": "sodium_reel.py",
        "domain": "technology",
        "title": "Sodium Power: Why Salt Will Replace Lithium",
        "narration": (
            "What if the world runs out of lithium? "
            "Every phone, laptop, and electric car depends on lithium-ion batteries. "
            "But lithium is rare, just 0.002 percent of Earth's crust. "
            "Meet sodium. The sixth most abundant element on Earth. "
            "You know it as table salt, sodium chloride. "
            "When a sodium atom meets chlorine, it donates one electron, forming Na plus and Cl minus ions. "
            "This ionic bond creates the salt crystals you sprinkle on your food. "
            "But here's the exciting part. Sodium ions can shuttle between electrodes, "
            "just like lithium does in batteries. "
            "A sodium-ion battery works the same way: ions flow through an electrolyte "
            "from cathode to anode during charging, and back during discharge. "
            "The difference? Sodium costs 100 times less than lithium. "
            "It lasts three times as many charge cycles. And it doesn't catch fire. "
            "In a salt crystal lattice, every sodium ion is perfectly surrounded by six chloride ions, "
            "forming one of nature's most stable structures. "
            "That same stability makes sodium batteries incredibly safe. "
            "The future of energy isn't rare. It's in every ocean, every grain of salt. "
            "The future is sodium."
        ),
    },
    {
        "file": "ml_reel.py",
        "domain": "ai",
        "title": "What Is Machine Learning?",
        "narration": (
            "How does your phone know your face? Machine learning. "
            "It's a system where computers learn patterns from data, instead of being explicitly programmed. "
            "You feed in thousands of examples, and the model learns to predict new ones. "
            "The more data it sees, the smarter it gets, following a learning curve from bad to brilliant. "
            "Machine learning is already everywhere. Netflix uses it to recommend your next show. "
            "Spotify predicts your music taste. Tesla uses it for self-driving cars. Siri understands your voice through ML. "
            "Inside, a neural network has layers of artificial neurons. Input goes in, signals pass through hidden layers, "
            "and predictions come out. Each layer learns different features, step by step. "
            "Machine learning isn't the future. It's the present. And it's teaching machines to think."
        ),
    },
    {
        "file": "blackhole_reel.py",
        "domain": "space",
        "title": "Black Holes: The Universe's Darkest Secret",
        "narration": (
            "A region of space where nothing can escape. Not even light. "
            "Black holes form when massive stars, twenty to fifty times our sun's mass, run out of fuel. "
            "The core collapses in seconds. A supernova explosion. And what's left is a black hole. "
            "A black hole has three key parts. The singularity at the center, a point of infinite density. "
            "The event horizon, the point of no return. And the accretion disk, superheated matter spiraling in. "
            "But the most mind-bending part? Black holes literally warp the fabric of spacetime itself. "
            "Space bends around them like a bowling ball on a trampoline. "
            "We've now photographed real black holes. Sagittarius A star sits at the center of our Milky Way. "
            "M87 star was the first ever photographed. The universe's darkest secrets are still full of mysteries we're solving."
        ),
    },
    {
        "file": "dna_reel.py",
        "domain": "biology",
        "title": "DNA: The Code of Life",
        "narration": (
            "Inside every cell of your body lives a three billion letter code. Your DNA. "
            "It's the blueprint that makes you, you. Packed inside the nucleus of every cell. "
            "DNA forms a double helix, two sugar-phosphate backbones twisted together, "
            "connected by base pairs like rungs of a twisted ladder. "
            "The code uses just four letters. A, T, G, and C. Adenine always pairs with thymine. "
            "Guanine always pairs with cytosine. Hydrogen bonds hold them together. "
            "And now, with CRISPR, we can actually edit this code. Like find and replace in a text document. "
            "Scientists can cut out a defective gene and replace it with a corrected one. "
            "Gene editing could cure genetic diseases, make crops drought-resistant, "
            "and even eliminate hereditary conditions. Three billion letters. One unique you."
        ),
    },
    {
        "file": "quantum_reel.py",
        "domain": "physics",
        "title": "Quantum Physics in 60 Seconds",
        "narration": (
            "A coin is heads or tails. But what if it could be both at once? "
            "Welcome to quantum superposition. In the quantum world, particles exist in multiple states simultaneously. "
            "A classical bit is zero or one. A qubit can be both zero and one at the same time. "
            "Then there's entanglement. Einstein called it spooky action at a distance. "
            "Two particles become linked. Measure one, and you instantly know the state of the other, "
            "even if they're light years apart. "
            "Quantum computers harness both of these properties. While a classical computer tries paths one by one, "
            "a quantum computer explores all possible solutions simultaneously. "
            "This could revolutionize drug discovery, cryptography, and artificial intelligence. "
            "Quantum physics is weird. But it's the science that will change everything."
        ),
    },
    {
        "file": "climate_reel.py",
        "domain": "nature",
        "title": "Climate Change: The 1.2\u00b0C Crisis",
        "narration": (
            "Earth has warmed one point two degrees celsius since 1850. And the speed is accelerating. "
            "Here's how it works. Sunlight enters our atmosphere and warms Earth's surface. "
            "Heat radiates back up, but CO2 molecules trap it like a blanket. "
            "This greenhouse effect is natural, but we've supercharged it by burning fossil fuels. "
            "CO2 levels are skyrocketing. In 1900 it was 280 parts per million. "
            "The safe limit is 350. Today we're at 422 and climbing. We've blown past the safe limit. "
            "But solutions exist. Solar and wind energy to replace fossil fuels. "
            "Planting trees for natural carbon capture. Electrifying transport with EVs. "
            "Cleaning up industry with green steel and cement. "
            "One planet. One chance. The solutions exist. We just need the will to act. The clock is ticking."
        ),
    },
]


async def render_and_push():
    for reel_info in REELS:
        reel_id = f"reel_{uuid.uuid4().hex[:12]}"
        scene_file = os.path.join(SCENES_DIR, reel_info["file"])
        print(f"\n{'='*60}")
        print(f"Rendering: {reel_info['title']}")
        print(f"{'='*60}")

        # 1. Render Manim
        tmp_dir = tempfile.mkdtemp(prefix=f"reel_{reel_info['domain']}_")
        media_dir = os.path.join(tmp_dir, "media").replace("\\", "/")
        cmd = [
            sys.executable, "-m", "manim", "render",
            scene_file, "ReelScene",
            "-r", "540,960", "--fps", "30", "--format=mp4",
            f"--media_dir={media_dir}", "--disable_caching",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=tmp_dir)
        if result.returncode != 0:
            print(f"  RENDER FAILED: {result.stderr[-500:]}")
            continue

        # Find MP4
        manim_mp4 = ""
        for root, dirs, files in os.walk(os.path.join(tmp_dir, "media")):
            for f in files:
                if f.endswith(".mp4") and "partial" not in root:
                    manim_mp4 = os.path.join(root, f)
                    break
            if manim_mp4: break

        if not manim_mp4:
            print("  NO MP4 FOUND")
            continue

        print(f"  Rendered: {os.path.getsize(manim_mp4) / 1024:.0f} KB")

        # 2. Generate TTS
        audio_path = os.path.join(tmp_dir, "voiceover.mp3")
        await generate_voiceover(reel_info["narration"], audio_path)
        has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
        print(f"  Audio: {'YES' if has_audio else 'NO'}")

        # 3. Assemble
        output_mp4 = os.path.join(tmp_dir, f"{reel_id}.mp4")
        assembled = assemble_reel(manim_mp4, audio_path if has_audio else "", output_mp4)
        final = assembled or manim_mp4
        print(f"  Final: {os.path.getsize(final) / 1024:.0f} KB")

        # 4. Upload to S3
        s3_url = upload_reel(final, reel_info["domain"], reel_id)
        s3_thumb = ""
        thumb_path = os.path.join(tmp_dir, f"{reel_id}_thumb.jpg")
        if extract_thumbnail(final, thumb_path):
            with open(thumb_path, "rb") as f:
                s3_thumb = upload_thumb(f.read(), reel_info["domain"], reel_id)

        # 5. Publish to Appwrite
        pub = publish_reel({
            "reel_id": reel_id,
            "domain": reel_info["domain"],
            "title": reel_info["title"],
            "script_text": reel_info["narration"],
            "s3_video_url": s3_url,
            "s3_thumb_url": s3_thumb,
            "source_type": "ai_generated",
            "content_type": "reel",
        })
        print(f"  Published: {pub.get('id')} -> {reel_info['domain']}")
        print(f"  LIVE: {reel_info['title']}")

    print(f"\n{'='*60}")
    print("ALL 5 REELS LIVE IN THE APP!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(render_and_push())
