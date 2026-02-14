# FindBrandDomain — Instruções para o Agente

Micro SaaS de busca de domínios disponíveis com UX minimalista. O usuário digita um nome, vê disponibilidade em tempo real nos TLDs que importam, recebe sugestões de variações e registra com um clique (link afiliado).

## Documentação do Projeto

- `docs/PRD.md` — Product Requirements Document do MVP
- `docs/projeto/pesquisa1.md` — Pesquisa de viabilidade (benchmark instantdomainsearch.com)

## Estrutura do Projeto

```
findbranddomain/
├── check_domains.py          # Motor RDAP (reaproveitado como módulo no backend)
├── gen_domains.py             # Gerador de candidatos (base para motor de sugestões)
├── termos-ai.txt              # Lista de ~160 termos para combinação
├── CLAUDE.md                  # Este arquivo
└── docs/
    ├── PRD.md                 # Especificação do MVP
    └── projeto/
        └── pesquisa1.md       # Pesquisa de viabilidade
```

## Stack do MVP

| Camada | Tecnologia |
|--------|------------|
| Frontend | Next.js 15 + React 19 + Tailwind CSS |
| i18n | next-intl (en + pt-BR) |
| Backend | FastAPI (Python) |
| Cache | Redis (TTL 1h) |
| Verificação | DNS pré-filtro → RDAP confirmação |
| Deploy | VPS (Hetzner/DigitalOcean) |

## Arquitetura

```
Frontend (Next.js) → WebSocket/REST → Backend (FastAPI) → DNS → Cache → RDAP
```

### Pipeline de verificação

1. Normalizar input (lowercase, caracteres válidos)
2. Gerar domínios para 8-10 TLDs curados
3. Checar cache Redis
4. DNS pré-filtro (~30ms) — se tem DNS → registrado
5. RDAP confirmação (~500ms) — só para domínios sem DNS
6. Cache resultado com TTL 1h
7. Gerar sugestões (prefixos, sufixos, plurais)

## Código Reaproveitável

### check_domains.py

Funções que viram módulo no backend FastAPI:

- `check_domain(domain, timeout)` → verifica um domínio via RDAP, retorna `{domain, available, status, time_ms}`
- `get_rdap_url(domain)` → resolve endpoint RDAP por TLD (Verisign direto para .com/.net)
- Retry com exponential backoff para HTTP 429

### gen_domains.py

Lógica de combinação reaproveitável para o motor de sugestões:

- Prefixos: get-, my-, try-, use-, go-
- Sufixos: -app, -hub, -hq, -dev
- Plurais, hífens, inversões

## Consulta de Domínios via CLI

Os scripts CLI continuam funcionais para testes e validação durante o desenvolvimento:

```bash
# Busca padrão
python3 check_domains.py -p "ai*.com" -t hub flow kit -n 10

# Com variantes
python3 check_domains.py -p "ai*.com" -tf termos-ai.txt --variants -n 50

# Domínios específicos
python3 check_domains.py -d exemplo.com teste.com outro.com

# JSON para pós-processamento
python3 check_domains.py -p "ai*.com" -tf termos-ai.txt --json 2>/dev/null
```

## Limites Técnicos

- RDAP: ~500ms/domínio via Verisign (.com/.net), ~800-1200ms via rdap.org (outros TLDs)
- DNS pré-filtro: ~30ms, cobre ~90% dos casos
- Rate limit: 15-20 workers simultâneos funciona bem
- Retry automático em HTTP 429 com backoff exponencial
- Falsos positivos possíveis em .co via rdap.org (confirmar no registrador)
- TLDs confiáveis: .com, .net (Verisign direto). Boa confiabilidade: .org, .io, .dev, .app, .xyz

## Lições Aprendidas

- Prefixo `ai` extremamente saturado; `ais` tem mais disponibilidade
- Plurais importam: guide ≠ guides — sempre testar ambos
- Domínios com hífen: mais disponíveis, menos brandáveis
- Domínios curtos (5-8 chars) são mais valiosos
- Verisign direto é ~2x mais rápido que bootstrap rdap.org
