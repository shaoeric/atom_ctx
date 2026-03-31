app_path = "/usr/local/lib/python3.11/site-packages/atom_ctx/server/app.py"
print(f"Reading {app_path}...")
print("=" * 80)

with open(app_path, "r") as f:
    print(f.read())
