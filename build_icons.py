"""Génère img/ et icons.js depuis le dépôt du tracker d'origine (branche archipelago ou main).
Usage : python build_icons.py chemin/vers/SS-Randomizer-Tracker"""
import sys, re, os, shutil, json
repo = sys.argv[1] if len(sys.argv) > 1 else "SS-Randomizer-Tracker"
src = open(os.path.join(repo, "src/itemTracker/Images.ts"), encoding="utf-8").read()
imports = dict(re.findall(r"import (\w+) from '\.\./assets/([^']+)';", src))
body = src.split("const images: Images = {")[1].split("\n};")[0]
body = re.sub(r"//[^\n]*", "", body)
table = {}
for m in re.finditer(r"(?:'([^']+)'|\"([^\"]+)\"|(\w+)):\s*\[([^\]]*)\]", body):
    key = m[1] or m[2] or m[3]
    table[key] = [v.strip() for v in m[4].split(",") if v.strip()]

# Noms Archipelago -> clé du tracker d'origine
ALIAS = {"Gratitude Crystal": "Gratitude Crystals", "Rattle": "Baby Rattle", "Skyview Temple Boss Key": "Skyview Boss Key",
<<<<<<< HEAD
         "Skyview Temple Small Key": "Skyview Small Key", "Big Bug Net": "Progressive Bug Net", "Song of the Hero Part": "Song of the Hero"}
ap_items = json.loads(open("data.js", encoding="utf-8").read()[len("window.SSHD_DATA="):-1])["items"].values()
os.makedirs("img", exist_ok=True)
def empty(path):  # vrai si l'image est (presque) entièrement transparente
    try:
        from PIL import Image
        a = Image.open(path).convert("RGBA").getchannel("A")
        return sum(1 for v in a.getdata() if v > 40) / (a.width * a.height) < 0.02
    except ImportError:
        return False
=======
         "Skyview Temple Small Key": "Skyview Small Key", "Big Bug Net": "Progressive Bug Net"}
ap_items = json.loads(open("data.js", encoding="utf-8").read()[len("window.SSHD_DATA="):-1])["items"].values()
os.makedirs("img", exist_ok=True)
>>>>>>> 475b6dbe9f54ec9ad1f11ad55e3ff94dd32b6d1c
icons, copied = {}, {}
def copy(var):
    rel = imports[var]
    dest = "img/" + rel.replace("/", "_").replace(" ", "_")
    if rel not in copied:
        shutil.copyfile(os.path.join(repo, "src/assets", rel), dest); copied[rel] = dest
    return copied[rel]
for name in sorted(set(ap_items)):
    key = ALIAS.get(name, name)
    if key in table and all(v in imports for v in table[key]):
        files = [copy(v) for v in table[key]]
<<<<<<< HEAD
        dim0 = "No_" in files[0] or "no_" in files[0].lower() or "Silhouette" in files[0]
        ghost = len(files) == 1 or empty(files[0])  # pas d'image « non obtenu » utilisable -> on grisera l'image « obtenu »
        icons[name] = {"i": files, "d": dim0, "g": ghost}
=======
        dim0 = bool(re.match(r"(no_|.*silhouette)", os.path.basename(files[0]).split("_", 1)[-1] if files[0].startswith("img/") else "", re.I)) or "No_" in files[0] or "no_" in files[0].lower() or "Silhouette" in files[0]
        icons[name] = {"i": files, "d": dim0}
>>>>>>> 475b6dbe9f54ec9ad1f11ad55e3ff94dd32b6d1c
EXTRA = ["Sword_Block.png", "tablets_slot.png", "swords/Dins_Flame.png", "swords/No_Dins_Flame.png", "swords/Farores_Flame.png",
         "swords/No_Farores_Flame.png", "swords/Nayrus_Flame.png", "swords/No_Nayrus_Flame.png"]
for rel in EXTRA:
    shutil.copyfile(os.path.join(repo, "src/assets", rel), "img/" + rel.replace("/", "_").replace(" ", "_"))
open("icons.js", "w", encoding="utf-8").write("window.SSHD_ICONS=" + json.dumps(icons, separators=(",", ":")) + ";")
print(len(icons), "objets avec icône,", len(copied), "images copiées")
print("sans icône (extrait) :", [n for n in sorted(set(ap_items)) if n not in icons][:12])
