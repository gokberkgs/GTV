import re
import os

# `listem` dosyasını oku
def read_listem():
    listem = []
    excluded = set()
    try:
        with open('listem', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Numarayı ve olası `(-)` işaretini kaldır
                    match = re.match(r'(\d+\.)?(.+?)(?:\s*\(-\))?$', line)
                    if match:
                        name = match.group(2).strip()
                        listem.append(name)
                        if '(-)' in line:
                            excluded.add(name)
    except FileNotFoundError:
        pass
    return listem, excluded

# M3U dosyasını oku ve kanalları ayrıştır
def parse_m3u(file_path):
    channels = []
    current_channel = None
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#EXTM3U'):
                channels.append(line)  # EPG satırını koru
            elif line.startswith('#EXTINF'):
                match = re.search(r'tvg-id="([^"]+)"', line)
                name_match = re.search(r',(.+)$', line)
                if match and name_match:
                    tvg_id = match.group(1)
                    name = name_match.group(1).strip()
                    current_channel = {'tvg_id': tvg_id, 'extinf': line, 'name': name}
            elif line and current_channel:
                current_channel['url'] = line
                channels.append(current_channel)
                current_channel = None
    return channels

# Kanalları sırala ve yeni/sıralama dışı kanalları ekle
def sort_channels(channels, listem, excluded):
    sorted_channels = []
    new_listem = listem.copy()
    used_names = set()
    next_index = len(listem) + 1 if listem else 1

    # `listem` sırasına göre kanalları ekle (hariç tutulanlar hariç)
    for name in listem:
        if name not in excluded:
            for channel in channels:
                if isinstance(channel, dict) and channel['name'] == name:
                    sorted_channels.append(channel)
                    used_names.add(name)
                    break

    # Sıralama dışı ve yeni kanalları ekle
    for channel in channels:
        if isinstance(channel, dict) and channel['name'] not in used_names and channel['name'] not in excluded:
            sorted_channels.append(channel)
            if channel['name'] not in listem:
                new_listem.append(f"{next_index}.{channel['name']} [Yeni Kanal]")
                next_index += 1
            else:
                new_listem.append(f"{next_index}.{channel['name']} [Sıralama Dışı]")
                next_index += 1
            used_names.add(channel['name'])

    # EPG satırını başa ekle
    result = [channels[0]] if channels and isinstance(channels[0], str) else []
    for channel in sorted_channels:
        result.append(channel['extinf'])
        result.append(channel['url'])

    # Yeni `listem` içeriğini formatla
    formatted_listem = []
    for item in new_listem:
        if item in listem and item not in excluded:
            # Mevcut sıralı kanalları koru
            formatted_listem.append(f"{listem.index(item) + 1}.{item}")
        elif item in excluded:
            # Hariç tutulan kanalları `(-)` ile koru
            formatted_listem.append(f"{listem.index(item) + 1}.{item} (-)")
        else:
            # Yeni veya sıralama dışı kanalları ekle
            formatted_listem.append(item)

    return result, formatted_listem

# M3U dosyasını yaz
def write_m3u(channels, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in channels:
            f.write(f"{item}\n")

# `listem` dosyasını yaz
def write_listem(listem):
    with open('listem', 'w', encoding='utf-8') as f:
        for item in listem:
            f.write(f"{item}\n")

# Ana işlem
def main():
    listem, excluded = read_listem()
    channels = parse_m3u('temp.m3u')
    sorted_channels, new_listem = sort_channels(channels, listem, excluded)
    write_m3u(sorted_channels, 'gtv.m3u')
    write_listem(new_listem)

if __name__ == "__main__":
    main()
