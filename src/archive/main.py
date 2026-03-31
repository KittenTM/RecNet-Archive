import asyncio
import aiohttp
import json
import os
from pathlib import Path
from tabulate import tabulate
from internetarchive import upload
from dotenv import load_dotenv

from profiles.bio import fetch_bio
from profiles.subscriberCount import fetch_subscriber_count
from profiles.info import fetch_bulk_info 
from profiles.images import fetch_player_images

load_dotenv()
IA_ACCESS_KEY = os.getenv("IA_ACCESS_KEY")
IA_SECRET_KEY = os.getenv("IA_SECRET_KEY")
IA_IDENTIFIER = os.getenv("IA_IDENTIFIER")

# recnet ratelimits
MAX_CONCURRENT_REQUESTS = 20
BATCH_SIZE = 20
SLEEP_BETWEEN_BATCHES = 11
# only here for testing
START_ID = 0
END_ID = 50

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://rec.net/",
    "Origin": "https://rec.net",
}

def save_to_folders(base_path, data):
    acc_id = data["id"]
    user_dir = Path(base_path) / str(acc_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    with open(user_dir / "info.json", "w") as f:
        json.dump(data["info"], f, indent=4)
    
    with open(user_dir / "bio.json", "w") as f:
        json.dump(data["bio"], f, indent=4)
    
    with open(user_dir / "images.json", "w") as f:
        json.dump(data["images"], f, indent=4)
        
    with open(user_dir / "stats.json", "w") as f:
        json.dump({"subscriberCount": data["subs"]}, f, indent=4)

async def fetch_remaining_data(session, account_id, info_dict, semaphore):
    async with semaphore:
        b_status, b_data = await fetch_bio(session, account_id)
        s_status, s_data = await fetch_subscriber_count(session, account_id)
        i_status, i_images = await fetch_player_images(session, account_id)

        info = info_dict.get(account_id, {})
        
        username = info.get("username", "N/A")
        display = info.get("displayName", "N/A")
        junior = "Yes" if info.get("isJunior") else "No"
        platforms = info.get("platforms", 0)
        pronouns = info.get("personalPronouns", 0)
        created = info.get("createdAt", "N/A")[:10] if info.get("createdAt") else "N/A"
        subs = s_data if s_data is not None else "N/A"
        
        if isinstance(b_data, dict):
            bio_text = b_data.get("bio") or ""
        else:
            bio_text = ""
        bio_preview = (bio_text[:25] + "..") if len(bio_text) > 25 else bio_text
        bio_preview = bio_preview.replace("\n", " ")

        img_count = len(i_images) if isinstance(i_images, list) else 0
        latest_img = "N/A"
        if img_count > 0:
            first_img = i_images
            if isinstance(first_img, dict):
                latest_desc = first_img.get("Description") or "No Desc"
                latest_img = (latest_desc[:15] + "..") if len(latest_desc) > 15 else latest_desc
                latest_img = latest_img.replace("\n", " ")

        row = [
            account_id, username, display, junior, 
            platforms, pronouns, created, subs, img_count, latest_img, bio_preview
        ]
        
        result = {
            "id": account_id,
            "info": info if info else None,
            "bio": b_data, 
            "subs": s_data,
            "images": i_images
        }
        
        return result, row

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    full_table = []
    base_folder = "archive_data"
    
    headers = [
        "ID", "Username", "Display Name", "Jr", 
        "Plat", "Pronoun", "Created", "Subs", "Imgs", "Latest", "Bio Preview"
    ]

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for i in range(START_ID, END_ID + 1, BATCH_SIZE):
            batch_ids = list(range(i, min(i + BATCH_SIZE, END_ID + 1)))
            
            print(f"\n--- Processing Batch {i} to {batch_ids[-1]} ---")
            info_status, info_map = await fetch_bulk_info(session, batch_ids)

            tasks = [fetch_remaining_data(session, aid, info_map, semaphore) for aid in batch_ids]
            batch_output = await asyncio.gather(*tasks)

            for res_dict, row in batch_output:
                info = res_dict.get("info")
                username = info.get("username", "N/A") if info else "N/A"
                
                full_table.append(row)

                if username != "N/A":
                    save_to_folders(base_folder, res_dict)
            
            print(tabulate(full_table[-len(batch_ids):], headers=headers, tablefmt="grid"))

            if i + BATCH_SIZE <= END_ID:
                print(f"Sleeping {SLEEP_BETWEEN_BATCHES}s...")
                await asyncio.sleep(SLEEP_BETWEEN_BATCHES)

    print("Finished!")

if __name__ == "__main__":
    asyncio.run(main())