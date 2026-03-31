async def fetch_bio(session, account_id):
    url = f"https://apim.rec.net/accounts/account/{account_id}/bio"
    try:
        async with session.get(url, timeout=10) as response:
            status = response.status
            data = await response.json() if status == 200 else None
            return status, data
    except Exception as e:
        print(f"[ID {account_id}] Bio Connection Error: {e}")
        return 500, None