import os
import re
import shutil

def main():
    chat_dir = 'chatwhatssap'
    chat_file = os.path.join(chat_dir, '_chat.txt')
    dest_base = 'fotosjoias'
    index_file = 'index.html'

    if not os.path.exists(chat_file):
        print(f"Erro: Arquivo {chat_file} não encontrado.")
        return

    with open(chat_file, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\n')
    current_category = 'nariz'
    items = []

    # Map category names to folder names and HTML categories
    # Folder names: Boca, Nariz, Orelha, corpo, facial
    # HTML category keys: boca, nariz, orelha, corpo, facial
    category_map = {
        'nariz': {'folder': 'Nariz', 'key': 'nariz'},
        'corpo': {'folder': 'corpo', 'key': 'corpo'},
        'facial': {'folder': 'facial', 'key': 'facial'},
        'boca': {'folder': 'Boca', 'key': 'boca'},
        'orelha': {'folder': 'Orelha', 'key': 'orelha'}
    }

    # Ensure folders exist
    for cat, info in category_map.items():
        os.makedirs(os.path.join(dest_base, info['folder']), exist_ok=True)

    print("Iniciando leitura do arquivo de chat...")

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
        
        # Check category updates in message body
        if 'Essas são de nariz' in msg_body:
            current_category = 'nariz'
            print(f"Linha {idx+1}: Categoria mudou para NARIZ")
        elif 'Daqui pra baixo, todas corporais' in msg_body or 'Essas são corporais' in msg_body:
            current_category = 'corpo'
            print(f"Linha {idx+1}: Categoria mudou para CORPO")
        elif 'Esses são faciais' in msg_body:
            current_category = 'facial'
            print(f"Linha {idx+1}: Categoria mudou para FACIAL")
        elif msg_body.strip().lower() == 'boca':
            current_category = 'boca'
            print(f"Linha {idx+1}: Categoria mudou para BOCA")
        elif 'Orelha esses últimos' in msg_body or msg_body.strip().lower() == 'orelha':
            current_category = 'orelha'
            print(f"Linha {idx+1}: Categoria mudou para ORELHA")
            
        # Match pattern: Código [número] - [nome] - R$ [preço]
        # Wait, some prices are like "R$ 120 a 150" or "R$ 180 á 230" or "R$ 110"
        # We want to capture the price properly.
        match = re.search(r'Código\s*(\d+)\s*-\s*(.*?)\s*-\s*R\$\s*([\d,\s\-a-zÀ-ÿáàéèíìóòúù\s]+?)(?=\s*(?:\(apenas|\/|R\$|<attached:|$))', msg_body, re.IGNORECASE)
        if match:
            code, name, price = match.groups()
            
            # Clean price string
            price_val = price.lower().replace('apenas joia', '').replace('apenas jia', '').replace('apenas joa', '').strip()
            # If price has a range (e.g. '120 a 150'), keep it as range but clean it up
            # Otherwise if it is just a number like '110', convert to '110,00'
            price_val = re.sub(r'\s+', ' ', price_val) # normalize spaces
            # If it's a range like '180 á 230', format as '180,00 a 230,00' or keep simple
            # Let's write a small helper to format prices
            def clean_single_price(p):
                p = re.sub(r'[^\d,]', '', p)
                if not p:
                    return ""
                if ',' not in p:
                    p += ',00'
                return p

            # If it is a range like '120 a 150' or '180 á 230'
            if ' a ' in price_val or ' á ' in price_val or ' à ' in price_val:
                parts = re.split(r'\s*(?:a|á|à)\s*', price_val)
                p1 = clean_single_price(parts[0])
                p2 = clean_single_price(parts[1]) if len(parts) > 1 else ""
                if p2:
                    price_str = f"R$ {p1} a R$ {p2}"
                else:
                    price_str = f"R$ {p1}"
            else:
                p_clean = clean_single_price(price_val)
                price_str = f"R$ {p_clean}"

            # Check attachment
            attach_match = re.search(r'<attached:\s*(.*?)\s*>', msg_body)
            filename = attach_match.group(1).strip() if attach_match else None
            
            if filename:
                items.append({
                    'code': code,
                    'name': name.strip(),
                    'price': price_str,
                    'category': current_category,
                    'filename': filename
                })

    print(f"Total de itens válidos encontrados no chat: {len(items)}")

    # We will copy the files and prepare the new jewelryData list
    new_jewelry_data = []
    copied_count = 0

    for item in items:
        src_path = os.path.join(chat_dir, item['filename'])
        if not os.path.exists(src_path):
            print(f"Aviso: Imagem {src_path} não encontrada no diretório chatwhatssap.")
            continue
            
        # Target folder and filename
        cat_info = category_map[item['category']]
        dest_folder = os.path.join(dest_base, cat_info['folder'])
        
        # Clean target filename to use the code or original name
        # We can rename to code + original filename for safety and uniqueness
        # E.g. '2145-IMG_3816.png'
        orig_name_clean = item['filename'].split('-', 1)[-1] if '-' in item['filename'] else item['filename']
        # Ensure it has .png or .jpg correctly
        dest_filename = f"{item['code']}-{orig_name_clean}"
        dest_path = os.path.join(dest_folder, dest_filename)
        
        try:
            shutil.copy2(src_path, dest_path)
            copied_count += 1
        except Exception as e:
            print(f"Erro ao copiar {src_path} para {dest_path}: {e}")
            continue

        # Determine material keyword
        name_lower = item['name'].lower()
        material = 'aco' # default
        if 'titânio' in name_lower or 'titanio' in name_lower:
            material = 'titanio'
        elif 'ouro' in name_lower:
            material = 'ouro'
        elif 'prata' in name_lower:
            material = 'prata'

        # Format name beautifully (Capitalize first letter)
        formatted_name = item['name'][0].upper() + item['name'][1:] if item['name'] else ""

        new_jewelry_data.append({
            'id': int(item['code']),
            'name': formatted_name,
            'price': item['price'],
            'category': cat_info['key'],
            'material': material,
            'img': f"fotosjoias/{cat_info['folder']}/{dest_filename}",
            'code': f"#{item['code']}"
        })

    print(f"Imagens copiadas e organizadas: {copied_count}")

    # Now we need to update index.html
    # Read index.html
    with open(index_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find the jewelryData array inside the script
    # Pattern: const jewelryData = [ ... ];
    # Let's replace the whole jewelryData array
    # Since jewelryData is defined as:
    # const jewelryData = [
    #   ...
    # ].map((item, idx) => ({ ... }));
    
    # We will format the list in JavaScript format
    js_items = []
    for item in new_jewelry_data:
        js_line = f"      {{ id: {item['id']}, name: \"{item['name']}\", price: \"{item['price']}\", category: \"{item['category']}\", material: \"{item['material']}\", img: \"{item['img']}\", code: \"{item['code']}\" }}"
        js_items.append(js_line)
        
    js_array_content = ",\n".join(js_items)
    
    # We will search for jewelryData array definition and replace it
    jewelry_data_pattern = r'(const\s+jewelryData\s*=\s*\[)(.*?)(\]\.map\((?:item|idx))'
    # Wait, let's use a simpler replacement or check index.html layout
    
    # Let's find index.html's exact jewelryData array using regex and substitute it
    # We'll use re.DOTALL to match multiline
    match = re.search(r'const\s+jewelryData\s*=\s*\[.*?\]\.map', html_content, re.DOTALL)
    if not match:
        print("Erro: Não foi possível localizar a definição de jewelryData em index.html")
        return
        
    replacement_string = f"const jewelryData = [\n{js_array_content}\n    ].map"
    
    updated_html = re.sub(r'const\s+jewelryData\s*=\s*\[.*?\]\.map', replacement_string, html_content, flags=re.DOTALL)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    print("index.html atualizado com sucesso!")
    print(f"Total de {len(new_jewelry_data)} joias importadas para o catálogo.")

if __name__ == '__main__':
    main()
