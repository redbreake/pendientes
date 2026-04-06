import pandas as pd
import json
import os
import re

def clean_filename(filename):
    # Remove invalid characters for filenames
    return re.sub(r'[\\/*?:"<>|]', "", str(filename)).strip()

def find_image_for_anime(image_folder, anime_name):
    """
    Looks for an image file in the folder that matches the anime name (case-insensitive).
    Supported extensions: .png, .jpg, .jpeg, .webp, .gif
    """
    if not os.path.exists(image_folder):
        return None
    
    name_to_find = clean_filename(anime_name).lower()
    extensions = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.PNG', '.JPG', '.JPEG']
    
    # Priority 1: Exact name match (case-insensitive)
    for f in os.listdir(image_folder):
        name_only, ext = os.path.splitext(f)
        if name_only.lower() == name_to_find and ext in extensions:
            return f"imagenes/{f}"
            
    # Priority 2: Partial match if name is long (optional, but let's keep it exact for now)
    
    return None

def excel_to_json(input_file, output_json, image_folder):
    print(f"Reading {input_file}...")
    
    try:
        # Read Excel
        df = pd.read_excel(input_file)
        
        animes = []
        for index, row in df.iterrows():
            raw_name = row['Unnamed: 1']
            if pd.isna(raw_name):
                continue
                
            name = str(raw_name).strip()
            
            # Format episode
            current_ep = row['Unnamed: 2']
            if pd.isna(current_ep):
                current_ep = "N/A"
            else:
                if isinstance(current_ep, float) and current_ep.is_integer():
                    current_ep = int(current_ep)
                else:
                    current_ep = str(current_ep).strip()

            # Format purchased
            purchased = row['COMPRADOS']
            if pd.isna(purchased):
                purchased = 0
            elif isinstance(purchased, str):
                purchased = purchased.strip()
            elif isinstance(purchased, float) and purchased.is_integer():
                purchased = int(purchased)
            else:
                purchased = str(purchased).strip()

            # Match image by NAME in the folder
            image_path = find_image_for_anime(image_folder, name)
            
            if image_path:
                print(f"✓ Found image for: {name} -> {image_path}")
            else:
                print(f"✗ No image found for: {name} (expected {clean_filename(name)}.png in {image_folder})")

            animes.append({
                "name": name,
                "current_episode": current_ep,
                "purchased": purchased,
                "image": image_path
            })
        
        # Save JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(animes, f, ensure_ascii=False, indent=2)
            
        print(f"\nDone! Processed {len(animes)} animes.")
        print(f"Data saved to {output_json}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # We no longer extract images automatically inside this script to keep it simple.
    # The user can manage the 'imagenes' folder manually.
    excel_to_json('ANIMES KALA.xlsx', 'data.json', 'imagenes')
