async def fetch_subscriber_count(session, account_id):
    url = f"https://clubs.rec.net/subscription/subscriberCount/{account_id}"
    try:
        async with session.get(url, timeout=10) as response:
            status = response.status
            data = await response.json() if status == 200 else None
            return status, data
    except Exception as e:
        print(f"[ID {account_id}] Sub Connection Error: {e}")
        return 500, None