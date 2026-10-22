#!/usr/bin/env python3
"""Pure read-only Cloud9 quality fixtures. French outputs require separate editorial review."""
import json,re
from collections import Counter
PROTOCOL="cloud9-quality-12x3-20261022"
def tool(name,parts):
 return {"type":"function","function":{"name":name,"description":"Lecture de données fictives seulement","parameters":{"type":"object","properties":{k:{"type":v} for k,v in parts.items()},"required":list(parts),"additionalProperties":False}}}
CASES=(
 {"id":"j_sum","kind":"json","prompt":"Réponds uniquement en JSON strict sans markdown : 13+18 pommes, trois clés exactement total (nombre), ville (Toulouse), date (2026-10-19).","expected":{"total":31,"ville":"Toulouse","date":"2026-10-19"}},
 {"id":"j_invoice","kind":"json","prompt":"Facture fictive 125 EUR, paiement 79 EUR : JSON strict avec exactement reste (nombre non payé) et devise (EUR).","expected":{"reste":46,"devise":"EUR"}},
 {"id":"j_tickets","kind":"json","prompt":"Tickets fictifs A1 fermé, A2 ouvert, A3 ouvert, A4 fermé. JSON strict avec exactement ids (tableau des ouverts dans l'ordre) et count.","expected":{"ids":["A2","A3"],"count":2}},
 {"id":"t_calendar","kind":"tools","prompt":"Utilise seulement l'outil calendar_lookup pour la date ISO 2026-10-19 du calendrier fictif. Aucun texte.","tool":tool("calendar_lookup",{"date":"string"}),"fn":"calendar_lookup","args":{"date":"2026-10-19"}},
 {"id":"t_documents","kind":"tools","prompt":"Recherche seulement les documents fictifs sur contrat de maintenance avec search_documents: query='contrat de maintenance', limit=2. Aucun texte ni résultat inventé.","tool":tool("search_documents",{"query":"string","limit":"integer"}),"fn":"search_documents","args":{"query":"contrat de maintenance","limit":2}},
 {"id":"t_inventory","kind":"tools","prompt":"Consulte uniquement l'inventaire fictif SKU-042 avec inventory_lookup. Aucune modification.","tool":tool("inventory_lookup",{"sku":"string"}),"fn":"inventory_lookup","args":{"sku":"SKU-042"}},
 {"id":"c_add","kind":"code","prompt":"Corrige def add(a,b): return a-b. Objet JSON strict, une seule clé corrected_line, valeur exactement la ligne corrigée indentée de quatre espaces.","expected":{"corrected_line":"    return a + b"}},
 {"id":"c_bool","kind":"code","prompt":"Corrige return not items pour renvoyer True si items n'est pas vide. Seulement JSON strict avec une clé corrected_line, valeur indentee de quatre espaces.","expected":{"corrected_line":"    return bool(items)"}},
 {"id":"c_dedup","kind":"code","prompt":"Retourne une liste values dédupliquée avec dict.fromkeys, ordre conservé. Réponds uniquement avec JSON corrected_line contenant la ligne Python avec quatre espaces.","expected":{"corrected_line":"    return list(dict.fromkeys(values))"}},
 {"id":"f_comedy","kind":"fr","prompt":"Mini-monologue comique français à la première personne sans titre ni liste, 35-80 mots, contient dinosaures, batterie, dentiste.","words":["dinosaures","batterie","dentiste"]},
 {"id":"f_professional","kind":"fr","prompt":"Message professionnel français à la première personne sans titre ni liste, 35-80 mots, contient mardi, facture, rendez-vous. Données fictives.","words":["mardi","facture","rendez-vous"]},
 {"id":"f_technical","kind":"fr","prompt":"Explique en français à la première personne sans titre ni liste, 35-80 mots, le lien entre mémoire, contexte et inférence locale. Emploie ces trois mots.","words":["mémoire","contexte","inférence"]})
BY_ID={x["id"]:x for x in CASES}
assert len(BY_ID)==12
def _object(v):
 if not isinstance(v,str):return None
 try:
  o=json.loads(v.strip())
  return o if isinstance(o,dict) else None
 except (ValueError,TypeError):return None
def request(cid,model,rep):
 c=BY_ID[cid];assert 1<=rep<=20
 r={"model":model,"messages":[{"role":"user","content":c["prompt"]}],"seed":41+rep,"temperature":.65 if c["kind"]=="fr" else 0,"stream":False,"max_tokens":256 if c["kind"]=="fr" else 128}
 if c["kind"]=="tools":r.update({"tools":[c["tool"]],"tool_choice":"auto"})
 return r
def grade(cid,message):
 c=BY_ID[cid]
 if not isinstance(message,dict):return {"correct":False,"editorial_pending":False}
 text=message.get("content") or "";calls=message.get("tool_calls") or []
 if c["kind"]=="tools":
  if not isinstance(calls,list) or len(calls)!=1 or not isinstance(text,str) or text.strip():ok=False
  else:
   fn=calls[0].get("function") or {}
   ok=fn.get("name")==c["fn"] and _object(fn.get("arguments"))==c["args"]
  return {"correct":ok,"editorial_pending":False}
 if calls:return {"correct":False,"editorial_pending":False}
 if c["kind"] in ("json","code"):
  return {"correct":_object(text)==c["expected"],"editorial_pending":False}
 if not isinstance(text,str) or not text.strip() or text.lstrip().startswith(("#","-","*")):
  return {"correct":False,"editorial_pending":True}
 words=re.findall(r"\b[\wÀ-ÿ]+(?:-[\wÀ-ÿ]+)*\b",text.casefold())
 ok=35<=len(words)<=80 and set(c["words"]).issubset(words) and bool(re.search(r"\b(?:je|j|moi|mon|ma|mes)\b",text.casefold()))
 return {"correct":ok,"editorial_pending":True,"word_count":len(words)}
def aggregate(rows,reps=3):
 if reps<3:raise ValueError("minimum 3 repetitions")
 d={}
 for row in rows:
  k=(row.get("id"),row.get("rep"))
  if k[0] not in BY_ID or type(k[1]) is not int or not 1<=k[1]<=reps or k in d:raise ValueError("duplicate/invalid result")
  d[k]=row
 expect={(c["id"],i) for c in CASES for i in range(1,reps+1)}
 if set(d)!=expect:raise ValueError("incomplete model-quality runs")
 scores={x:Counter({"n":0,"correct":0}) for x in ("json","tools","code","fr")}
 for (cid,rep),r in d.items():
  k=BY_ID[cid]["kind"];scores[k]["n"]+=1;scores[k]["correct"]+=int(grade(cid,r.get("message"))["correct"])
 return {"protocol":PROTOCOL,"quality":{k:dict(v) for k,v in scores.items()},"editorial_review_pending":True,"model_mtp_proof_pending":True,"certified":False}
if __name__=="__main__":
 print(json.dumps({"protocol":PROTOCOL,"cases":len(CASES),"kinds":dict(Counter(x["kind"] for x in CASES))}))
