async def fetch_player_images(session, account_id):
    url = f"https://apim.rec.net/apis/api/images/v4/player/{account_id}"
    try:
        async with session.get(url, timeout=10) as response:
            status = response.status
            data = await response.json() if status == 200 else []
            return status, data
    except Exception as e:
        print(f"[ID {account_id}] Image Connection Error: {e}")
        return 500, []