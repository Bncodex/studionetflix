import os
import re
import shutil
from PIL import Image

def get_image_signature(img_path, size=10):
    try:
        with Image.open(img_path) as img:
            img_resized = img.convert('L').resize((size, size), Image.Resampling.BILINEAR)
            pixels = list(img_resized.getdata())
            avg = sum(pixels) / len(pixels)
            return pixels, avg
    except Exception as e:
        return None, None

def get_pixel_distance(sig1, sig2):
    pixels1, avg1 = sig1
    pixels2, avg2 = sig2
    if not pixels1 or not pixels2:
        return 999999
    diff = 0
    for p1, p2 in zip(pixels1, pixels2):
        n1 = p1 - avg1
        n2 = p2 - avg2
        diff += abs(n1 - n2)
    return diff / len(pixels1)

def main():
    chat_file = 'chatwhatssap/_chat.txt'
    chat_dir = 'chatwhatssap'
    dest_base = 'fotosjoias'
    index_file = 'index.html'

    category_keys = {
        'Orelha': 'orelha',
        'Nariz': 'nariz',
        'Boca': 'boca',
        'corpo': 'corpo',
        'facial': 'facial'
    }

    chat_to_folder = {
        'nariz': 'Nariz',
        'orelha': 'Orelha',
        'boca': 'Boca',
        'corpo': 'corpo',
        'facial': 'facial'
    }

    # 1. Build database of sorted files
    sorted_files = {}
    for root, dirs, files in os.walk(dest_base):
        subfolder = os.path.basename(root)
        if subfolder in category_keys:
            for f in files:
                if re.match(r'^\d+-', f):
                    continue
                f_lower = f.lower()
                if f_lower not in sorted_files:
                    sorted_files[f_lower] = []
                sorted_files[f_lower].append(subfolder)

    print(f"Banco de dados de fotos ordenadas: {len(sorted_files)} arquivos unicos.")

    # 2. Parse descriptions
    if not os.path.exists(chat_file):
        print(f"Erro: {chat_file} nao encontrado.")
        return

    with open(chat_file, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\n')
    descriptions = []

    for idx, line in enumerate(lines):
        line_clean = line.replace('\u200e', '').strip()
        bracket_idx = line_clean.find(']')
        if bracket_idx == -1:
            continue
        msg_part = line_clean[bracket_idx+1:].strip()
        colon_idx = msg_part.find(':')
        if colon_idx == -1:
            continue
        msg_body = msg_part[colon_idx+1:].strip()
        
        # Determine category based on line number
        line_num = idx + 1
        chat_cat = None
        if 252 <= line_num <= 279:
            chat_cat = 'nariz'
        elif 282 <= line_num <= 329:
            chat_cat = 'corpo'
        elif 330 <= line_num <= 356:
            chat_cat = 'facial'
        elif 358 <= line_num <= 398:
            chat_cat = 'boca'
        elif 399 <= line_num <= 422:
            chat_cat = 'orelha'
            
        if chat_cat:
            match = re.search(r'Código\s*(\d+)\s*-\s*(.*?)\s*-\s*R\$\s*([\d,\s\-a-zÀ-ÿáàéèíìóòúù\s]+?)(?=\s*(?:\(apenas|\/|R\$|<attached:|$))', msg_body, re.IGNORECASE)
            if match:
                code, name, price = match.groups()
                attach_match = re.search(r'<attached:\s*(.*?)\s*>', msg_body)
                filename = attach_match.group(1).strip() if attach_match else None
                if filename:
                    descriptions.append({
                        'code': code,
                        'name': name.strip(),
                        'price_raw': price.strip(),
                        'filename': filename,
                        'chat_cat': chat_cat
                    })

    print(f"Carregados {len(descriptions)} itens do log de chat.")

    # 3. Find high-quality files in chatwhatssap
    hq_files = [f for f in os.listdir(chat_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and 'IMG_' in f]
    print(f"Pre-computando assinaturas de {len(hq_files)} originais...")
    hq_signatures = {}
    for f in hq_files:
        sig = get_image_signature(os.path.join(chat_dir, f))
        if sig[0] is not None:
            hq_signatures[f] = sig

    # Helper function to clean price
    def clean_price(price_raw):
        p_val = price_raw.lower().replace('apenas joia', '').replace('apenas jia', '').replace('apenas joa', '').strip()
        p_val = re.sub(r'\s+', ' ', p_val)
        
        def clean_single(p):
            p = re.sub(r'[^\d,]', '', p)
            if not p:
                return ""
            if ',' not in p:
                p += ',00'
            return p

        if ' a ' in p_val or ' á ' in p_val or ' à ' in p_val:
            parts = re.split(r'\s*(?:a|á|à)\s*', p_val)
            p1 = clean_single(parts[0])
            p2 = clean_single(parts[1]) if len(parts) > 1 else ""
            if p2:
                return f"R$ {p1} a R$ {p2}"
            else:
                return f"R$ {p1}"
        else:
            p_clean = clean_single(p_val)
            return f"R$ {p_clean}"

    # 4. Process each item, match, copy and generate JS data
    new_jewelry_data = []
    unique_entries = set() # (id, category)
    
    for item in descriptions:
        photo_path = os.path.join(chat_dir, item['filename'])
        
        if 'IMG_' in item['filename']:
            best_match_name = item['filename'].split('-', 1)[-1] if '-' in item['filename'] else item['filename']
            src_hq_path = os.path.join(chat_dir, item['filename'])
        else:
            photo_sig = get_image_signature(photo_path)
            if photo_sig[0] is None:
                print(f"Erro ao ler imagem {item['filename']} do codigo {item['code']}")
                continue
                
            best_match = None
            min_dist = 999999
            for f, sig in hq_signatures.items():
                dist = get_pixel_distance(photo_sig, sig)
                if dist < min_dist:
                    min_dist = dist
                    best_match = f
            
            if not best_match:
                print(f"Nenhum match original para o codigo {item['code']}")
                continue
                
            best_match_name = re.sub(r'^\d+-', '', best_match)
            src_hq_path = os.path.join(chat_dir, best_match)
            
        best_match_lower = best_match_name.lower()
        
        # Determine all categories for this item:
        # 1. From folders where the user sorted the image
        # 2. From the chat section category
        categories = set()
        folders = sorted_files.get(best_match_lower, [])
        for f in folders:
            categories.add(category_keys[f])
        categories.add(item['chat_cat'])

        # For each category, create a unique entry
        for cat in categories:
            entry_key = (int(item['code']), cat)
            if entry_key in unique_entries:
                continue
            unique_entries.add(entry_key)
            
            final_folder = chat_to_folder[cat]
            dest_filename = f"{item['code']}-{best_match_name}"
            dest_path = os.path.join(dest_base, final_folder, dest_filename)
            
            # Copy file to destination folder
            os.makedirs(os.path.join(dest_base, final_folder), exist_ok=True)
            try:
                shutil.copy2(src_hq_path, dest_path)
            except Exception as e:
                # Fallback to copy from the sorted location if source not in chatwhatssap
                copied = False
                for f_folder in folders:
                    fallback_src = os.path.join(dest_base, f_folder, best_match_name)
                    if os.path.exists(fallback_src):
                        shutil.copy2(fallback_src, dest_path)
                        copied = True
                        break
                if not copied:
                    print(f"Erro ao copiar {best_match_name} para {dest_path}: {e}")
                    continue

            # Material detection
            name_lower = item['name'].lower()
            material = 'aco'
            if 'titânio' in name_lower or 'titanio' in name_lower:
                material = 'titanio'
            elif 'ouro' in name_lower:
                material = 'ouro'
            elif 'prata' in name_lower:
                material = 'prata'

            formatted_name = item['name'][0].upper() + item['name'][1:] if item['name'] else ""
            formatted_price = clean_price(item['price_raw'])

            new_jewelry_data.append({
                'id': int(item['code']),
                'name': formatted_name,
                'price': formatted_price,
                'category': cat,
                'material': material,
                'img': f"fotosjoias/{final_folder}/{dest_filename}".replace('\\', '/'),
                'code': f"#{item['code']}"
            })

    print(f"Processados e copiados {len(new_jewelry_data)} arquivos de joias com sucesso.")

    # 5. Replace in index.html
    if not os.path.exists(index_file):
        print(f"Erro: {index_file} nao encontrado.")
        return

    with open(index_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    js_items = []
    # Sort new_jewelry_data by category then by id to keep it clean
    new_jewelry_data.sort(key=lambda x: (x['category'], x['id']))
    for item in new_jewelry_data:
        js_line = f'      {{ id: {item["id"]}, name: "{item["name"]}", price: "{item["price"]}", category: "{item["category"]}", material: "{item["material"]}", img: "{item["img"]}", code: "{item["code"]}" }}'
        js_items.append(js_line)
        
    js_array_content = ",\n".join(js_items)

    # Replace the array in index.html
    pattern = r'(const\s+jewelryData\s*=\s*\[)(.*?)(\]\.map\(\(item,\s*idx\)\s*=>\s*\({\s*\.\.\.item,\s*code:\s*item\.code\s*\|\|\s*`#\$\{213301\s*\+\s*idx\}`\s*}\)\);)'
    
    match = re.search(pattern, html_content, re.DOTALL)
    if not match:
        print("Erro: Nao foi possivel encontrar o padrao de const jewelryData em index.html")
        return

    replacement = f"const jewelryData = [\n{js_array_content}\n    ].map((item, idx) => ({{\n      ...item,\n      code: item.code || `#${{213301 + idx}}`\n    }}));"
    
    updated_html = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    print("index.html atualizado com sucesso!")
    print(f"Total de {len(new_jewelry_data)} joias importadas para o catalogo.")

if __name__ == '__main__':
    main()
