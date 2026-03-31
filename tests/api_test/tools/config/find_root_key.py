import os
import subprocess

import atom_ctx

print("Searching for root_api_key in AtomCtx code...")

# Find where atom_ctx is installed

atom_ctx_path = os.path.dirname(atom_ctx.__file__)
print(f"AtomCtx path: {atom_ctx_path}")

# Search for root_api_key in the code
print("\nSearching in atom_ctx package...")
try:
    result = subprocess.run(
        ["grep", "-r", "root_api_key", atom_ctx_path], capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("No matches in atom_ctx package")
except Exception as e:
    print(f"Error searching: {e}")

# Also check atom_ctx_cli
try:
    import atom_ctx_cli

    cli_path = os.path.dirname(atom_ctx_cli.__file__)
    print(f"\nAtomCtx CLI path: {cli_path}")
    print("\nSearching in atom_ctx_cli package...")
    result = subprocess.run(
        ["grep", "-r", "root_api_key", cli_path], capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("No matches in atom_ctx_cli package")
except Exception as e:
    print(f"Error searching CLI: {e}")

# Also search for "Admin API requires" to find where that error is coming from
print("\n" + "=" * 80)
print("Searching for error message...")
try:
    result = subprocess.run(
        ["grep", "-r", "Admin API requires", atom_ctx_path], capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("No matches for error message")
except Exception as e:
    print(f"Error searching error message: {e}")
