# Promo regału: przeniesienie renderu i muzyki na Maca

Cel: finalny render w Blenderze na GPU Maca, praca przez oficjalny Blender MCP (Blender Lab), muzyka z fal.ai z kluczem trzymanym na Macu.

## 1. Remote Control (żeby sesja w chmurze mogła działać na Macu)
1. Folder roboczy musi być katalogiem głównym repo git (nie w ukrytym folderze ani w `~/Library`). Najprościej:
   `git clone https://github.com/piotrbugaj-tech/cnc-ai-office ~/Projekty/cnc-ai-office && cd ~/Projekty/cnc-ai-office && git checkout claude/shelf-storage-furniture-design-64l18y`
2. Claude Desktop → Settings → Claude Code → Remote Control → dodaj ten folder. Zamiast tego możesz w tym folderze uruchomić `claude remote-control`.
3. Zostaw Maca włączonego z uruchomioną aplikacją Claude.

## 2. Blender + oficjalny MCP (Blender Lab)
- Wymagany Blender **5.1 lub nowszy** (sprawdź: `/Applications/Blender.app/Contents/MacOS/Blender --version`).
- Dodatek MCP pobierasz ze strony Blender Lab: https://www.blender.org/lab/mcp-server/ (repo: projects.blender.org/lab/blender_mcp). Instalacja: przeciągnij ZIP do okna Blendera albo Preferences → Add-ons → Install from Disk, potem włącz dodatek i uruchom serwer w jego ustawieniach.
- Serwer MCP Blender Lab jest typu stdio: uruchamia go klient (Claude Code / Claude Desktop) zgodnie z instrukcją na stronie Blender Lab. Narzędzia MCP są dostępne w sesji Claude uruchomionej na Macu z tym serwerem w konfiguracji.
- Niezależnie od MCP te same sceny da się wyrenderować bez GUI:
  `/Applications/Blender.app/Contents/MacOS/Blender -b -P projects/regal-nieregularny/promo/scene/<skrypt>.py -- <argumenty>`
  W Blenderze: Preferences → System → Cycles Render Devices → **Metal** (GPU Apple).

## 3. fal.ai (muzyka i ewentualnie efekty)
- Klucz trzymaj w zmiennej `FAL_KEY` (np. w pliku `.env` poza repo albo w `~/.zshrc`). **Nigdy nie wklejaj klucza do czatu ani do repo.**
- Skrypt i instrukcja: `projects/regal-nieregularny/promo/audio_edit/` (`fal_music.py`, przygotowuje agent od dźwięku).
  Typowo: `pip3 install fal-client && python3 fal_music.py --env ~/sciezka/.env`

## 4. Zasoby z repo produktu
Model regału pochodzi z repo `piotrbugaj-tech/cnc` (`output/model.json`, `regal/blender_scene.py`). Na Macu sklonuj je obok:
`git clone https://github.com/piotrbugaj-tech/cnc ~/Projekty/cnc`
Skrypty promo czytają ścieżkę do niego ze zmiennej `CNC_REPO` (domyślnie `/home/user/cnc` w chmurze).
