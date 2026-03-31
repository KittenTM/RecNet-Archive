import asyncio
import aiohttp
import json
from tabulate import tabulate
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import recnetpy

from profiles.bio import fetch_bio
from profiles.subscriberCount import fetch_subscriber_count

# recnet no api key ratelimits
MAX_CONCURRENT_REQUESTS = 20
BATCH_SIZE = 20
SLEEP_BETWEEN_BATCHES = 11
START_ID = 0
END_ID = 50

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://rec.net/",
    "Origin": "https://rec.net",
}

async def fetch_account(session, account_id, semaphore):
    async with semaphore:
        b_status, b_data = await fetch_bio(session, account_id)
        s_status, s_data = await fetch_subscriber_count(session, account_id)

        row = [account_id, b_status, s_status, s_data if s_data is not None else "N/A"]
        
        if b_status == 429 or s_status == 429:
            return "RATE_LIMIT", row

        return {"id": account_id, "bio": b_data, "subs": s_data}, row

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    all_results = []
    table_data = []
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for i in range(START_ID, END_ID + 1, BATCH_SIZE):
            batch_end = min(i + BATCH_SIZE, END_ID + 1)
            tasks = [fetch_account(session, account_id, semaphore) for account_id in range(i, batch_end)]
            
            batch_output = await asyncio.gather(*tasks)
            
            for result, row in batch_output:
                table_data.append(row)
                if result != "RATE_LIMIT":
                    all_results.append(result)
            
            print(f"\n--- Batch {i} to {batch_end-1} Complete ---")
            print(tabulate(table_data[-BATCH_SIZE:], 
                           headers=["Account ID", "Bio Status", "Sub Status", "Subs"], 
                           tablefmt="grid"))
            
            if batch_end <= END_ID:
                print(f"Sleeping {SLEEP_BETWEEN_BATCHES}s...")
                await asyncio.sleep(SLEEP_BETWEEN_BATCHES)

    print("\n" + "="*50)
    print("FINAL SCRAPE SUMMARY")
    print("="*50)
    print(tabulate(table_data, headers=["ID", "Bio", "Sub", "Count"], tablefmt="pretty"))

    # todo: rewrite to use psql
    with open("archive.json", "w") as f:
        json.dump([r for r in all_results if isinstance(r, dict)], f, indent=4)
    
    print(f"\nFinished! Data saved to archive.json")

if __name__ == "__main__":
    asyncio.run(main())