"""
Fetch Pollinations.ai images for all 20 news items and update Appwrite thumbnail_url.
Run: python add_news_thumbnails.py
"""
import os, sys, time, datetime, urllib.parse, urllib.request, tempfile, logging

sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("thumbs")

# Map news doc ID → image prompt
NEWS_THUMBS = [
    ("news_b49b7e9538a1", "rocket,moon,nasa,space"),
    ("news_1f6b3c062945", "artificial,intelligence,technology,computer"),
    ("news_90d41ce4a7bb", "satellite,space,orbit,technology"),
    ("news_edbe14617701", "quantum,computer,laboratory,technology"),
    ("news_4e16e3bbe0d4", "google,technology,AI,digital"),
    ("news_8bba3ac7fe4e", "brain,neuroscience,medical,technology"),
    ("news_4edfbb50aa0c", "solar,wind,energy,renewable"),
    ("news_50ccc880ae9a", "military,jet,fighter,war"),
    ("news_2fd8e1fc62a4", "wind,turbine,ocean,energy"),
    ("news_8780de34679b", "quantum,physics,laboratory,science"),
    ("news_5aea622a194d", "data,center,server,technology"),
    ("news_bde0db1e6652", "physics,science,research,laboratory"),
    ("news_d47b043e607e", "robot,artificial,intelligence,factory"),
    ("news_5609f855cb55", "city,power,energy,night"),
    ("news_d88dec92f1fd", "self,driving,car,autonomous,technology"),
    ("news_d4b0a54c90b7", "humanitarian,crisis,refugees,aid"),
    ("news_11290d546c78", "venezuela,politics,government,latin,america"),
    ("news_7109827c0612", "climate,summit,conference,environment"),
    ("news_dc6eb3bc09dd", "superconductor,crystal,physics,laboratory"),
    ("news_cd773024a727", "moon,space,rocket,nasa,lunar"),
]


def fetch_image(keywords: str, out_path: str, idx: int) -> bool:
    """Fetch a relevant photo from loremflickr.com (CC-licensed, no API key, no rate limit)."""
    # loremflickr returns a real photo matching the keyword(s)
    kw = urllib.parse.quote(keywords.replace(" ", ","))
    url = f"https://loremflickr.com/800/450/{kw}?lock={idx+200}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if len(data) < 5000:
            return False
        with open(out_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        log.warning(f"  Image failed: {e}")
        return False


def main():
    from dotenv import load_dotenv
    load_dotenv()
    from appwrite_client import get_databases
    from config import APPWRITE_DATABASE_ID, COLLECTION_CONTENT, AWS_S3_BUCKET
    from s3_client import get_s3_client

    db = get_databases()
    s3 = get_s3_client()
    tmp = tempfile.mkdtemp(prefix="news_thumbs_")
    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    updated = 0
    for i, (doc_id, prompt) in enumerate(NEWS_THUMBS):
        log.info(f"[{i+1:02d}/20] {doc_id}")
        img_path = os.path.join(tmp, f"{doc_id}.jpg")

        # Fetch image — retry once on failure
        ok = fetch_image(prompt, img_path, i)
        if not ok:
            log.info(f"  Retrying...")
            time.sleep(2)
            ok = fetch_image(prompt, img_path, i + 50)

        if not ok:
            log.warning(f"  Skipping {doc_id} — no image")
            time.sleep(5)
            continue

        # Upload to S3
        key = f"news/thumbnails/{date_str}/{doc_id}.jpg"
        try:
            s3.upload_file(img_path, AWS_S3_BUCKET, key,
                           ExtraArgs={"ContentType": "image/jpeg"})
            thumb_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": AWS_S3_BUCKET, "Key": key},
                ExpiresIn=86400 * 7,  # 7 days
            )
            log.info(f"  S3 upload OK")
        except Exception as e:
            log.error(f"  S3 failed: {e}")
            time.sleep(5)
            continue

        # Update Appwrite document
        try:
            db.update_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_CONTENT,
                document_id=doc_id,
                data={"thumbnail_url": thumb_url},
            )
            log.info(f"  Appwrite updated ✓")
            updated += 1
        except Exception as e:
            log.error(f"  Appwrite update failed: {e}")

        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"  Thumbnails added: {updated}/20 news items")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
