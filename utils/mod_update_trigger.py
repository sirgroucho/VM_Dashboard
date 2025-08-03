import subprocess

def send_update_to_homelab(version):
    try:
        # Example using SSH over Tailscale
        subprocess.run(
            ["ssh", "user@100.x.x.x", f"/home/user/apply_modpack.sh {version}"],
            check=True
        )
        return True
    except Exception as e:
        print(f"Update failed: {e}")
        return False
