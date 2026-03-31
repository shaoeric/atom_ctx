# Let's look at the admin router
admin_path = "/usr/local/lib/python3.11/site-packages/atom_ctx/server/routers/admin.py"
print(f"Reading {admin_path}...")
print("=" * 80)

with open(admin_path, "r") as f:
    print(f.read())
