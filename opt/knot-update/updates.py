import requests
import re
import time
import shutil
import os
from concurrent.futures import ThreadPoolExecutor

# --- Konfigurasi ---
url = "https://trustpositif.komdigi.go.id/assets/db/domains_isp"
output_file_rpz = "/dev/shm/kresd-rpz/xdomains.rpz"
output_file_csv = "/dev/shm/kresd-rpz/xdomains.csv"
xip_address = "xblock.gmedia.id"
backup_dir = "/opt/knot-update/"

# --- Regex untuk validasi domain ---
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.[A-Za-z]{2,}$"
)

# --- Fungsi Validasi Domain ---
def is_valid_domain(domain):
    return DOMAIN_RE.match(domain) is not None

# --- Baca RPZ Lama ---
def load_existing_rpz(path):
    existing = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 1:
                    existing.add(parts[0])
    return existing

# --- Sinkronisasi File RPZ ---
def sync_rpz_file(file_path, ip_address, domains_new):
    existing_domains = load_existing_rpz(file_path)
    domains_new_set = set(domains_new)

    domains_to_add = domains_new_set - existing_domains
    domains_to_remove = existing_domains - domains_new_set

    if domains_to_add or domains_to_remove:
        print(f"Updating RPZ: +{len(domains_to_add)} new, -{len(domains_to_remove)} removed")
        with open(file_path, 'w') as f:
            for domain in sorted(domains_new_set):
                f.write(f"{domain} CNAME {ip_address}\n")
    else:
        print("RPZ already up to date, no changes needed.")

# --- Tulis File CSV (Optional) ---
def write_csv_file(file_path, ip_address, domains):
    with open(file_path, 'w') as outfile:
        for domain in sorted(domains):
            outfile.write(f"{domain},CNAME,{ip_address}\n")

# --- Pastikan Direktori Backup Ada ---
def ensure_backup_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

# --- Main ---
def main():
    start_time = time.time()
    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch domain list: {e}")
        return

    cleaned_domains = set()

    for line in response.iter_lines():
        if line:
            domain = line.decode('utf-8').strip().replace(" ", "")
            if is_valid_domain(domain):
                cleaned_domains.add(domain)
            else:
                print(f"[INVALID] {domain}")

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(sync_rpz_file, output_file_rpz, xip_address, cleaned_domains)
        executor.submit(write_csv_file, output_file_csv, xip_address, cleaned_domains)

    # Backup
    ensure_backup_dir(backup_dir)
    shutil.copy2(output_file_rpz, os.path.join(backup_dir, "xdomains.rpz"))
    shutil.copy2(output_file_csv, os.path.join(backup_dir, "xdomains.csv"))

    end_time = time.time()
    print(f"Domain list processed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
