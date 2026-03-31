auth_path = "/usr/local/lib/python3.11/site-packages/atom_ctx/server/auth.py"
print(f"Reading {auth_path}...")
print("=" * 80)

with open(auth_path, "r") as f:
    print(f.read())
