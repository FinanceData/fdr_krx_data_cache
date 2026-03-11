import traceback
try:
    from krx_auth import login
    from collectors import collect_listing_desc
    login()
    df = collect_listing_desc("KRX")
    with open("success.txt", "w", encoding="utf-8") as f:
        f.write(f"count: {len(df)}\n")
        f.write(str(df.head()))
except Exception as e:
    with open("error.txt", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
