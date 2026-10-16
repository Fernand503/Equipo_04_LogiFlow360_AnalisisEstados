"""
Extrae las 10 máquinas de estado de LogiFlow360_StateModels.mdj y genera:
  - matrices_desde_mdj.json : transiciones por entidad (origen, trigger, guarda, efecto, destino, doc)
  - auditoria_qa.json       : comprobaciones del Rol 3 (initial, finales, pozos negros, huérfanos,
                              nomenclatura, determinismo a revisar, sintaxis)
Uso: python3 -I extraer_matrices.py <ruta.mdj> <carpeta_salida>
Solo lee el .mdj; no lo modifica.
"""
import json, re, sys, collections, os

mdj, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
root = json.load(open(mdj, encoding="utf-8"))

by_id = {}
def index(o, parent=None):
    if isinstance(o, dict):
        if "_id" in o:
            by_id[o["_id"]] = o
            o["__parent_obj"] = parent
        for k, v in list(o.items()):
            if k != "__parent_obj":
                index(v, o if "_id" in o else parent)
    elif isinstance(o, list):
        for v in o:
            index(v, parent)
index(root)

def ref(r): return by_id[r["$ref"]]

def owner_state(v):
    """Estado compuesto que contiene al vértice (o None)."""
    p = v.get("__parent_obj")          # región
    if p and p.get("_type") == "UMLRegion":
        q = p.get("__parent_obj")
        if q and q.get("_type") == "UMLState":
            return q
    return None

def label(v):
    t = v["_type"]
    if t == "UMLPseudostate":
        base = {"initial": "● Initial", "choice": "◇ Choice"}.get(v.get("kind"), v.get("kind"))
        if v.get("kind") == "choice":
            base += " " + (v.get("name") or CHOICE_NUM.get(v["_id"], ""))
    elif t == "UMLFinalState":
        base = "◉ Final"
    else:
        base = v.get("name", "?")
    own = owner_state(v)
    return (own["name"] + "::" + base) if own else base

def machine_of(o):
    p = o
    while p is not None and p.get("_type") != "UMLStateMachine":
        p = p.get("__parent_obj")
    return p

def ancestors(v):
    res, s = [], owner_state(v)
    while s is not None:
        res.append(s); s = owner_state(s)
    return res

machines = [o for o in by_id.values() if o.get("_type") == "UMLStateMachine"]
CHOICE_NUM = {}
for _m in machines:
    _ch = [o for o in by_id.values() if o.get("_type") == "UMLPseudostate" and o.get("kind") == "choice" and machine_of(o) is _m]
    for _i, _c in enumerate(_ch, 1):
        CHOICE_NUM[_c["_id"]] = "C" + str(_i)
diagrams = [o for o in by_id.values() if o.get("_type") == "UMLStatechartDiagram"]

VERB_RE = re.compile(r"^(?:[A-Za-zÁÉÍÓÚáéíóúñÑ]+(?:ar|er|ir))$")
PARTICIPIO_OK = re.compile(r"(ado|ada|ido|ida|to|ta|cho|cha|so|sa)$")

result, audit = {}, {}
for m in machines:
    ent = m["name"].replace("SM_", "")
    verts = [o for o in by_id.values() if machine_of(o) is m and o["_type"] in ("UMLState", "UMLPseudostate", "UMLFinalState")]
    trans = [o for o in by_id.values() if machine_of(o) is m and o["_type"] == "UMLTransition"]
    rows = []
    out_by, in_by = collections.defaultdict(list), collections.defaultdict(list)
    for t in trans:
        s, d = ref(t["source"]), ref(t["target"])
        trig = ", ".join(e.get("name", "") for e in t.get("triggers", []))
        eff = "; ".join(e.get("name", "") for e in t.get("effects", []))
        rows.append({
            "id": t["_id"], "origen": label(s), "trigger": trig,
            "guarda": ("[" + t["guard"] + "]") if t.get("guard") else "",
            "efecto": ("/ " + eff) if eff else "", "destino": label(d),
            "kind": t.get("kind", ""), "doc": (t.get("documentation") or "").strip(),
            "_src": s["_id"], "_dst": d["_id"],
        })
        out_by[s["_id"]].append(t); in_by[d["_id"]].append(t)

    states = [v for v in verts if v["_type"] == "UMLState"]
    initials = [v for v in verts if v["_type"] == "UMLPseudostate" and v.get("kind") == "initial"]
    finals = [v for v in verts if v["_type"] == "UMLFinalState"]
    choices = [v for v in verts if v["_type"] == "UMLPseudostate" and v.get("kind") == "choice"]
    composites = [v for v in states if v.get("regions")]

    def has_out(v):   # salida propia o heredada de un compuesto que lo contiene
        return bool(out_by[v["_id"]]) or any(out_by[a["_id"]] for a in ancestors(v))
    def has_in(v):    # entrada propia, o entrada al compuesto que lo contiene (no se usa initial anidado)
        return bool(in_by[v["_id"]])

    pozos = [label(v) for v in states if not has_out(v)]
    huerfanos = [label(v) for v in states if not has_in(v)]
    finales_con_salida = [label(v) for v in finals if out_by[v["_id"]]]
    choice_sin_guarda = [label(c) for c in choices for t in out_by[c["_id"]] if not t.get("guard")]
    trans_sin_trigger = [r for r in rows if not r["trigger"] and not r["origen"].endswith("Initial")
                         and "Choice" not in r["origen"]]
    # Determinismo: mismo origen + mismo trigger con >1 salida -> requiere guardas excluyentes (revisión manual)
    grupos = collections.defaultdict(list)
    for r in rows:
        if r["trigger"]:
            grupos[(r["origen"], r["trigger"])].append(r)
    determinismo = []
    for (o, tr), rs in grupos.items():
        if len(rs) > 1:
            determinismo.append({"origen": o, "trigger": tr,
                                 "guardas": [r["guarda"] or "(SIN GUARDA)" for r in rs],
                                 "alguna_sin_guarda": any(not r["guarda"] for r in rs)})
    nombres_sospechosos = []
    for v in states:
        first = v["name"].split("_")[0]
        if VERB_RE.match(first) and not PARTICIPIO_OK.search(first):
            nombres_sospechosos.append(v["name"])
    auto_transiciones = [{"estado": r["origen"], "trigger": r["trigger"], "kind": r["kind"],
                          "riesgo_reentrada": r["kind"] != "internal"} for r in rows if r["_src"] == r["_dst"]]
    eventos_mal = sorted({r["trigger"] for r in rows if r["trigger"] and not (
        r["trigger"].endswith(")") )})
    entry_do_exit = sum(1 for v in states if v.get("entryActivities") or v.get("doActivities") or v.get("exitActivities"))
    timers = sorted({r["trigger"] for r in rows if r["trigger"].startswith(("after(", "at("))})

    result[ent] = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    audit[ent] = {
        "estados": len(states), "transiciones": len(rows), "initial": len(initials), "finales": len(finals),
        "choice": len(choices), "compuestos": [c["name"] for c in composites],
        "eventos_temporales": timers, "estados_con_entry_do_exit": entry_do_exit,
        "pozos_negros": pozos, "estados_sin_entrada": huerfanos,
        "finales_con_salida": finales_con_salida, "choice_salida_sin_guarda": choice_sin_guarda,
        "transiciones_sin_trigger": [f'{r["origen"]} -> {r["destino"]}' for r in trans_sin_trigger],
        "determinismo_revisar": determinismo, "auto_transiciones": auto_transiciones, "nombres_estado_sospechosos": nombres_sospechosos,
        "eventos_sin_parentesis": eventos_mal,
        "doc_vacia": sum(1 for r in rows if not r["doc"]),
    }

audit["_diagramas"] = sorted(d.get("name", "") for d in diagrams)
json.dump(result, open(os.path.join(out, "matrices_desde_mdj.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(audit, open(os.path.join(out, "auditoria_qa.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if k == "_diagramas" else {x: v[x] for x in ("estados","transiciones","initial","finales","choice","compuestos","pozos_negros","estados_sin_entrada","finales_con_salida","choice_salida_sin_guarda","transiciones_sin_trigger","nombres_estado_sospechosos","eventos_sin_parentesis","doc_vacia","estados_con_entry_do_exit")}) for k, v in audit.items()}, ensure_ascii=False, indent=1))
