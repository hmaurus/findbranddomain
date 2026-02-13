# FindBrandDomain — Instruções para o Agente

Micro SaaS de busca de domínios disponíveis com UX limpa e minimalista.

## Documentação

- `docs/PRD.md` — Product Requirements Document do MVP
- `docs/projeto/pesquisa1.md` — Pesquisa de viabilidade (benchmark instantdomainsearch.com)

## Stack do MVP

- **Frontend**: Next.js 15 + React 19, Tailwind CSS, next-intl (i18n: en + pt-BR)
- **Backend**: FastAPI (Python), WebSocket + REST
- **Cache**: Redis (TTL 1h)
- **Deploy**: VPS (Hetzner/DigitalOcean)

## Código Legado Reaproveitável

Estes scripts CLI são a base para os módulos do backend:

- `check_domains.py` — Lógica RDAP core (`check_domain()`, `get_rdap_url()`, retry com backoff). Será refatorado em módulo importável para o backend FastAPI.
- `gen_domains.py` — Gerador de variações de nomes. Base para o motor de sugestões.
- `termos-ai.txt` — Lista de ~160 termos para sugestões.

## Arquitetura

```
Frontend (Next.js) → WebSocket/REST → Backend (FastAPI)
                                        ↓
                              DNS pré-filtro (~30ms)
                                        ↓
                              Cache Redis (TTL 1h)
                                        ↓
                              RDAP confirmação (~500ms)
```

## Limites Técnicos RDAP

- `.com`/`.net` via Verisign direto: ~500ms, confiabilidade alta
- `.org`, `.io`, `.dev`, `.app`, `.xyz` via rdap.org bootstrap: ~800-1200ms, confiabilidade boa
- `.co` via bootstrap: **falsos positivos** — não confiar sem validação extra
- Rate limit: 15-20 workers simultâneos funciona bem
- DNS como pré-filtro resolve ~90% dos casos em ~30ms

## Convenções

- Commits: Conventional Commits (`tipo(escopo): descrição`)
- Idioma do código: inglês
- Idioma da documentação: português (BR)
- Sem dependências externas desnecessárias
