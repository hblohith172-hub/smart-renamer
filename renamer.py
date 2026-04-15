import os
import base64
import json
import argparse
import requests
from pathlib import Path

def analyze_image(path, model="batiai/gemma4-26b:iq4"):
    """Sends image to local Ollama for description."""
    try:
        with open(path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
        
        payload = {
            "model": model,
            "prompt": "Describe in 3 snake_case words for filename, reply ONLY the words",
            "stream": False,
            "images": [base64_image]
        }
        
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=10)
        response.raise_for_status()
        
        content = response.json().get("response", "").strip().lower()
        clean_content = "".join(c if c.isalnum() or c == '_' else '_' for c in content)
        clean_content = "_".join(filter(None, clean_content.split('_')))
        
        return clean_content if clean_content else None
    except Exception as e:
        print(f"Error analyzing {path}: {e}")
        return None

def safe_rename(directory, old_name, new_base):
    """Handles collisions and length limits."""
    ext = Path(old_name).suffix
    base_limit = 40 - len(ext)
    new_base = new_base[:base_limit].replace(" ", "_")
    
    target = directory / f"{new_base}{ext}"
    
    counter = 1
    while target.exists():
        suffix = f"_{counter}"
        new_name = f"{new_base[:base_limit-len(suffix)]}{suffix}{ext}"
        target = directory / new_name
        counter += 1
    return target

def undo_last(directory):
    """Reverts the last renaming session from undo.json."""
    log_path = directory / "undo.json"
    if not log_path.exists():
        print("No undo log found.")
        return

    with open(log_path, "r") as f:
        try:
            history = json.load(f)
        except:
            print("Error reading undo log.")
            return
    
    if not history:
        print("Undo history is empty.")
        return

    last_session = history.pop()
    print(f"Undoing {len(last_session)} changes...")
    
    for old_path, new_path in reversed(last_session):
        try:
            if os.path.exists(new_path):
                os.rename(new_path, old_path)
                print(f"Restored: {os.path.basename(old_path)}")
            else:
                print(f"Warning: {new_path} not found, can't revert.")
        except Exception as e:
            print(f"Failed to restore {new_path}: {e}")

    with open(log_path, "w") as f:
        json.dump(history, f)

def main():
    parser = argparse.ArgumentParser(description="AI-powered image renamer using local Gemma4")
    parser.add_argument("folder", type=str, help="Path to the folder containing images")
    parser.add_argument("--execute", action="store_true", help="Actually rename files")
    parser.add_argument("--undo", action="store_true", help="Revert last session")
    args = parser.parse_args()

    dir_path = Path(args.folder).expanduser().resolve()
    if not dir_path.is_dir():
        print(f"Error: {dir_path} is not a directory.")
        return

    if args.undo:
        undo_last(dir_path)
        return

    extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    files_to_process = [f for f in dir_path.iterdir() if f.suffix.lower() in extensions]
    files_to_process.sort()

    if not files_to_process:
        print("No matching images found.")
        return

    print(f"Found {len(files_to_process)} images. Starting analysis...")
    
    rename_tasks = []
    undo_entries = []

    for file_path in files_to_process:
        print(f"Analyzing: {file_path.name}...")
        description = analyze_image(str(file_path))
        
        if description:
            target_path = safe_rename(dir_path, file_path.name, description)
            rename_tasks.append((str(file_path), str(target_path)))
            print(f"  [PLAN] {file_path.name} -> {target_path.name}")
        else:
            print(f"  [SKIP] Could not generate description for {file_path.name}")

    if not rename_tasks:
        print("No valid images identified for renaming.")
        return

    if args.execute:
        print("\nExecuting renames...")
        for old, new in rename_tasks:
            try:
                os.rename(old, new)
                undo_entries.append([old, new])
                print(f"Renamed: {os.path.basename(old)} -> {os.path.basename(new)}")
            except Exception as e:
                print(f"Error renaming {old}: {e}")
        
        if undo_entries:
            log_path = dir_path / "undo.json"
            history = []
            if log_path.exists():
                with open(log_path, "r") as f:
                    try: history = json.load(f)
                    except: history = []
            
            history.append(undo_entries)
            with open(log_path, "w") as f:
                json.dump(history, f)
            print(f"Done. Session logged to undo.json")
    else:
        print("\nDRY RUN COMPLETE. Use --execute to apply changes.")
        print(f"{'OLD NAME':<30} | {'NEW NAME':<30}")
        print("-" * 65)
        for old, new in rename_tasks:
            print(f"{os.path.basename(old):<30} | {os.path.basename(new):<30}")

if __name__ == "__main__":
    main()
