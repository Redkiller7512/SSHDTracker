"""Régénère data.js et maps/ depuis un .apworld : python build_data.py chemin/vers/sshd.apworld"""
import sys, zipfile, types, json, re, os, struct, yaml
apworld = sys.argv[1] if len(sys.argv) > 1 else "sshd.apworld"
z = zipfile.ZipFile(apworld)
base = "sshd/sshd-rando-backend/"

mod = types.ModuleType("L"); exec(z.read("sshd/Locations.py").decode(), mod.__dict__)
loc = mod.LOCATION_TABLE
items = {m.group(2): m.group(1) for m in re.finditer(r'"((?:[^"\\]|\\.)*)": SSHDItem\("(?:[^"\\]|\\.)*", (\d+),', z.read("sshd/Items.py").decode())}
meta = json.loads(z.read("sshd/archipelago.json"))

nodes = {a["name"]: a for a in yaml.safe_load(z.read(base + "data/tracker_areas.yaml"))}
FR = {"Skyloft": "Célesbourg", "Faron": "Firone", "Eldin": "Ordinn", "Lanayru": "Lanelle", "Sky": "Ciel", "Inside the Thunderhead": "Thunderhead"}
ORDER = ["Sky", "Skyloft", "Faron", "Eldin", "Lanayru", "Inside the Thunderhead"]
# Régions absentes de tracker_areas.yaml -> nœud de carte le plus proche
EXTRA = {
 "Sparring Hall": "Knight Academy", "Inside the Statue of the Goddess": "Upper Skyloft", "Bazaar": "Central Skyloft",
 "Sealed Temple": "Sealed Grounds", "Temple of Hylia": "Sealed Grounds", "Hylia's Realm": "Sealed Grounds",
 "Deep Woods": "Faron Woods", "Floria Waterfall": "Lake Floria", "Inside the Flooded Great Tree": "Flooded Faron Woods", "Skyview Spring": "Skyview Temple",
 "Thrill Digger Cave": "Eldin Volcano", "Lower Eldin Cave": "Eldin Volcano", "Upper Eldin Cave": "Eldin Volcano", "Earth Spring": "Earth Temple",
 "Fire Node": "Lanayru Desert", "Lightning Node": "Lanayru Desert", "Skipper's Retreat": "Lanayru Sand Sea", "Skipper's Retreat Shack": "Lanayru Sand Sea",
 "Shipyard": "Lanayru Sand Sea", "Construction Bay": "Lanayru Sand Sea", "Pirate Stronghold": "Lanayru Sand Sea", "Pirate Stronghold Interior": "Lanayru Sand Sea",
}
SKY_ISLANDS = ["Bamboo Island Interior", "Bamboo Island", "Lumpy Pumpkin", "Orielle's Island", "Beedle's Island", "Fun Fun Island", "Island near Bamboo Island",
               "Northeast Island", "Island Closest to Faron Pillar", "Volcanic Island", "Triple Island", "Bug Heaven", "Isle of Songs"]

os.makedirs("maps", exist_ok=True)
def png(name):
    d = z.read(base + "assets/tracker/maps/" + name); open("maps/" + name, "wb").write(d)
    w, h = struct.unpack(">II", d[16:24]); return {"file": "maps/" + name, "w": w, "h": h}

zones = []
for k in ORDER:
    n = nodes[k]
    zone = {"k": k, "fr": FR[k], "x": n["x"], "y": n["y"], "areas": []}
    if n.get("image"):
        zone["img"] = png(n["image"])
        zone["areas"] = [{"n": c, "x": nodes[c]["x"], "y": nodes[c]["y"], "t": nodes[c].get("type", "")} for c in n.get("children", [])]
    zones.append(zone)
root_img = png(nodes["Root"]["image"])

region_area = {}
zone_of = {}
for z_ in zones:
    for a in z_["areas"]:
        region_area[a["n"]] = a["n"]; zone_of[a["n"]] = z_["k"]
for r, a in EXTRA.items():
    region_area[r] = a
for r in SKY_ISLANDS + ["The Sky"]:
    region_area[r] = "Sky"; zone_of["Sky"] = "Sky"
region_area["Inside the Thunderhead"] = "Inside the Thunderhead"; zone_of["Inside the Thunderhead"] = "Inside the Thunderhead"
for r in {l.region for l in loc.values()}:
    if r not in region_area:
        print("Région non classée :", r)
alias = {n["alias"]: n["name"] for n in nodes.values() if n.get("alias")}
for al, nm in alias.items():
    region_area.setdefault(al, nm)

data = {"game": meta["game"], "version": meta["world_version"], "root": root_img, "zones": zones,
        "regionArea": region_area, "zoneOf": zone_of, "items": items,
        "locations": [[l.name, l.code, l.region, l.types] for l in loc.values()]}
open("data.js", "w", encoding="utf-8").write("window.SSHD_DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
print(len(loc), "locations,", len(items), "objets, jeu =", meta["game"])


# ================= Logique (zones, sorties, macros, réglages) -> logic.js =================
import glob
bk = "sshd/sshd-rando-backend/data/"
def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

macros = {k.replace("_", " "): str(v) for k, v in yaml.safe_load(z.read(bk + "macros.yaml")).items()}
settings_raw = yaml.safe_load(z.read(bk + "settings_list.yaml"))
settings = {}
for s in settings_raw:
    opts = s.get("options")
    names = []
    if isinstance(opts, list):
        for o in opts:
            names.append(str(list(o.keys())[0]))
    rng = bool(names) and all(re.fullmatch(r"\d+-\d+", n) for n in names)
    d = s.get("default_option")
    settings[s["name"]] = {"d": d if rng or not names else str(d), "o": [] if rng else names}
    if rng: settings[s["name"]]["d"] = int(d) if str(d).lstrip("-").isdigit() else d

TOK = re.compile(r"\(|\)|[A-Za-z_]+\([^)]*\)|[^\s()]+")
errors = []
def atom(a):
    if a == "Nothing": return ["N"]
    if a in ("Impossible", "not_tracker"): return ["X"]
    if a == "Day": return ["D"]
    if a == "Night": return ["T"]
    if a.replace("_", " ") in macros: return ["m", a.replace("_", " ")]
    if a.startswith("'"): return ["e", norm(a.strip("'"))]  # noms d'événements normalisés : les règles écrivent Save_Orielle, les zones « Save Orielle »
    m = re.fullmatch(r"count\(\s*(\d+)\s*,\s*([^)]+?)\s*\)", a)
    if m: return ["i", norm(m[2])] if m[1] == "1" else ["c", int(m[1]), norm(m[2])]
    m = re.fullmatch(r"can_access\((.+)\)", a)
    if m: return ["a", m[1].strip()]
    m = re.fullmatch(r"wallet_capacity\((\d+)\)", a)
    if m: return ["w", int(m[1])]
    m = re.fullmatch(r"gratitude_crystals\((\d+)\)", a)
    if m: return ["g", int(m[1])]
    m = re.fullmatch(r"(\w+)(==|!=|>=|<=)(\S+)", a)
    if m and m[1] in settings: return ["s", m[1], m[2], m[3]]
    if a in settings: return ["b", a]
    return ["i", norm(a)]

def parse(text):
    t = re.sub(r"\s*(==|!=|>=|<=)\s*", r"\1", " ".join(str(text).split()))
    toks = TOK.findall(t); pos = [0]
    def seq():
        ops, kind = [], None
        while pos[0] < len(toks) and toks[pos[0]] != ")":
            tk = toks[pos[0]]
            if tk in ("and", "or"): kind = tk; pos[0] += 1; continue
            ops.append(operand())
        if len(ops) == 1: return ops[0]
        return ["&" if kind == "and" else "|"] + ops
    def operand():
        tk = toks[pos[0]]; pos[0] += 1
        if tk == "not": return ["!", operand()]
        if tk == "(":
            r = seq(); pos[0] += 1; return r
        return atom(tk)
    return seq()

def P(text):
    try: return parse(text)
    except Exception as e:
        errors.append((text, str(e))); return ["X"]

areas = {}
for f in z.namelist():
    if f.startswith(bk + "world/") and f.endswith(".yaml"):
        for a in yaml.safe_load(z.read(f)) or []:
            d = areas.setdefault(a["name"], {"x": {}, "l": {}, "e": {}})
            for k, key in (("exits", "x"), ("locations", "l"), ("events", "e")):
                for n, r in (a.get(k) or {}).items(): d[key][norm(n) if key == "e" else n] = P(r)
mac = {k: P(v) for k, v in macros.items()}
ER = [n for n in settings if re.match(r"(randomize_(dungeon|trial|door|interior|overworld|entrance|gate)|decouple|random_starting_spawn)", n)]
open("logic.js", "w", encoding="utf-8").write("window.SSHD_LOGIC=" + json.dumps({"areas": areas, "macros": mac, "settings": settings, "er": ER}, separators=(",", ":")) + ";")
print("logique :", len(areas), "zones,", sum(len(a["l"]) for a in areas.values()), "checks avec règles,", len(mac), "macros,", len(settings), "réglages,", len(errors), "erreurs d'analyse")
for e in errors[:5]: print("  ", e)
