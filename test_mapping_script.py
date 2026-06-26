import os
import re

def main():
    chat_file = 'chatwhatssap/_chat.txt'
    dest_base = 'fotosjoias'

    if not os.path.exists(chat_file):
        print(f"Erro: Arquivo {chat_file} não encontrado.")
        return

    with open(chat_file, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\n')
    items = []

    # Map subfolder names to category keys
    category_keys = {
        'Orelha': 'orelha',
        'Nariz': 'nariz',
        'Boca': 'boca',
        'corpo': 'corpo',
        'facial': 'facial'
    }

    # Build a dictionary of files currently in fotosjoias subfolders
    # Key: filename (lower), Value: (subfolder_name, relative_path)
    fotos_db = {}
    for root, dirs, files in os.walk(dest_base):
        subfolder = os.path.basename(root)
        if subfolder in category_keys:
            for f in files:
                # We can store key as filename in lowercase
                fotos_db[f.lower()] = (subfolder, os.path.join(root, f).replace('\\', '/'))

    print(f"Banco de dados local de fotos carregado: {len(fotos_db)} arquivos em fotosjoias.")

    unmatched = []
    matched = []

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
        
        # Match pattern: Código [número] - [nome] - R$ [preço]
        match = re.search(r'Código\s*(\d+)\s*-\s*(.*?)\s*-\s*R\$\s*([\d,\s\-a-zÀ-ÿáàéèíìóòúù\s]+?)(?=\s*(?:\(apenas|\/|R\$|<attached:|$))', msg_body, re.IGNORECASE)
        if match:
            code, name, price = match.groups()
            
            # Check attachment
            attach_match = re.search(r'<attached:\s*(.*?)\s*>', msg_body)
            filename = attach_match.group(1).strip() if attach_match else None
            
            if filename:
                # Strip prefix like '00000193-' to get the original name
                # E.g. '00000193-IMG_3816.png' -> 'IMG_3816.png'
                base_name = re.sub(r'^\d+-', '', filename).lower()
                # Also handle files named '00000287-PHOTO-2026-06-23-21-04-54.jpg' -> 'PHOTO-2026-06-23-21-04-54.jpg'
                
                # Check if this base name exists in our fotosjoias subfolders
                if base_name in fotos_db:
                    subfolder, rel_path = fotos_db[base_name]
                    matched.append({
                        'code': code,
                        'name': name.strip(),
                        'price': price.strip(),
                        'category': category_keys[subfolder],
                        'path': rel_path,
                        'filename': filename
                    })
                else:
                    unmatched.append((idx+1, code, base_name))

    print(f"Total de itens correspondidos: {len(matched)}")
    print(f"Total de itens não correspondidos: {len(unmatched)}")
    if unmatched:
        print("Alguns não correspondidos (primeiros 10):")
        for line_num, code, base_name in unmatched[:10]:
            print(f"Linha {line_num}: Código {code}, Nome base: {base_name}")

if __name__ == '__main__':
    main()
