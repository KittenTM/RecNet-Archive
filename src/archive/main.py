import asyncio
import aiohttp
import json
from tabulate import tabulate

from profiles.bio import fetch_bio
from profiles.subscriberCount import fetch_subscriber_count
from profiles.info import fetch_bulk_info 

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

async def fetch_remaining_data(session, account_id, info_dict, semaphore):
    async with semaphore:
        b_status, b_data = await fetch_bio(session, account_id)
        s_status, s_data = await fetch_subscriber_count(session, account_id)

        info = info_dict.get(account_id, {})
        
        username = info.get("username", "N/A")
        display = info.get("displayName", "N/A")
        junior = "Yes" if info.get("isJunior") else "No"
        platforms = info.get("platforms", 0)
        pronouns = info.get("personalPronouns", 0)
        created = info.get("createdAt", "N/A")[:10] if info.get("createdAt") else "N/A"
        subs = s_data if s_data is not None else "N/A"

        bio_text = b_data.get("bio", "") if isinstance(b_data, dict) else ""
        bio_preview = (bio_text[:25] + "..") if len(bio_text) > 25 else bio_text
        bio_preview = bio_preview.replace("\n", " ")

        row = [
            account_id, username, display, junior, 
            platforms, pronouns, created, subs, bio_preview
        ]
        
        result = {
            "id": account_id,
            "info": info if info else None,
            "bio": b_data, 
            "subs": s_data
        }
        
        return result, row

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    all_results = []
    full_table = []
    
    headers = [
        "ID", "Username", "Display Name", "Jr", 
        "Plat", "Pronoun", "Created", "Subs", "Bio Preview"
    ]

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for i in range(START_ID, END_ID + 1, BATCH_SIZE):
            batch_ids = list(range(i, min(i + BATCH_SIZE, END_ID + 1)))
            
            print(f"\n--- Processing Batch {i} to {batch_ids[-1]} ---")
            info_status, info_map = await fetch_bulk_info(session, batch_ids)

            tasks = [fetch_remaining_data(session, aid, info_map, semaphore) for aid in batch_ids]
            batch_output = await asyncio.gather(*tasks)

            for res_dict, row in batch_output:
                all_results.append(res_dict)
                full_table.append(row)
            
            print(tabulate(full_table[-len(batch_ids):], headers=headers, tablefmt="grid"))

            if i + BATCH_SIZE <= END_ID:
                print(f"Sleeping {SLEEP_BETWEEN_BATCHES}s...")
                await asyncio.sleep(SLEEP_BETWEEN_BATCHES)

    with open("archive.json", "w") as f:
        json.dump(all_results, f, indent=4)
    
    print(f"\nFinished! Total accounts archived: {len(all_results)}")

if __name__ == "__main__":
    asyncio.run(main())