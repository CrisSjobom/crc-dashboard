import requests, base64, os, sys
from requests.auth import HTTPBasicAuth
from datetime import datetime
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

JIRA_EMAIL = os.environ['JIRA_EMAIL']
JIRA_TOKEN = os.environ['JIRA_TOKEN']
GH_PAT     = os.environ['GH_PAT']
REPO       = 'CrisSjobom/crc-dashboard'
PROJECT    = 'Centraliza\u00e7\u00e3o - Reclama\u00e7\u00f5es - Clientes'

ASSIGNEE_MAP = [
    ('Andr\u00e9 Porto','Andr\u00e9 Porto'),('Andr\u00e9 Luiz','Andr\u00e9 Porto'),
    ('Ricardo Suzuki','Ricardo Suzuki'),('Ricardo Eiji','Ricardo Suzuki'),
    ('B\u00e1rbara H\u00fclse','B\u00e1rbara H\u00fclse'),
    ('Cristtiane Sjobom','Cristtiane Sjobom'),('Cristtiane Moreira','Cristtiane Sjobom'),
    ('Rafael Yoneta','Rafael Yoneta'),
    ('yan.garcia','Yan Garcia'),('Yan Almeida','Yan Garcia'),
    ('Faruk Abdo','Faruk Feres'),('Faruk','Faruk Feres'),
    ('Gerbert Santos','Gerbert Santos'),
    ('Pedro Henrique Stival','Pedro Stival'),
    ('Bruno','Bruno Martins'),
    ('Ricardo Duque','Ricardo Goes'),
    ('Rafael Libano','Rafael Rodrigues'),('Rafael L\u00edbano','Rafael Rodrigues'),
    ('Adriano Rodrigues','Adriano Rodrigues'),('Adriano Silva','Adriano Rodrigues'),
    ('Priscila Mara','Priscila Mara'),
    ('Leandro Lustosa','Leandro Lustosa'),
    ('Jean Fontoura','Jean Fontoura'),('Jean Rosado','Jean Fontoura'),
    ('felipe.fernandes','Felipe Fernandes'),('Felipe Hermes','Felipe Fernandes'),
    ('arthur.iensen','Arthur Iensen'),('Arthur Ribeiro','Arthur Iensen'),
    ('Yasmin Jannuzzi','Yasmin Cozaciuc'),('Yasmin Di Franco','Yasmin Cozaciuc'),
    ('William Bartos','William Bartos'),
    ('Phillipe Soares','Phillipe Rangel'),
]

GROUPS = [
    {'num':1,'cls':'g1','icon':'\U0001f680','members':[
        {'display':'Andr\u00e9 Porto','key':'Andr\u00e9 Porto','initials':'AN'},
        {'display':'Ricardo Suzuki','key':'Ricardo Suzuki','initials':'RC'},
        {'display':'B\u00e1rbara H\u00fclse','key':'B\u00e1rbara H\u00fclse','initials':'BH'},
        {'display':"Jo\u00e3o Sant'Anna",'key':"Jo\u00e3o Sant'Anna",'initials':'JO','nao_atuou':True,'destaque':True},
    ]},
    {'num':2,'cls':'g2','icon':'\u26a1','members':[
        {'display':'Cristtiane Sjobom','key':'Cristtiane Sjobom','initials':'CS'},
        {'display':'Rafael Yoneta','key':'Rafael Yoneta','initials':'RY'},
        {'display':'Yan Garcia','key':'Yan Garcia','initials':'YG'},
        {'display':'Faruk Feres','key':'Faruk Feres','initials':'FF'},
    ]},
    {'num':3,'cls':'g3','icon':'\U0001f525','members':[
        {'display':'Gerbert Santos','key':'Gerbert Santos','initials':'GS'},
        {'display':'Pedro Stival','key':'Pedro Stival','initials':'PS'},
        {'display':'Bruno Martins','key':'Bruno Martins','initials':'BM'},
        {'display':'Isabela Ara\u00fajo','key':'Isabela Ara\u00fajo','initials':'IA','nao_atuou':True},
    ]},
    {'num':4,'cls':'g4','icon':'\U0001f48e','members':[
        {'display':'Ricardo Goes','key':'Ricardo Goes','initials':'RG'},
        {'display':'Rafael Rodrigues','key':'Rafael Rodrigues','initials':'RR'},
        {'display':'Adriano Rodrigues','key':'Adriano Rodrigues','initials':'AR'},
        {'display':'Priscila Mara','key':'Priscila Mara','initials':'PM'},
    ]},
    {'num':5,'cls':'g5','icon':'\u2694\ufe0f','members':[
        {'display':'Leandro Lustosa','key':'Leandro Lustosa','initials':'LL'},
        {'display':'Jean Fontoura','key':'Jean Fontoura','initials':'JF'},
        {'display':'Felipe Fernandes','key':'Felipe Fernandes','initials':'FH'},
        {'display':'Arthur Iensen','key':'Arthur Iensen','initials':'AI'},
    ]},
    {'num':6,'cls':'g6','icon':'\U0001f4a0','members':[
        {'display':'Yasmin Cozaciuc','key':'Yasmin Cozaciuc','initials':'YC'},
        {'display':'William Bartos','key':'William Bartos','initials':'WB','nao_atuou':True},
        {'display':'Phillipe Rangel','key':'Phillipe Rangel','initials':'PR'},
    ]},
]

STATUS_BADGE = {
    'Em andamento':('b-em-andamento','Em andamento'),
    'N\u00e3o avan\u00e7ou':('b-nao-avancou','N\u00e3o avan\u00e7ou'),
    'N\u00e3o iniciado':('b-nao-iniciado','N\u00e3o iniciado'),
    'Aguardando Desenvolvimento':('b-ag-dev','Ag. Desenvolvimento'),
    'Pend\u00eancia com outro time':('b-pendencia','Pend\u00eancia c/ outro time'),
    'Aguardando Cliente':('b-ag-cliente','Aguardando Cliente'),
}

def resolve(name):
    if not name: return None
    for frag, key in ASSIGNEE_MAP:
        if frag.lower() in name.lower(): return key
    return None

def badge(s):
    return STATUS_BADGE.get(s, ('b-nao-iniciado', s or '?'))

def fetch():
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    h = {'Accept':'application/json','Content-Type':'application/json'}
    r = requests.post('https://mottu-team.atlassian.net/rest/api/3/search/jql', headers=h, auth=auth, json={
        'jql': f'project = "{PROJECT}" AND assignee is not EMPTY ORDER BY key ASC',
        'maxResults':100,'fields':['summary','status','assignee']
    })
    r.raise_for_status()
    return r.json()['issues']

def build_map(issues):
    m = {}
    for i in issues:
        f = i['fields']
        k = resolve(f['assignee']['displayName'] if f.get('assignee') else None)
        if k:
            m.setdefault(k,[]).append({'key':i['key'],'summary':f['summary'],
                'status':f['status']['name'] if f.get('status') else '?',
                'url':f"https://mottu-team.atlassian.net/browse/{i['key']}"})
    return m

CSS = (
    "* { margin: 0; padding: 0; box-sizing: border-box; }"
    "body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; }"
    "header { background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%); border-bottom: 2px solid #21262d; padding: 24px 32px; text-align: center; }"
    "header h1 { font-size: 1.8rem; font-weight: 700; letter-spacing: 1px; color: #f0f6fc; }"
    "header p { color: #8b949e; margin-top: 6px; font-size: 0.9rem; }"
    ".header-meta { display: flex; justify-content: center; gap: 24px; margin-top: 16px; flex-wrap: wrap; align-items: center; }"
    ".meta-badge { background: #21262d; border: 1px solid #30363d; border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; color: #8b949e; }"
    ".meta-badge span { color: #f0f6fc; font-weight: 600; }"
    ".live-badge { display: inline-flex; align-items: center; gap: 6px; background: #0d2a0d; border: 1px solid #238636; border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; color: #56d364; }"
    ".live-dot { width: 8px; height: 8px; background: #56d364; border-radius: 50%; animation: pulse 2s infinite; }"
    "@keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.4} }"
    ".grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 28px 32px; max-width: 1600px; margin: 0 auto; }"
    ".group-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; }"
    ".group-header { padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; }"
    ".group-header h2 { font-size: 1.05rem; font-weight: 700; letter-spacing: 0.5px; }"
    ".group-xp { background: rgba(0,0,0,0.25); border-radius: 20px; padding: 3px 12px; font-size: 0.75rem; font-weight: 600; color: #fff; }"
    ".g1 .group-header { background: linear-gradient(135deg, #e8510a, #c0410a); }"
    ".g2 .group-header { background: linear-gradient(135deg, #0a7c6e, #057a62); }"
    ".g3 .group-header { background: linear-gradient(135deg, #d4920a, #b07a08); }"
    ".g4 .group-header { background: linear-gradient(135deg, #1560bd, #0f4d9c); }"
    ".g5 .group-header { background: linear-gradient(135deg, #7a3fbf, #612fb0); }"
    ".g6 .group-header { background: linear-gradient(135deg, #3a5fa8, #2d4d8e); }"
    ".group-body { padding: 14px 16px; flex: 1; }"
    ".member { margin-bottom: 10px; border: 1px solid #21262d; border-radius: 8px; overflow: hidden; }"
    ".member-name { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #0d1117; font-size: 0.82rem; font-weight: 600; color: #c9d1d9; border-bottom: 1px solid #21262d; }"
    ".member-name .avatar { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; flex-shrink: 0; }"
    ".g1 .avatar { background: #e8510a; } .g2 .avatar { background: #0a7c6e; }"
    ".g3 .avatar { background: #d4920a; } .g4 .avatar { background: #1560bd; }"
    ".g5 .avatar { background: #7a3fbf; } .g6 .avatar { background: #3a5fa8; }"
    ".tickets { padding: 6px 8px; display: flex; flex-direction: column; gap: 4px; }"
    ".ticket { display: flex; align-items: center; gap: 8px; padding: 5px 8px; background: #161b22; border-radius: 6px; font-size: 0.75rem; }"
    ".ticket-key { font-weight: 700; color: #58a6ff; white-space: nowrap; font-size: 0.72rem; min-width: 48px; }"
    ".ticket-key a { color: inherit; text-decoration: none; } .ticket-key a:hover { text-decoration: underline; }"
    ".ticket-summary { color: #8b949e; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }"
    ".badge { border-radius: 4px; padding: 2px 7px; font-size: 0.65rem; font-weight: 700; white-space: nowrap; flex-shrink: 0; text-transform: uppercase; letter-spacing: 0.3px; }"
    ".b-em-andamento { background: #1a4a1a; color: #56d364; border: 1px solid #238636; }"
    ".b-nao-avancou { background: #4a1a1a; color: #f85149; border: 1px solid #da3633; }"
    ".b-nao-iniciado { background: #3a3a1a; color: #e3b341; border: 1px solid #9e6a03; }"
    ".b-ag-dev { background: #1a2f4a; color: #79c0ff; border: 1px solid #1f6feb; }"
    ".b-ag-cliente { background: #2a1f3a; color: #d2a8ff; border: 1px solid #8957e5; }"
    ".b-pendencia { background: #3a1f1f; color: #ffa657; border: 1px solid #bd561d; }"
    ".b-nao-atuou { background: #1c1c1c; color: #6e7681; border: 1px solid #30363d; }"
    ".joao-highlight { border: 2px solid #f5c518 !important; box-shadow: 0 0 12px rgba(245,197,24,0.3); animation: golden-pulse 2.5s ease-in-out infinite; }"
    "@keyframes golden-pulse { 0%,100%{box-shadow:0 0 8px rgba(245,197,24,0.25)}50%{box-shadow:0 0 20px rgba(245,197,24,0.55)} }"
    ".badge-joao { background: linear-gradient(135deg, #f5c518, #d4a017); color: #000; border: none; font-weight: 800; }"
    ".no-ticket { padding: 8px; font-size: 0.72rem; color: #484f58; font-style: italic; }"
    ".group-stats { display: flex; gap: 6px; padding: 10px 16px; border-top: 1px solid #21262d; background: #0d1117; flex-wrap: wrap; }"
    ".stat-pill { border-radius: 10px; padding: 2px 8px; font-size: 0.65rem; font-weight: 600; }"
    ".footer { text-align: center; padding: 20px; color: #484f58; font-size: 0.75rem; border-top: 1px solid #21262d; margin-top: 8px; }"
    "@media (max-width: 1100px) { .grid { grid-template-columns: repeat(2, 1fr); } }"
    "@media (max-width: 700px)  { .grid { grid-template-columns: 1fr; padding: 16px; } }"
)

def generate_html(issues, mi):
    stats = Counter(i['fields']['status']['name'] for i in issues if i['fields'].get('status'))
    total = len(issues)
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    cards = ''
    for g in GROUPS:
        mhtml = ''
        g_em=g_nao=g_ag=g_pend=g_cli=0
        for mem in g['members']:
            nao_atuou = mem.get('nao_atuou', False)
            destaque  = mem.get('destaque', False)
            extra = ' joao-highlight' if destaque else ''
            av_s = ' style=\"background:#f5c518;color:#000\"' if destaque else ''
            star = ' <span>&#11088;</span>' if destaque else ''
            if nao_atuou:
                b = '<span class=\"badge badge-joao\">N&atilde;o Atuou</span>' if destaque else '<span class=\"badge b-nao-atuou\">N&atilde;o Atuou</span>'
                mhtml += f'<div class=\"member{extra}\"><div class=\"member-name\"><div class=\"avatar\"{av_s}>{mem[\"initials\"]}</div> {mem[\"display\"]}{star}</div><div class=\"tickets\"><div class=\"ticket\"><span class=\"ticket-key\">&mdash;</span><span class=\"ticket-summary\">Nenhum caso atribu&iacute;do</span>{b}</div></div></div>'
            else:
                ts = mi.get(mem['key'], [])
                if ts:
                    th = ''
                    for t in ts:
                        bcls,blbl = badge(t['status'])
                        if bcls=='b-em-andamento': g_em+=1
                        elif bcls=='b-nao-avancou': g_nao+=1
                        elif bcls=='b-ag-dev': g_ag+=1
                        elif bcls=='b-pendencia': g_pend+=1
                        elif bcls=='b-ag-cliente': g_cli+=1
                        s = t['summary'][:55]+'...' if len(t['summary'])>55 else t['summary']
                        th += f'<div class=\"ticket\"><span class=\"ticket-key\"><a href=\"{t[\"url\"]}\" target=\"_blank\">{t[\"key\"]}</a></span><span class=\"ticket-summary\">{s}</span><span class=\"badge {bcls}\">{blbl}</span></div>'
                    mhtml += f'<div class=\"member\"><div class=\"member-name\"><div class=\"avatar\">{mem[\"initials\"]}</div> {mem[\"display\"]}</div><div class=\"tickets\">{th}</div></div>'
                else:
                    mhtml += f'<div class=\"member\"><div class=\"member-name\"><div class=\"avatar\">{mem[\"initials\"]}</div> {mem[\"display\"]}</div><div class=\"no-ticket\">Nenhum caso ainda</div></div>'
        pills=''
        if g_em:   pills+=f'<span class=\"stat-pill\" style=\"background:#1a4a1a;color:#56d364\">&check; {g_em} em andamento</span>'
        if g_nao:  pills+=f'<span class=\"stat-pill\" style=\"background:#4a1a1a;color:#f85149\">&times; {g_nao} n&atilde;o avan&ccedil;ou</span>'
        if g_ag:   pills+=f'<span class=\"stat-pill\" style=\"background:#1a2f4a;color:#79c0ff\">&#9203; {g_ag} ag. dev</span>'
        if g_pend: pills+=f'<span class=\"stat-pill\" style=\"background:#3a1f1f;color:#ffa657\">&#9888; {g_pend} pend&ecirc;ncia</span>'
        if g_cli:  pills+=f'<span class=\"stat-pill\" style=\"background:#2a1f3a;color:#d2a8ff\">&#128100; {g_cli} ag. cliente</span>'
        if not pills: pills='<span style=\"color:#484f58;font-size:0.72rem\">Nenhuma atividade ainda</span>'
        tc=sum(len(mi.get(m['key'],[])) for m in g['members'])
        cards+=f'<div class=\"group-card {g[\"cls\"]}\"><div class=\"group-header\"><h2>{g[\"icon\"]} GRUPO {g[\"num\"]}</h2><span class=\"group-xp\">{len(g[\"members\"])} membros &middot; {tc} tickets</span></div><div class=\"group-body\">{mhtml}</div><div class=\"group-stats\">{pills}</div></div>'
    em=stats.get('Em andamento',0); nao=stats.get('N\u00e3o avan\u00e7ou',0)
    ag=stats.get('Aguardando Desenvolvimento',0); ni=stats.get('N\u00e3o iniciado',0); pd=stats.get('Pend\u00eancia com outro time',0)
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CRC Dashboard</title><style>{CSS}</style></head><body><header><h1>&#x1F3CD;&#xFE0F; &nbsp;CRC &mdash; Voltando &agrave;s Origens &nbsp;&#x1F3CD;&#xFE0F;</h1><p>Acompanhamento de casos por grupo &middot; Projeto Centraliza&ccedil;&atilde;o - Reclama&ccedil;&otilde;es - Clientes</p><div class="header-meta"><div class="meta-badge">Total <span>{total}</span></div><div class="meta-badge">Em andamento <span style="color:#56d364">{em}</span></div><div class="meta-badge">N&atilde;o avan&ccedil;ou <span style="color:#f85149">{nao}</span></div><div class="meta-badge">Ag. Dev <span style="color:#79c0ff">{ag}</span></div><div class="meta-badge">N&atilde;o iniciado <span style="color:#e3b341">{ni}</span></div><div class="meta-badge">Pend&ecirc;ncias <span style="color:#ffa657">{pd}</span></div><div class="live-badge"><span class="live-dot"></span>Atualizado {now}</div></div></header><div class="grid">{cards}</div><div class="footer">&#x1F504; Atualizado automaticamente a cada 30 min via GitHub Actions &middot; {now}</div></body></html>'''

def push_file(path, content, msg):
    h = {'Authorization':f'token {GH_PAT}','Accept':'application/vnd.github.v3+json','Content-Type':'application/json'}
    url = f'https://api.github.com/repos/{REPO}/contents/{path}'
    r = requests.get(url, headers=h)
    sha = r.json().get('sha') if r.status_code==200 else None
    enc = base64.b64encode(content.encode('utf-8')).decode() if isinstance(content,str) else base64.b64encode(content).decode()
    p = {'message':msg,'content':enc,'branch':'main'}
    if sha: p['sha']=sha
    r = requests.put(url, headers=h, json=p); r.raise_for_status()
    print(f'  OK {path} -> {r.status_code}')

if __name__ == '__main__':
    print('Buscando Jira...')
    issues = fetch()
    mi = build_map(issues)
    print(f'{len(issues)} issues / {len(mi)} membros mapeados')
    html = generate_html(issues, mi)
    push_file('index.html', html, f'chore: dashboard {datetime.now().strftime("%d/%m/%Y %H:%M")}')
    print('Concluido!')
