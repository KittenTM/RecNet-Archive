async def fetch_bulk_info(session, account_ids):
    query_params = "&".join([f"id={aid}" for aid in account_ids])
    url = f"https://accounts.rec.net/account/bulk?{query_params}"
    
    try:
        async with session.get(url, timeout=10) as response:
            status = response.status
            if status == 200:
                data = await response.json()
                return status, {item["accountId"]: item for item in data}
            return status, {}
    except Exception as e:
        print(f"Bulk Info Error: {e}")
        return 500, {}
    
""" https://accounts.rec.net/account/bulk?id=895160593&id=845216236
# works as in multiple act IDS, returns in json the following:
[
  {
    "accountId": 845216236,
    "username": "NachoMan223",
    "displayName": "Alfredo.Zulu",
    "profileImage": "axu9plrgbqfdy4n8vy38fkxjc.jpg",
    "bannerImage": "bopbog5qhzf0di5ob3d5kicy5.jpg",
    "isJunior": false,
    "platforms": 68,
    "personalPronouns": 2,
    "identityFlags": 0,
    "createdAt": "2023-07-17T02:15:45.2664212Z",
    "isMetaPlatformBlocked": false
  },
  {
    "accountId": 895160593,
    "username": "Sophiafay83",
    "displayName": "..SOPHIA...",
    "profileImage": "e8pazmohcyx5i85zb6tkut979.jpg",
    "bannerImage": "d9qoglz4w0tolt3osqgp3bu2z.jpg",
    "isJunior": false,
    "platforms": 578,
    "personalPronouns": 1,
    "identityFlags": 0,
    "createdAt": "2024-01-14T03:22:59.8348501Z",
    "isMetaPlatformBlocked": false
  }
]
"""