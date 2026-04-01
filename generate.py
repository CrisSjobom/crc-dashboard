import requests, base64, os, sys
from requests.auth import HTTPBasicAuth
from datetime import datetime
from collections import Counter

JIRA_EMAIL = os.environ['JIRA_EMAIL']
JIRA_TOKEN = os.environ['JIRA_TOKEN']
GH_PAT     = os.environ['GH_PAT']
REPO       = 'CrisSjobom/crc-dashboard'
PROJECT    = 'Centralização - Reclamações - Clientes'

ASSIGNEE_MAP = [
    ('André Porto','André Porto'),('André Luiz','André Porto'),
    ('Ricardo Suzuki','Ricardo Suzuki'),('Ricardo Eiji','Ricardo Suzuki'),
    ('Bárbara Hülse','Bárbara Hülse'),
    ('Cristtiane Sjobom','Cristtiane Sjobom'),('Cristtiane Moreira','Cristtiane Sjobom'),
    ('Rafael Yoneta','Rafael Yoneta'),
    ('yan.garcia','Yan Garcia'),('Yan Almeida','Yan Garcia'),
    ('Faruk Abdo','Faruk Feres'),('Faruk','Faruk Feres'),
    ('Gerbert Santos','Gerbert Santos'),
    ('Pedro Henrique Stival','Pedro Stival'),
    ('Bruno','Bruno Martins'),
    ('Ricardo Duque','Ricardo Goes'),
    ('Rafael Libano','Rafael Rodrigues'),('Rafael Líbano','Rafael Rodrigues'),
    ('Adriano Rodrigues','Adriano Rodrigues'),('Adriano Silva','Adriano Rodrigues'),
    ('Priscila Mara','Priscila Mara'),
    ('Leandro Lustosa','Leandro Lustosa'),
    ('Jean Fontoura','Jean Fontoura'),('Jean Rosado','Jean Fontoura'),
    ('felipe.fernandes','Felipe Fernandes'),('Felipe Hermes','Felipe Fernandes'),
    ('arthur.iensen','Arthur Iensen'),('Arthur Ribeiro','Arthur Iensen'),
    ('Yasmin Jannuzzi','Yasmin Cozaciuc'),('Yasmin Di Franco','Yasmin Cozaciuc'),
    ('William Bartos','William Bartos'),
    ('Phillipe Soares','Phillipe Rangel'),
    ("João Sant'Anna","João Sant'Anna"),('João Victor',"João Sant'Anna"),('joao.santanna',"João Sant'Anna"),
]

GROUPS = [
    {'num':1,'cls':'g1','icon':'🚀','members':[
        {'display':'André Porto',     'key':'André Porto',     'ini':'AN'},
        {'display':'Ricardo Suzuki',  'key':'Ricardo Suzuki',  'ini':'RC'},
        {'display':'Bárbara Hülse',   'key':'Bárbara Hülse',   'ini':'BH'},
        {'display':"João Sant'Anna",  'key':"João Sant'Anna",  'ini':'JO','dest':True},
    ]},
    {'num':2,'cls':'g2','icon':'⚡','members':[
        {'display':'Cristtiane Sjobom','key':'Cristtiane Sjobom','ini':'CS'},
        {'display':'Rafael Yoneta',   'key':'Rafael Yoneta',   'ini':'RY'},
        {'display':'Yan Garcia',      'key':'Yan Garcia',      'ini':'YG'},
        {'display':'Faruk Feres',     'key':'Faruk Feres',     'ini':'FF'},
    ]},
    {'num':3,'cls':'g3','icon':'🔥','members':[
        {'display':'Gerbert Santos',  'key':'Gerbert Santos',  'ini':'GS'},
        {'display':'Pedro Stival',    'key':'Pedro Stival',    'ini':'PS'},
        {'display':'Bruno Martins',   'key':'Bruno Martins',   'ini':'BM'},
        {'display':'Isabela Araújo',  'key':'Isabela Araújo',  'ini':'IA','nao_atuou':True},
    ]},
    {'num':4,'cls':'g4','icon':'💎','members':[
        {'display':'Ricardo Goes',      'key':'Ricardo Goes',      'ini':'RG'},
        {'display':'Rafael Rodrigues',  'key':'Rafael Rodrigues',  'ini':'RR'},
        {'display':'Adriano Rodrigues', 'key':'Adriano Rodrigues', 'ini':'AR'},
        {'display':'Priscila Mara',     'key':'Priscila Mara',     'ini':'PM'},
    ]},
    {'num':5,'cls':'g5','icon':'⚔️','members':[
        {'display':'Leandro Lustosa',  'key':'Leandro Lustosa',  'ini':'LL'},
        {'display':'Jean Fontoura',    'key':'Jean Fontoura',    'ini':'JF'},
        {'display':'Felipe Fernandes', 'key':'Felipe Fernandes', 'ini':'FH'},
        {'display':'Arthur Iensen',    'key':'Arthur Iensen',    'ini':'AI'},
    ]},
    {'num':6,'cls':'g6','icon':'💠','members':[
        {'display':'Yasmin Cozaciuc', 'key':'Yasmin Cozaciuc', 'ini':'YC'},
        {'display':'William Bartos',  'key':'William Bartos',  'ini':'WB','nao_atuou':True},
        {'display':'Phillipe Rangel', 'key':'Phillipe Rangel', 'ini':'PR'},
    ]},
]

STATUS_BADGE = {
    'Em andamento':               ('b-em-andamento', 'Em andamento'),
    'Não avançou':                ('b-nao-avancou',  'Não avançou'),
    'Não iniciado':               ('b-nao-iniciado', 'Não iniciado'),
    'Aguardando Desenvolvimento': ('b-ag-dev',       'Ag. Desenvolvimento'),
    'Pendência com outro time':   ('b-pendencia',    'Pendência c/ outro time'),
    'Aguardando Cliente':         ('b-ag-cliente',   'Aguardando Cliente'),
    'Concluído':                  ('b-concluido',    'Concluído'),
    'Concluido':                  ('b-concluido',    'Concluído'),
}

def resolve(name):
    if not name: return None
    for frag, key in ASSIGNEE_MAP:
        if frag.lower() in name.lower(): return key
    return None

def get_badge(s):
    return STATUS_BADGE.get(s, ('b-outro', s or '?'))

def fetch_issues():
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    h = {'Accept':'application/json','Content-Type':'application/json'}
    r = requests.post(
        'https://mottu-team.atlassian.net/rest/api/3/search/jql',
        headers=h, auth=auth,
        json={
            'jql': 'project = "' + PROJECT + '" AND assignee is not EMPTY ORDER BY key ASC',
            'maxResults': 100,
            'fields': ['summary','status','assignee']
        }
    )
    r.raise_for_status()
    return r.json()['issues']

def build_map(issues):
    m = {}
    for i in issues:
        f = i['fields']
        k = resolve(f['assignee']['displayName'] if f.get('assignee') else None)
        if k:
            m.setdefault(k, []).append({
                'key': i['key'],
                'summary': f['summary'],
                'status': f['status']['name'] if f.get('status') else '?',
                'url': 'https://mottu-team.atlassian.net/browse/' + i['key']
            })
    return m

def ticket_html(t):
    bcls, blbl = get_badge(t['status'])
    s = t['summary'][:55] + '...' if len(t['summary']) > 55 else t['summary']
    return (
        '<div class="ticket">'
        '<span class="ticket-key"><a href="' + t['url'] + '" target="_blank">' + t['key'] + '</a></span>'
        '<span class="ticket-summary">' + s + '</span>'
        '<span class="badge ' + bcls + '">' + blbl + '</span>'
        '</div>'
    )

def member_html(mem, mi):
    nao_atuou = mem.get('nao_atuou', False)
    dest      = mem.get('dest', False)
    ini       = mem['ini']
    display   = mem['display']
    key       = mem['key']
    tickets   = mi.get(key, [])

    if dest:
        av   = '<div class="avatar" style="background:#f5c518;color:#000">' + ini + '</div>'
        star = ' <span>&#11088;</span>'
        mcls = 'member joao-highlight'
    else:
        av   = '<div class="avatar">' + ini + '</div>'
        star = ''
        mcls = 'member'

    name_row = '<div class="member-name">' + av + ' ' + display + star + '</div>'

    if nao_atuou:
        tick = (
            '<div class="tickets"><div class="ticket">'
            '<span class="ticket-key">&mdash;</span>'
            '<span class="ticket-summary">Nenhum caso atribu&iacute;do</span>'
            '<span class="badge b-nao-atuou">N&atilde;o Atuou</span>'
            '</div></div>'
        )
    elif tickets:
        tick = '<div class="tickets">' + ''.join(ticket_html(t) for t in tickets) + '</div>'
    elif dest:
        tick = (
            '<div class="tickets"><div class="ticket">'
            '<span class="ticket-key">&mdash;</span>'
            '<span class="ticket-summary">Nenhum caso atribu&iacute;do</span>'
            '<span class="badge badge-joao">N&atilde;o Atuou</span>'
            '</div></div>'
        )
    else:
        tick = '<div class="no-ticket">Nenhum caso atribu&iacute;do ainda</div>'

    return '<div class="' + mcls + '">' + name_row + tick + '</div>'

def group_html(g, mi):
    members_out = ''.join(member_html(m, mi) for m in g['members'])
    cnt = {'b-em-andamento':0,'b-nao-avancou':0,'b-ag-dev':0,'b-pendencia':0,'b-ag-cliente':0,'b-concluido':0}
    for mem in g['members']:
        for t in mi.get(mem['key'], []):
            bcls, _ = get_badge(t['status'])
            if bcls in cnt: cnt[bcls] += 1

    pills = []
    if cnt['b-concluido']:    pills.append('<span class="stat-pill" style="background:#0d3a2a;color:#39d353">&#10003; ' + str(cnt['b-concluido']) + ' conclu&iacute;do</span>')
    if cnt['b-em-andamento']: pills.append('<span class="stat-pill" style="background:#1a4a1a;color:#56d364">&#9654; ' + str(cnt['b-em-andamento']) + ' em andamento</span>')
    if cnt['b-nao-avancou']:  pills.append('<span class="stat-pill" style="background:#4a1a1a;color:#f85149">&#10007; ' + str(cnt['b-nao-avancou']) + ' n&atilde;o avan&ccedil;ou</span>')
    if cnt['b-ag-dev']:       pills.append('<span class="stat-pill" style="background:#1a2f4a;color:#79c0ff">&#9203; ' + str(cnt['b-ag-dev']) + ' ag. dev</span>')
    if cnt['b-pendencia']:    pills.append('<span class="stat-pill" style="background:#3a1f1f;color:#ffa657">&#9888; ' + str(cnt['b-pendencia']) + ' pend&ecirc;ncia</span>')
    if cnt['b-ag-cliente']:   pills.append('<span class="stat-pill" style="background:#2a1f3a;color:#d2a8ff">&#128100; ' + str(cnt['b-ag-cliente']) + ' ag. cliente</span>')
    pills_html = ''.join(pills) if pills else '<span style="color:#484f58;font-size:0.72rem">Nenhuma atividade ainda</span>'

    tc = sum(len(mi.get(m['key'], [])) for m in g['members'])
    header = (
        '<div class="group-header">'
        '<h2>' + g['icon'] + ' GRUPO ' + str(g['num']) + '</h2>'
        '<span class="group-xp">' + str(len(g['members'])) + ' membros &middot; ' + str(tc) + ' tickets</span>'
        '</div>'
    )
    return '<div class="group-card ' + g['cls'] + '">' + header + '<div class="group-body">' + members_out + '</div><div class="group-stats">' + pills_html + '</div></div>'

CSS = """* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; }
header { background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%); border-bottom: 2px solid #21262d; padding: 24px 32px; text-align: center; }
header h1 { font-size: 1.8rem; font-weight: 700; letter-spacing: 1px; color: #f0f6fc; }
header p { color: #8b949e; margin-top: 6px; font-size: 0.9rem; }
.header-meta { display: flex; justify-content: center; gap: 16px; margin-top: 16px; flex-wrap: wrap; align-items: center; }
.meta-badge { background: #21262d; border: 1px solid #30363d; border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; color: #8b949e; }
.meta-badge span { color: #f0f6fc; font-weight: 600; }
.live-badge { display: inline-flex; align-items: center; gap: 8px; background: #0d2a0d; border: 2px solid #238636; border-radius: 20px; padding: 6px 18px; font-size: 0.85rem; color: #56d364; font-weight: 700; }
.live-dot { width: 9px; height: 9px; background: #56d364; border-radius: 50%; animation: pulse 2s infinite; flex-shrink: 0; }
@keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.3} }
.update-sub { font-size: 0.72rem; color: #484f58; margin-top: 8px; }
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
.ticket { display: flex; align-items: center; gap: 8px; padding: 5px 8px; background: #161b22; border-radius: 6px; font-size: 0.75rem; }
.ticket-key { font-weight: 700; color: #58a6ff; white-space: nowrap; font-size: 0.72rem; min-width: 48px; }
.ticket-key a { color: inherit; text-decoration: none; } .ticket-key a:hover { text-decoration: underline; }
.ticket-summary { color: #8b949e; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.badge { border-radius: 4px; padding: 2px 7px; font-size: 0.65rem; font-weight: 700; white-space: nowrap; flex-shrink: 0; text-transform: uppercase; letter-spacing: 0.3px; }
.b-em-andamento { background: #1a4a1a; color: #56d364; border: 1px solid #238636; }
.b-nao-avancou  { background: #4a1a1a; color: #f85149; border: 1px solid #da3633; }
.b-nao-iniciado { background: #3a3a1a; color: #e3b341; border: 1px solid #9e6a03; }
.b-ag-dev       { background: #1a2f4a; color: #79c0ff; border: 1px solid #1f6feb; }
.b-ag-cliente   { background: #2a1f3a; color: #d2a8ff; border: 1px solid #8957e5; }
.b-pendencia    { background: #3a1f1f; color: #ffa657; border: 1px solid #bd561d; }
.b-nao-atuou    { background: #1c1c1c; color: #6e7681; border: 1px solid #30363d; }
.b-concluido    { background: #0d3a2a; color: #39d353; border: 1px solid #2ea043; }
.b-outro        { background: #2a2a2a; color: #aaa; border: 1px solid #444; }
.joao-highlight { border: 2px solid #f5c518 !important; box-shadow: 0 0 12px rgba(245,197,24,0.3); animation: golden-pulse 2.5s ease-in-out infinite; }
@keyframes golden-pulse { 0%,100%{box-shadow:0 0 8px rgba(245,197,24,0.25)}50%{box-shadow:0 0 20px rgba(245,197,24,0.55)} }
.badge-joao { background: linear-gradient(135deg, #f5c518, #d4a017); color: #000; border: none; font-weight: 800; }
.no-ticket { padding: 8px; font-size: 0.72rem; color: #484f58; font-style: italic; }
.group-stats { display: flex; gap: 6px; padding: 10px 16px; border-top: 1px solid #21262d; background: #0d1117; flex-wrap: wrap; }
.stat-pill { border-radius: 10px; padding: 2px 8px; font-size: 0.65rem; font-weight: 600; }
.footer { text-align: center; padding: 16px 20px; color: #6e7681; font-size: 0.78rem; border-top: 1px solid #21262d; margin-top: 8px; }
.footer strong { color: #c9d1d9; }
@media (max-width: 1100px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 700px)  { .grid { grid-template-columns: 1fr; padding: 16px; } }"""

def generate_html(issues, mi):
    stats = Counter(i['fields']['status']['name'] for i in issues if i['fields'].get('status'))
    total = len(issues)
    now   = datetime.now().strftime('%d/%m/%Y %H:%M')
    cards = ''.join(group_html(g, mi) for g in GROUPS)

    em   = stats.get('Em andamento', 0)
    nao  = stats.get('Não avançou', 0)
    ag   = stats.get('Aguardando Desenvolvimento', 0)
    ni   = stats.get('Não iniciado', 0)
    pd   = stats.get('Pendência com outro time', 0)
    conc = stats.get('Concluído', 0) + stats.get('Concluido', 0)

    return (
        '<!DOCTYPE html><html lang="pt-BR"><head>'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>CRC Dashboard — Voltando às Origens</title>'
        '<style>' + CSS + '</style></head><body>'
        '<header>'
        '<h1>&#x1F3CD;&#xFE0F;&nbsp; CRC — Voltando às Origens &nbsp;&#x1F3CD;&#xFE0F;</h1>'
        '<p>Acompanhamento de casos por grupo · Projeto Centralização - Reclamações - Clientes</p>'
        '<div class="header-meta">'
        '<div class="meta-badge">Total <span>' + str(total) + '</span></div>'
        '<div class="meta-badge">&#9654; Em andamento <span style="color:#56d364">' + str(em) + '</span></div>'
        '<div class="meta-badge">&#10003; Concluído <span style="color:#39d353">' + str(conc) + '</span></div>'
        '<div class="meta-badge">&#10007; Não avançou <span style="color:#f85149">' + str(nao) + '</span></div>'
        '<div class="meta-badge">&#9203; Ag. Dev <span style="color:#79c0ff">' + str(ag) + '</span></div>'
        '<div class="meta-badge">&#9888; Pendências <span style="color:#ffa657">' + str(pd) + '</span></div>'
        '<div class="live-badge"><span class="live-dot"></span>&#128260; Atualizado ' + now + '</div>'
        '</div>'
        '<p class="update-sub">Atualização automática a cada 30 min via GitHub Actions · dados em tempo real do Jira</p>'
        '</header>'
        '<div class="grid">' + cards + '</div>'
        '<div class="footer">&#128260; Última atualização: <strong>' + now + '</strong> · Dados sincronizados do Jira em tempo real</div>'
        '</body></html>'
    )

def push_file(path, content, msg):
    gh = {'Authorization': 'token ' + GH_PAT, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'}
    url = 'https://api.github.com/repos/' + REPO + '/contents/' + path
    r = requests.get(url, headers=gh)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {'message': msg, 'content': base64.b64encode(content.encode('utf-8')).decode(), 'branch': 'main'}
    if sha: payload['sha'] = sha
    r = requests.put(url, headers=gh, json=payload)
    r.raise_for_status()
    print('OK ' + path + ' -> ' + str(r.status_code))

if __name__ == '__main__':
    print('Buscando issues do Jira...')
    issues = fetch_issues()
    mi = build_map(issues)
    print(str(len(issues)) + ' issues / ' + str(len(mi)) + ' membros mapeados')
    html = generate_html(issues, mi)
    push_file('index.html', html, 'chore: dashboard ' + datetime.now().strftime('%d/%m/%Y %H:%M'))
    print('Concluido!')
