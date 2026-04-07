import requests, base64, os, sys, unicodedata
from requests.auth import HTTPBasicAuth
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding="utf-8")

JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_TOKEN = os.environ["JIRA_TOKEN"]
GH_PAT     = os.environ["GH_PAT"]
REPO       = "CrisSjobom/crc-dashboard"
DONE_ST    = {"concluido","done","closed","resolved"}

ASSIGNEE_MAP = [
    ("Andre Porto","Andre Porto"),("André Porto","Andre Porto"),("André Luiz","Andre Porto"),
    ("Ricardo Suzuki","Ricardo Suzuki"),("Ricardo Eiji","Ricardo Suzuki"),
    ("Barbara Hulse","Barbara Hulse"),("Bárbara Hülse","Barbara Hulse"),
    ("Cristtiane Sjobom","Cristtiane Sjobom"),("Cristtiane Moreira","Cristtiane Sjobom"),
    ("Rafael Yoneta","Rafael Yoneta"),
    ("yan.garcia","Yan Garcia"),("Yan Almeida","Yan Garcia"),
    ("Faruk Abdo","Faruk Feres"),("Faruk","Faruk Feres"),
    ("Gerbert Santos","Gerbert Santos"),
    ("Pedro Henrique Stival","Pedro Stival"),
    ("Bruno","Bruno Martins"),
    ("Ricardo Duque","Ricardo Goes"),
    ("Rafael Libano","Rafael Rodrigues"),("Rafael Líbano","Rafael Rodrigues"),
    ("Adriano Rodrigues","Adriano Rodrigues"),("Adriano Silva","Adriano Rodrigues"),
    ("Priscila Mara","Priscila Mara"),
    ("Leandro Lustosa","Leandro Lustosa"),
    ("Jean Fontoura","Jean Fontoura"),("Jean Rosado","Jean Fontoura"),
    ("felipe.fernandes","Felipe Fernandes"),("Felipe Hermes","Felipe Fernandes"),
    ("arthur.iensen","Arthur Iensen"),("Arthur Ribeiro","Arthur Iensen"),
    ("Yasmin Jannuzzi","Yasmin Cozaciuc"),("Yasmin Di Franco","Yasmin Cozaciuc"),
    ("William Bartos","William Bartos"),
    ("Phillipe Soares","Phillipe Rangel"),
    ("Joao Pradella","Joao Pradella"),("João Pradella","Joao Pradella"),
    ("João Sant","Joao Sant Anna"),("Joao Sant","Joao Sant Anna"),("Sant'Anna","Joao Sant Anna"),
]

GROUPS = [
    {"num":1,"cls":"g1","icon":"🚀","subjects":["Pagamento / Financeiro"],"members":[
        {"display":"André Porto",    "key":"Andre Porto",    "initials":"AN"},
        {"display":"Ricardo Suzuki", "key":"Ricardo Suzuki", "initials":"RC"},
        {"display":"Bárbara Hülse",  "key":"Barbara Hulse",  "initials":"BH"},
        {"display":"João Sant'Anna", "key":"Joao Sant Anna", "initials":"JO"},
    ]},
    {"num":2,"cls":"g2","icon":"⚡","subjects":["Documentação / Licenciamento","Pendências / Regularização","Vínculo / Minha Mottu"],"members":[
        {"display":"Cristtiane Sjobom","key":"Cristtiane Sjobom","initials":"CS"},
        {"display":"Rafael Yoneta",   "key":"Rafael Yoneta",    "initials":"RY"},
        {"display":"Yan Garcia",      "key":"Yan Garcia",       "initials":"YG"},
        {"display":"Faruk Feres",     "key":"Faruk Feres",      "initials":"FF"},
    ]},
    {"num":3,"cls":"g3","icon":"🔥","subjects":["Não é possível acessar o app por erro na tela inicial"],"members":[
        {"display":"Gerbert Santos", "key":"Gerbert Santos", "initials":"GS"},
        {"display":"Pedro Stival",   "key":"Pedro Stival",   "initials":"PS"},
        {"display":"Bruno Martins",  "key":"Bruno Martins",  "initials":"BM"},
        {"display":"Isabela Araújo", "key":"Isabela Araujo", "initials":"IA","nao_atuou":True},
    ]},
    {"num":4,"cls":"g4","icon":"💎","subjects":["Reconhecimento Facial","SINESP/190 - BO - Furto"],"members":[
        {"display":"Ricardo Goes",      "key":"Ricardo Goes",      "initials":"RG"},
        {"display":"Rafael Rodrigues",  "key":"Rafael Rodrigues",  "initials":"RR"},
        {"display":"Adriano Rodrigues", "key":"Adriano Rodrigues", "initials":"AR"},
        {"display":"Priscila Mara",     "key":"Priscila Mara",     "initials":"PM"},
    ]},
    {"num":5,"cls":"g5","icon":"⚔️","members":[
        {"display":"Leandro Lustosa",  "key":"Leandro Lustosa",  "initials":"LL"},
        {"display":"Jean Fontoura",    "key":"Jean Fontoura",    "initials":"JF"},
        {"display":"Felipe Fernandes", "key":"Felipe Fernandes", "initials":"FH"},
        {"display":"Arthur Iensen",    "key":"Arthur Iensen",    "initials":"AI"},
    ]},
    {"num":6,"cls":"g6","icon":"💠","subjects":["Erro no totem"],"members":[
        {"display":"Yasmin Cozaciuc","key":"Yasmin Cozaciuc","initials":"YC"},
        {"display":"William Bartos", "key":"William Bartos", "initials":"WB","nao_atuou":True},
        {"display":"Phillipe Rangel","key":"Phillipe Rangel","initials":"PR"},
        {"display":"João Pradella","key":"Joao Pradella","initials":"JP"},
    ]},
]

STATUS_BADGE = {
    "Em andamento":               ("b-em-andamento","Em andamento"),
    "Concluído":                  ("b-concluido",   "Concluído"),
    "Não avançou":                ("b-nao-avancou", "Não avançou"),
    "Não iniciado":               ("b-nao-iniciado","Não iniciado"),
    "Aguardando Desenvolvimento": ("b-ag-dev",       "Ag. Desenvolvimento"),
    "Pendência com outro time":   ("b-pendencia",   "Pendência c/ outro time"),
    "Aguardando Cliente":         ("b-ag-cliente",  "Aguardando Cliente"),
}

def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")

def resolve(name):
    if not name: return None
    nl = name.lower()
    for frag, key in ASSIGNEE_MAP:
        if frag.lower() in nl:
            return key
    return None

def get_badge(s):
    if s in STATUS_BADGE: return STATUS_BADGE[s]
    for k, v in STATUS_BADGE.items():
        if norm(k) == norm(s): return v
    return ("b-nao-iniciado", s or "?")

def extract_text(node):
    if not isinstance(node, dict): return ""
    if node.get("type") == "text": return node.get("text","")
    return "".join(extract_text(c) for c in node.get("content",[]))

def link_done(lnk):
    issue = lnk.get("inwardIssue") or lnk.get("outwardIssue") or {}
    st = issue.get("fields",{}).get("status",{}).get("name","")
    return norm(st) in DONE_ST

def fetch_issues():
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    hd = {"Accept":"application/json","Content-Type":"application/json"}
    r = requests.post("https://mottu-team.atlassian.net/rest/api/3/search/jql",
        headers=hd, auth=auth, json={
            "jql": 'project = "Centralização - Reclamações - Clientes" AND assignee is not EMPTY ORDER BY key ASC',
            "maxResults": 100,
            "fields": ["summary","status","assignee","comment","issuelinks"]
        })
    r.raise_for_status()
    return r.json()["issues"]

def build_map(issues):
    m = {}
    for i in issues:
        f = i["fields"]
        k = resolve(f["assignee"]["displayName"] if f.get("assignee") else None)
        if not k: continue
        comments = f.get("comment",{}).get("comments",[])
        last_c = {"author":"","date":"","text":""}
        if comments:
            c = comments[-1]
            raw = extract_text(c.get("body",{})).strip()
            dt  = c.get("created","")
            day = dt[8:10]+"/"+dt[5:7] if len(dt)>=10 else ""
            first = (c.get("author",{}).get("displayName","") or "").split()[0]
            last_c = {"author":first,"date":day,"text":raw[:120]}
        links   = f.get("issuelinks",[])
        total_l = len(links)
        done_l  = sum(1 for l in links if link_done(l))
        pct     = int(done_l/total_l*100) if total_l else 0
        m.setdefault(k,[]).append({
            "key":     i["key"],
            "summary": f["summary"],
            "status":  f["status"]["name"] if f.get("status") else "?",
            "url":     "https://mottu-team.atlassian.net/browse/"+i["key"],
            "comment": last_c,
            "progress":{"total":total_l,"done":done_l,"pct":pct},
        })
    return m

CSS = """* { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; }
  header { background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%); border-bottom: 2px solid #21262d; padding: 24px 32px; text-align: center; }
  header h1 { font-size: 1.8rem; font-weight: 700; letter-spacing: 1px; color: #f0f6fc; }
  header p { color: #8b949e; margin-top: 6px; font-size: 0.9rem; }
  .header-meta { display: flex; justify-content: center; gap: 16px; margin-top: 16px; flex-wrap: wrap; align-items: center; }
  .meta-badge { background: #21262d; border: 1px solid #30363d; border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; color: #8b949e; }
  .meta-badge span { color: #f0f6fc; font-weight: 600; }
  .live-badge { display: inline-flex; align-items: center; gap: 6px; background: #0d2a0d; border: 1px solid #238636; border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; color: #56d364; }
  .live-dot { width: 8px; height: 8px; background: #56d364; border-radius: 50%; animation: pulse 2s infinite; flex-shrink: 0; }
  @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.4} }
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 28px 32px; max-width: 1600px; margin: 0 auto; }
  .group-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; }
  .group-header { padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; }
  .group-header h2 { font-size: 1.05rem; font-weight: 700; letter-spacing: 0.5px; }
  .group-xp { background: rgba(0,0,0,0.25); border-radius: 20px; padding: 3px 12px; font-size: 0.75rem; font-weight: 600; color: #fff; }
  .g1 .group-header { background: linear-gradient(135deg, #e8510a, #c0410a); }
  .g2 .group-header { background: linear-gradient(135deg, #0a7c6e, #057a62); }
  .g3 .group-header { background: linear-gradient(135deg, #d4920a, #b07a08); }
  .g4 .group-header { background: linear-gradient(135deg, #1560bd, #0f4d9c); }
  .g5 .group-header { background: linear-gradient(135deg, #7a3fbf, #612fb0); }
  .g6 .group-header { background: linear-gradient(135deg, #3a5fa8, #2d4d8e); }
  .group-body { padding: 14px 16px; flex: 1; }
  .member { margin-bottom: 10px; border: 1px solid #21262d; border-radius: 8px; overflow: hidden; }
  .member-name { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #0d1117; font-size: 0.82rem; font-weight: 600; color: #c9d1d9; border-bottom: 1px solid #21262d; }
  .member-name .avatar { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; flex-shrink: 0; }
  .g1 .avatar { background: #e8510a; } .g2 .avatar { background: #0a7c6e; }
  .g3 .avatar { background: #d4920a; } .g4 .avatar { background: #1560bd; }
  .g5 .avatar { background: #7a3fbf; } .g6 .avatar { background: #3a5fa8; }
  .tickets { padding: 6px 8px; display: flex; flex-direction: column; gap: 4px; }
  .ticket-row { border-radius: 6px; overflow: hidden; background: #0d1117; border: 1px solid #21262d; margin-bottom: 2px; }
  .ticket { display: flex; align-items: center; gap: 8px; padding: 5px 8px; font-size: 0.75rem; background: #161b22; }
  .ticket-key { font-weight: 700; color: #58a6ff; white-space: nowrap; font-size: 0.72rem; min-width: 48px; }
  .ticket-key a { color: inherit; text-decoration: none; } .ticket-key a:hover { text-decoration: underline; }
  .ticket-summary { color: #8b949e; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .badge { border-radius: 4px; padding: 2px 7px; font-size: 0.65rem; font-weight: 700; white-space: nowrap; flex-shrink: 0; text-transform: uppercase; letter-spacing: 0.3px; }
  .b-em-andamento  { background: #1a4a1a; color: #56d364; border: 1px solid #238636; }
  .b-concluido     { background: #0d3a1a; color: #3fb950; border: 1px solid #2ea043; }
  .b-nao-avancou   { background: #4a1a1a; color: #f85149; border: 1px solid #da3633; }
  .b-nao-iniciado  { background: #3a3a1a; color: #e3b341; border: 1px solid #9e6a03; }
  .b-ag-dev        { background: #1a2f4a; color: #79c0ff; border: 1px solid #1f6feb; }
  .b-ag-cliente    { background: #2a1f3a; color: #d2a8ff; border: 1px solid #8957e5; }
  .b-pendencia     { background: #3a1f1f; color: #ffa657; border: 1px solid #bd561d; }
  .b-nao-atuou     { background: #1c1c1c; color: #6e7681; border: 1px solid #30363d; }
  .ticket-comment { display: flex; gap: 5px; padding: 3px 8px 5px; font-size: 0.68rem; align-items: flex-start; border-top: 1px dashed #21262d; }
  .cmt-icon { color: #484f58; flex-shrink: 0; }
  .cmt-author { color: #8b949e; font-weight: 600; white-space: nowrap; flex-shrink: 0; }
  .cmt-date { color: #484f58; white-space: nowrap; flex-shrink: 0; }
  .cmt-text { color: #6e7681; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
  .cmt-none { color: #30363d; font-style: italic; padding: 3px 8px 5px; font-size: 0.68rem; border-top: 1px dashed #21262d; }
  .progress-wrap { padding: 4px 8px 7px; border-top: 1px solid #21262d; }
  .progress-label { font-size: 0.62rem; color: #8b949e; margin-bottom: 3px; }
  .progress-track { background: #21262d; border-radius: 4px; height: 5px; overflow: hidden; }
  .progress-fill  { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #238636, #56d364); }
  .no-ticket { padding: 8px; font-size: 0.72rem; color: #484f58; font-style: italic; }
.group-subjects { padding: 8px 14px; display: flex; flex-wrap: wrap; gap: 6px; border-bottom: 1px solid #21262d; background: #0d1117; }
.subj-tag { font-size: 0.72rem; color: #c9d1d9; background: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 3px 10px; font-weight: 500; }
  .group-stats { display: flex; gap: 6px; padding: 10px 16px; border-top: 1px solid #21262d; background: #0d1117; flex-wrap: wrap; }
  .stat-pill { border-radius: 10px; padding: 2px 8px; font-size: 0.65rem; font-weight: 600; }
  .footer { text-align: center; padding: 20px; color: #484f58; font-size: 0.75rem; border-top: 1px solid #21262d; margin-top: 8px; }
  @media (max-width: 1100px) { .grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 700px)  { .grid { grid-template-columns: 1fr; padding: 16px; } }"""

def render_ticket(t):
    bcls, blbl = get_badge(t["status"])
    s  = (t["summary"][:55] + "...") if len(t["summary"]) > 55 else t["summary"]
    c  = t["comment"]
    pg = t["progress"]
    parts = []
    parts.append("<div class='ticket-row'>")
    parts.append("<div class='ticket'>")
    parts.append("<span class='ticket-key'><a href='" + t["url"] + "' target='_blank'>" + t["key"] + "</a></span>")
    parts.append("<span class='ticket-summary'>" + s + "</span>")
    parts.append("<span class='badge " + bcls + "'>" + blbl + "</span>")
    parts.append("</div>")
    if c["text"]:
        parts.append("<div class='ticket-comment'>")
        parts.append("<span class='cmt-icon'>💬</span>")
        parts.append("<span class='cmt-author'>" + c["author"] + "</span>")
        parts.append("<span class='cmt-date'>" + c["date"] + "</span>")
        parts.append("<span class='cmt-text'>" + c["text"] + "</span>")
        parts.append("</div>")
    else:
        parts.append("<div class='cmt-none'>Sem comentários ainda</div>")
    if pg["total"] > 0:
        lbl  = "⚙️ Progresso da entrega: " + str(pg["done"]) + "/" + str(pg["total"]) + " itens (" + str(pg["pct"]) + "%)"
        fill = "width:" + str(pg["pct"]) + "%"
        parts.append("<div class='progress-wrap'>")
        parts.append("<div class='progress-label'>" + lbl + "</div>")
        parts.append("<div class='progress-track'><div class='progress-fill' style='" + fill + "'></div></div>")
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)

def generate_html(issues, mi):
    from collections import Counter
    stats = Counter(i["fields"]["status"]["name"] for i in issues if i["fields"].get("status"))
    total = len(issues)
    tz_sp = timezone(timedelta(hours=-3))
    now   = datetime.now(tz_sp).strftime("%d/%m/%Y %H:%M")

    cards = []
    for g in GROUPS:
        mparts = []
        g_em = g_nao = g_ag = g_pend = g_cli = g_done = 0
        for mem in g["members"]:
            nao_atuou = mem.get("nao_atuou", False)
            ini  = mem["initials"]
            disp = mem["display"]
            mparts.append("<div class='member'>")
            mparts.append("<div class='member-name'><div class='avatar'>" + ini + "</div> " + disp + "</div>")
            if nao_atuou:
                mparts.append("<div class='tickets'><div class='ticket-row'><div class='ticket'>")
                mparts.append("<span class='ticket-key'>—</span>")
                mparts.append("<span class='ticket-summary'>Nenhum caso atribuído</span>")
                mparts.append("<span class='badge b-nao-atuou'>Não Atuou</span>")
                mparts.append("</div></div></div>")
            else:
                tlist = mi.get(mem["key"], [])
                if tlist:
                    mparts.append("<div class='tickets'>")
                    for t in tlist:
                        bcls, _ = get_badge(t["status"])
                        if bcls == "b-em-andamento": g_em += 1
                        elif bcls == "b-nao-avancou": g_nao += 1
                        elif bcls == "b-ag-dev": g_ag += 1
                        elif bcls == "b-pendencia": g_pend += 1
                        elif bcls == "b-ag-cliente": g_cli += 1
                        elif bcls == "b-concluido": g_done += 1
                        mparts.append(render_ticket(t))
                    mparts.append("</div>")
                else:
                    mparts.append("<div class='no-ticket'>Nenhum caso atribuído ainda</div>")
            mparts.append("</div>")

        pills = []
        if g_em:   pills.append("<span class='stat-pill' style='background:#1a4a1a;color:#56d364'>✓ " + str(g_em) + " em andamento</span>")
        if g_done: pills.append("<span class='stat-pill' style='background:#0d3a1a;color:#3fb950'>🏁 " + str(g_done) + " concluído</span>")
        if g_nao:  pills.append("<span class='stat-pill' style='background:#4a1a1a;color:#f85149'>✗ " + str(g_nao) + " não avançou</span>")
        if g_ag:   pills.append("<span class='stat-pill' style='background:#1a2f4a;color:#79c0ff'>⏳ " + str(g_ag) + " ag.dev</span>")
        if g_pend: pills.append("<span class='stat-pill' style='background:#3a1f1f;color:#ffa657'>⚠ " + str(g_pend) + " pendência</span>")
        if g_cli:  pills.append("<span class='stat-pill' style='background:#2a1f3a;color:#d2a8ff'>👤 " + str(g_cli) + " ag.cliente</span>")
        pills_html = "".join(pills) if pills else "<span style='color:#484f58;font-size:0.72rem'>Nenhuma atividade ainda</span>"

        t_count = sum(len(mi.get(m["key"],[])) for m in g["members"])
        card = []
        card.append("<div class='group-card " + g["cls"] + "'>")
        card.append("<div class='group-header'><h2>" + g["icon"] + " GRUPO " + str(g["num"]) + "</h2>")
        card.append("<span class='group-xp'>" + str(len(g["members"])) + " membros · " + str(t_count) + " tickets</span></div>")
        subjects = g.get("subjects", [])
        if subjects:
            tags = "".join("<span class='subj-tag'>" + s + "</span>" for s in subjects)
            card.append("<div class='group-subjects'><span class='subj-label'>Assuntos:</span>" + tags + "</div>")
        card.append("<div class='group-body'>" + "".join(mparts) + "</div>")
        card.append("<div class='group-stats'>" + pills_html + "</div>")
        card.append("</div>")
        cards.append("".join(card))

    em   = stats.get("Em andamento", 0)
    nao  = sum(v for k,v in stats.items() if norm(k) == "nao avancou")
    ag   = stats.get("Aguardando Desenvolvimento", 0)
    ni   = sum(v for k,v in stats.items() if norm(k) == "nao iniciado")
    done = sum(v for k,v in stats.items() if norm(k) == "concluido")

    html = []
    html.append("<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'>")
    html.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html.append("<title>CRC Dashboard — Voltando às Origens</title>")
    html.append("<style>" + CSS + "</style></head><body>")
    html.append("<header>")
    html.append("<h1>🏍️ &nbsp;CRC — Voltando às Origens &nbsp;🏍️</h1>")
    html.append("<p>Acompanhamento de casos por grupo · Projeto Centralização - Reclamações - Clientes</p>")
    html.append("<div class='header-meta'>")
    html.append("<div class='meta-badge'>Total <span>" + str(total) + "</span></div>")
    html.append("<div class='meta-badge'>Em andamento <span style='color:#56d364'>" + str(em) + "</span></div>")
    html.append("<div class='meta-badge'>Concluído <span style='color:#3fb950'>" + str(done) + "</span></div>")
    html.append("<div class='meta-badge'>Não avançou <span style='color:#f85149'>" + str(nao) + "</span></div>")
    html.append("<div class='meta-badge'>Ag. Dev <span style='color:#79c0ff'>" + str(ag) + "</span></div>")
    html.append("<div class='meta-badge'>Não iniciado <span style='color:#e3b341'>" + str(ni) + "</span></div>")
    html.append("<div class='live-badge'><span class='live-dot'></span>📅 " + now + " (Horário SP)</div>")
    html.append("</div></header>")
    html.append("<div class='grid'>" + "".join(cards) + "</div>")
    html.append("<div class='footer'>🔄 Atualizado automaticamente a cada 30 min via GitHub Actions · " + now + " (UTC-3 São Paulo)</div>")
    html.append("</body></html>")
    return "".join(html)

def push_file(path, content_str, msg, sha=None):
    hd = {"Authorization": "token " + GH_PAT,
          "Accept": "application/vnd.github.v3+json",
          "Content-Type": "application/json"}
    url = "https://api.github.com/repos/" + REPO + "/contents/" + path
    if not sha:
        r = requests.get(url, headers=hd)
        sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": msg,
               "content": base64.b64encode(content_str.encode("utf-8")).decode(),
               "branch": "main"}
    if sha: payload["sha"] = sha
    r = requests.put(url, headers=hd, json=payload)
    r.raise_for_status()
    print("OK " + path + " -> " + str(r.status_code))

if __name__ == "__main__":
    print("Buscando issues do Jira...")
    issues = fetch_issues()
    print(str(len(issues)) + " issues encontradas")
    mi = build_map(issues)
    print("Gerando HTML...")
    html = generate_html(issues, mi)
    tz_sp = timezone(timedelta(hours=-3))
    ts = datetime.now(tz_sp).strftime("%d/%m/%Y %H:%M")
    print("Publicando...")
    push_file("index.html", html, "chore: dashboard " + ts)
    print("Concluido!")
