# Pesquisa 1 — Viabilidade: Micro SaaS tipo Instant Domain Search

Data: 2026-02-13

## Referência: instantdomainsearch.com

| Feature | Detalhe |
|---------|---------|
| Busca em tempo real | Resultados em <25ms enquanto digita |
| 800+ TLDs | .com, .net, .ai, .io, .dev, .app, etc. |
| Sugestoes por IA | Gera nomes alternativos criativos |
| Marketplace premium | Dominios premium para venda |
| Comparacao de precos | Precos entre registradores |
| WHOIS lookup | Historico de proprietarios |
| Monetizacao | Afiliados + registrador ICANN acreditado |
| Stack tecnico | Rust (segmentacao), fastText (traducoes), infra dedicada |

## O que ja temos e o que podemos reaproveitar

| Componente nosso | Reaproveitavel? | Observacao |
|-------------------|:-:|---|
| `check_domain()` — logica RDAP | **Sim** | Core funcional, precisa virar API |
| `get_rdap_url()` — mapeamento de TLDs | **Sim** | Precisa expandir para mais TLDs |
| Retry com backoff | **Sim** | Essencial para producao |
| `generate_domains()` — gerador de padroes | **Parcial** | Util como base para sugestoes |
| `gen_domains.py` — gerador em massa | **Parcial** | Logica de combinacao reaproveitavel |
| CLI (argparse, output texto) | **Nao** | Precisa de web API + frontend |

## Problema central: VELOCIDADE

Nosso RDAP leva ~500ms por dominio. O instantdomainsearch retorna em <25ms. Como eles conseguem:

1. **Zone files** — Verisign vende dumps diarios do .com (~$10k/ano + contrato ICANN). Com isso, checam localmente em microsegundos
2. **DNS como pre-filtro** — Uma query DNS leva ~20-50ms e resolve a maioria dos casos
3. **Cache agressivo** — Dominios populares ficam em cache
4. **Streaming** — WebSocket envia resultados conforme chegam, sem esperar todos

## Arquitetura proposta para MVP

```
+---------------------------------------------+
|  Frontend (Next.js / React)                  |
|  - Search bar com debounce                   |
|  - Resultados em tempo real via WebSocket     |
|  - Links afiliados para registradores         |
+---------------+-----------------------------+
                |
+---------------v-----------------------------+
|  Backend API (FastAPI / Python)              |
|  - Endpoint /search?q=domain                 |
|  - WebSocket /ws/search                      |
|  - Pipeline: DNS -> Cache -> RDAP            |
|  - Sugestoes: variantes, sinonimos, IA       |
+---------------+-----------------------------+
                |
+---------------v-----------------------------+
|  Camada de dados                             |
|  - Redis/SQLite: cache de resultados (TTL)   |
|  - DNS resolver: pre-filtro rapido (~30ms)   |
|  - RDAP: confirmacao final (~500ms)          |
|  - Fila de sugestoes assincronas             |
+---------------------------------------------+
```

**Truque-chave**: Usar DNS como primeira camada. Se o dominio tem registro DNS -> registrado (resposta em ~30ms). Se nao tem -> confirmar via RDAP. Isso cobre ~90% dos casos rapidamente.

## Veredicto

| Aspecto | Avaliacao |
|---------|-----------|
| E possivel? | **Sim**, um MVP funcional e totalmente viavel |
| Refazer tudo? | **Nao** — o core RDAP e reaproveitavel como modulo |
| Dificuldade | **Media-alta** — backend e a parte mais facil, o desafio e o frontend em tempo real + velocidade |
| Monetizacao | Links afiliados (Namecheap, GoDaddy pagam $3-5 por dominio vendido) |
| Diferencial possivel | Foco em nichos (AI domains, dev domains), sugestoes mais inteligentes, UX brasileira |

## O que precisaria ser criado do zero

1. **Web API** (FastAPI) — expor `check_domain` como endpoint REST/WebSocket
2. **DNS pre-filter** — camada rapida usando `socket.getaddrinfo()` ou DoH
3. **Cache** — Redis ou SQLite com TTL para evitar rechecks
4. **Frontend** — React/Next.js com busca em tempo real
5. **Sugestoes** — motor de geracao de nomes (evolucao do `generate_domains`)
6. **Deploy** — VPS com dominio proprio

## Estimativa

MVP funcional: ~2-4 semanas de desenvolvimento.

---

## TLDs viaveis alem de .com/.net/.org

Nosso codigo ja tem o fallback `rdap.org` que funciona como bootstrap para qualquer TLD com servidor RDAP registrado na IANA:

| TLD | Servidor | Velocidade | Confiabilidade |
|-----|----------|:----------:|:--------------:|
| `.com` | Verisign direto | ~500ms | Alta |
| `.net` | Verisign direto | ~500ms | Alta |
| `.org` | rdap.org -> PIR | ~800ms | Alta |
| `.io` | rdap.org -> redireciona | ~1000ms | Boa |
| `.dev` | rdap.org -> Google | ~900ms | Boa |
| `.app` | rdap.org -> Google | ~900ms | Boa |
| `.co` | rdap.org -> redireciona | ~1000ms | **Baixa** (ver nota) |
| `.ai` | rdap.org -> redireciona | ~1200ms | Media |
| `.xyz` | rdap.org -> redireciona | ~1000ms | Boa |

**Conclusao**: Nao estamos limitados a 3 TLDs. Podemos oferecer 8-10 populares sem esforco extra — so adicionando ao dicionario de endpoints.

### Alerta: falsos positivos no .co via RDAP

O RDAP via `rdap.org` para `.co` pode dar **falsos positivos** — retorna HTTP 404 (indicando disponivel) mas o dominio ja esta registrado. Confirmado em testes reais: `domainiq.co` e `nameiq.co` apareceram como disponiveis no RDAP mas estavam registrados. Para TLDs que passam pelo bootstrap `rdap.org`, o check mais confiavel e direto no registrador (Namecheap, GoDaddy, etc.). Apenas `.com` e `.net` (Verisign direto) tem confiabilidade alta.

## Diferencial: Clean UX

O instantdomainsearch e poluido — 800 TLDs, marketplace premium, ads, precos, tudo ao mesmo tempo. Nossa abordagem "less is more":

- **Busca simples**: digita o nome, ve se esta disponivel nos TLDs que importam
- **Poucos TLDs curados** (8-10 relevantes) em vez de 800
- **Sem ruido**: sem premium domains, sem marketplace, sem WHOIS
- **Um botao "registrar"** por dominio -> link afiliado direto
- **Velocidade nao e prioridade no MVP** — foco em experiencia limpa e util

Analogia: Google vs Yahoo nos anos 2000 — uma caixa de busca limpa vs portal lotado.
