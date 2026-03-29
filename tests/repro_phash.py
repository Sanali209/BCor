import os
import hashlib
import imagehash
from PIL import Image
from dataclasses import dataclass

@dataclass
class PhashMatch:
    file1: str
    file2: str
    distance: int
    content_match: bool

def compute_phash(path: str) -> str:
    try:
        with open(path, "rb") as f:
            with Image.open(f) as img:
                return str(imagehash.phash(img))
    except Exception as e:
        return None

def compute_content_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def run_test():
    root = "D:/image_db/safe repo/ddsearch/kim_possible"
    files = [os.path.join(root, f) for f in os.listdir(root) if f.endswith(('.webp', '.jpg', '.png'))]
    
    hashes = {}
    content_hashes = {}
    print(f"Computing hashes for {len(files)} files...")
    for f in files:
        ph = compute_phash(f)
        ch = compute_content_hash(f)
        if ph:
            hashes[f] = ph
            content_hashes[f] = ch
        
    threshold = 15 # Increased threshold
    matches = []
    
    print(f"\nComparing hashes (threshold={threshold}):")
    file_list = list(hashes.keys())
    for i in range(len(file_list)):
        for j in range(i + 1, len(file_list)):
            f1, f2 = file_list[i], file_list[j]
            h1, h2 = hashes[f1], hashes[f2]
            
            # Hamming distance
            dist = imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)
            
            if dist <= threshold:
                matches.append(PhashMatch(
                    file1=os.path.basename(f1),
                    file2=os.path.basename(f2),
                    distance=dist,
                    content_match=(content_hashes[f1] == content_hashes[f2])
                ))
                
    print("\nResults:")
    if not matches:
        print("No duplicates or similar images found in the dataset.")
    else:
        # Sort by distance
        matches.sort(key=lambda x: x.distance)
        for m in matches:
            label = "EXACT" if m.content_match else ("DUPLICATE" if m.distance <= 5 else "SIMILAR")
            print(f"[{label}] {m.file1} <-> {m.file2} | Distance: {m.distance}")
        
    print("\nParameters for finding duplicates:")
    print("1. Engine: perceptual_hash (pHash)")
    print("2. Hash Size: 8x8 (default)")
    print(f"3. Threshold Used: {threshold}")
    print("4. Suggested Thresholds:")
    print("   - 0-2: Exact or near-exact duplicates")
    print("   - 3-8: Visually very similar")
    print("   - 10-15: Same scene / similar composition")

if __name__ == "__main__":
    run_test()
