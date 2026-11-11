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
        dim0 = "No_" in files[0] or "no_" in files[0].lower() or "Silhouette" in files[0]
        ghost = len(files) == 1 or empty(files[0])  # pas d'image « non obtenu » utilisable -> on grisera l'image « obtenu »
        icons[name] = {"i": files, "d": dim0, "g": ghost}
EXTRA = ["junk/tumbleweed.png", "Song_Block.png", "bosses/g1.png", "bosses/g2.png", "bosses/scaldera.png", "bosses/moldarach.png", "bosses/koloktos.png", "bosses/tentalus.png", "bosses/dreadfuse.png", "Sword_Block.png", "tablets_slot.png", "swords/Dins_Flame.png", "swords/No_Dins_Flame.png", "swords/Farores_Flame.png",
         "swords/No_Farores_Flame.png", "swords/Nayrus_Flame.png", "swords/No_Nayrus_Flame.png"]
for rel in EXTRA:
    shutil.copyfile(os.path.join(repo, "src/assets", rel), "img/" + rel.replace("/", "_").replace(" ", "_"))
# Recadrage : on rogne les marges transparentes (même cadre pour tous les états d'un objet) pour que chaque icône soit bien centrée dans son emplacement
TRIM_ITEMS = ["Ballad of the Goddess", "Farore's Courage", "Nayru's Wisdom", "Din's Power", "Song of the Hero Part", "Goddess's Harp", "Sailcloth",
              "Progressive Mitts", "Water Dragon's Scale", "Fireshield Earrings"]
try:
    from PIL import Image
    for name in TRIM_ITEMS:
        if name not in icons: continue
        ims = [Image.open(f).convert("RGBA") for f in icons[name]["i"]]
        box = None
        for im in ims:
            b = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
            if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        new = []
        for f, im in zip(icons[name]["i"], ims):
            out = f.replace("img/", "img/trim_", 1); im.crop(box).save(out); new.append(out)
        icons[name]["i"] = new
except ImportError:
    print("Pillow absent : icônes non recadrées")
# Triforce (cadre de pierre d'origine) : 0, 1, 2 ou 3 pièces
tri = ["No_Triforce.png", "1_Triforce.png", "2_Triforce.png", "Full_Triforce.png"]
for t in tri:
    shutil.copyfile(os.path.join(repo, "src/assets/main quest", t), "img/main_quest_" + t)
icons["Triforce"] = {"i": ["img/main_quest_" + t for t in tri], "d": False, "g": False}
open("icons.js", "w", encoding="utf-8").write("window.SSHD_ICONS=" + json.dumps(icons, separators=(",", ":")) + ";")
print(len(icons), "objets avec icône,", len(copied), "images copiées")
print("sans icône (extrait) :", [n for n in sorted(set(ap_items)) if n not in icons][:12])


# Tablettes assemblées en un rectangle 139x107 (positions retrouvées en faisant coïncider les pièces avec « no_tablets.png »)
try:
    from PIL import Image
    PIECES = {"Amber Tablet": (0, 0, "amber_tablet.png", "a"), "Ruby Tablet": (38, 0, "ruby_tablet.png", "r"), "Emerald Tablet": (65, 41, "emerald_tablet.png", "e")}
    W, H, S = 139, 107, 3
    ims = {n: Image.open(os.path.join(repo, "src/assets/tablets", f)).convert("RGBA") for n, (x, y, f, k) in PIECES.items()}
    def owner(px, py):
        best, who = 40, "."
        for n, (x, y, f, k) in PIECES.items():
            im = ims[n]; lx, ly = px - x, py - y
            if 0 <= lx < im.width and 0 <= ly < im.height and im.getpixel((lx, ly))[3] > best: best, who = im.getpixel((lx, ly))[3], k
        return who
    grid = ["".join(owner(cx * S + 1, cy * S + 1) for cx in range(-(-W // S))) for cy in range(-(-H // S))]
    tab = {"w": W, "h": H, "p": {n: [x, y, ims[n].width, ims[n].height] for n, (x, y, f, k) in PIECES.items()}, "g": grid, "k": {k: n for n, (x, y, f, k) in PIECES.items()}}
    open("icons.js", "a", encoding="utf-8").write("\nwindow.SSHD_TABLETS=" + json.dumps(tab, separators=(",", ":")) + ";")
    print("tablettes assemblées :", len(grid), "x", len(grid[0]))
except ImportError:
    print("Pillow absent : tablettes non assemblées")
