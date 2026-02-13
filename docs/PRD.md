# PRD — FindBrandDomain MVP

**Produto**: FindBrandDomain — Busca de domínios disponíveis com UX limpa
**Versão**: MVP (v0.1)
**Data**: 2026-02-13
**Status**: Draft

---

## 1. Problema

Encontrar um bom domínio disponível é frustrante. As ferramentas existentes (instantdomainsearch.com, namecheap search, etc.) são poluídas com 800+ TLDs, marketplaces premium, anúncios e informação desnecessária. O usuário quer uma resposta simples: **"meu nome está disponível em .com?"** — e alternativas se não estiver.

## 2. Visão do Produto

Uma ferramenta de busca de domínios **minimalista e rápida** que mostra disponibilidade nos TLDs que realmente importam, sugere variações inteligentes do nome, e leva o usuário direto para o registro — sem ruído.

**Analogia**: Google vs Yahoo nos anos 2000 — uma caixa de busca limpa vs portal lotado.

## 3. Público-Alvo

| Persona | Descrição | Necessidade |
|---------|-----------|-------------|
| **Empreendedor solo** | Está criando um produto/startup e precisa de um domínio | Nome brandável, curto, disponível em .com |
| **Dev/maker** | Construindo side project, precisa de domínio rápido | Verificação rápida, sem fricção |
| **Profissional de marketing** | Buscando domínio para campanha ou marca | Variações criativas, sugestões inteligentes |

## 4. Escopo do MVP

### 4.1 Funcionalidades Incluídas

| # | Feature | Descrição | Prioridade |
|---|---------|-----------|:----------:|
| F1 | **Busca em tempo real** | Digitar nome → ver disponibilidade enquanto digita | P0 |
| F2 | **TLDs curados** | Checar 8-10 TLDs populares (.com, .net, .org, .io, .dev, .app, .ai, .co, .xyz) | P0 |
| F3 | **Sugestões de variações** | Gerar automaticamente: prefixos, sufixos, plurais, hífens | P0 |
| F4 | **Link para registro** | Botão "Registrar" → link afiliado (Namecheap/GoDaddy) | P0 |
| F5 | **Internacionalização (i18n)** | Interface em inglês (padrão) e pt-BR, com detecção automática do idioma do navegador | P0 |
| F6 | **Pipeline DNS → RDAP** | DNS como pré-filtro rápido (~30ms), RDAP como confirmação (~500ms) | P1 |
| F7 | **Cache de resultados** | Evitar rechecks com TTL (Redis ou SQLite) | P1 |
| F8 | **Streaming de resultados** | WebSocket para enviar resultados conforme chegam | P1 |
| F9 | **Responsivo mobile** | Interface funcional em celular | P1 |

### 4.2 Funcionalidades Excluídas do MVP

- Marketplace de domínios premium
- Comparação de preços entre registradores
- WHOIS / histórico de proprietários
- Conta de usuário / login
- Favoritos / lista de desejos
- Sugestões por IA generativa (LLM)
- Zone files (custo de $10k/ano — não viável para MVP)

## 5. Arquitetura Técnica

### 5.1 Visão Geral

```
┌─────────────────────────────────┐
│  Frontend (Next.js)             │
│  - Search bar com debounce      │
│  - Resultados em tempo real     │
│  - Links afiliados              │
│  - SSR para SEO                 │
│  - i18n (en + pt-BR)           │
└──────────────┬──────────────────┘
               │ WebSocket + REST
┌──────────────▼──────────────────┐
│  Backend API (FastAPI)          │
│  - GET /api/search?q=           │
│  - WS  /api/ws/search           │
│  - Pipeline: DNS → Cache → RDAP │
│  - Gerador de sugestões         │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  Dados                          │
│  - Redis: cache (TTL 1h)        │
│  - DNS resolver: pré-filtro     │
│  - RDAP: verificação definitiva │
└─────────────────────────────────┘
```

### 5.2 Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| Frontend | **Next.js 15 + React 19** | SSR para SEO, App Router, ecossistema maduro |
| Estilização | **Tailwind CSS** | Desenvolvimento rápido, design system consistente |
| i18n | **next-intl** | Integração nativa com App Router, suporte a SSR/SSG, rotas localizadas |
| Backend | **FastAPI (Python)** | Async nativo, WebSocket, reaproveitamento do código RDAP existente |
| Cache | **Redis** | TTL nativo, rápido, padrão da indústria |
| Deploy | **VPS (Hetzner/DigitalOcean)** | Controle total, custo baixo (~$5-10/mês) |
| DNS | **Domínio próprio** | findbranddomain.com ou similar |

### 5.3 Componentes Reaproveitados

Do código existente (`check_domains.py`):
- `check_domain()` — lógica RDAP core → vira módulo Python importável
- `get_rdap_url()` — mapeamento TLD → endpoint RDAP
- Retry com exponential backoff
- `generate_domains()` — base para motor de sugestões

## 6. Internacionalização (i18n)

### 6.1 Idiomas do MVP

| Idioma | Código | Papel |
|--------|--------|-------|
| Inglês | `en` | Padrão (fallback) |
| Português (Brasil) | `pt-BR` | Secundário |

### 6.2 Estratégia

- **Detecção automática**: usar `Accept-Language` do navegador para selecionar idioma inicial
- **Seletor manual**: toggle en/pt-BR no header (flag ou sigla)
- **Rotas localizadas**: `/en/search?q=...` e `/pt-br/search?q=...`
- **SEO**: `hreflang` tags para cada idioma, sitemap multilíngue
- **Conteúdo traduzido**: UI labels, mensagens de status, tagline, textos de ajuda
- **Conteúdo NÃO traduzido**: nomes de domínio, TLDs, nomes de registradores (são universais)

### 6.3 Estrutura de Arquivos

```
messages/
├── en.json        # Traduções inglês
└── pt-BR.json     # Traduções português
```

### 6.4 Strings Principais

| Chave | en | pt-BR |
|-------|-----|-------|
| `hero.title` | Find the perfect domain for your brand | Encontre o domínio perfeito para sua marca |
| `search.placeholder` | Type a name... | Digite um nome... |
| `result.available` | Available | Disponível |
| `result.taken` | Taken | Registrado |
| `result.checking` | Checking... | Verificando... |
| `action.register` | Register | Registrar |
| `suggestions.title` | Suggestions | Sugestões |

## 7. User Stories

### Fluxo Principal — Busca de Domínio

```
US-01: Como usuário, quero digitar um nome e ver instantaneamente
       se está disponível em .com e outros TLDs populares.

US-02: Como usuário, quero ver sugestões de variações do nome
       (com prefixo, sufixo, plural, hífen) caso minha primeira
       escolha não esteja disponível.

US-03: Como usuário, quero clicar em "Registrar" e ser levado
       diretamente para comprar o domínio no registrador.

US-04: Como usuário brasileiro, quero usar a interface em português
       sem precisar configurar nada manualmente.

US-05: Como usuário, quero trocar o idioma da interface entre
       inglês e português a qualquer momento.
```

### Fluxo Detalhado

```
1. Usuário acessa findbranddomain.com
2. Idioma detectado automaticamente via Accept-Language do navegador
3. Vê uma interface limpa: logo + campo de busca + tagline (no idioma detectado)
4. Digita "coolproject"
5. Enquanto digita (debounce 300ms):
   a. Frontend abre WebSocket com o backend
   b. Backend checa DNS para coolproject.com (30ms)
   c. Se DNS responde → marcado como "registrado" (instantâneo)
   d. Se DNS não responde → checa RDAP para confirmar (500ms)
   e. Resultados chegam via WebSocket conforme ficam prontos
6. Tela mostra grid com TLDs:
   - coolproject.com → Registrado ✗
   - coolproject.net → Disponível ✓ [Registrar]
   - coolproject.io  → Disponível ✓ [Registrar]
   - ...
7. Abaixo, seção "Sugestões":
   - getcoolproject.com → Disponível ✓
   - coolprojects.com   → Disponível ✓
   - coolproject.dev     → Disponível ✓
8. Usuário clica "Registrar" → abre Namecheap com link afiliado
```

## 8. Design / UX

### 8.1 Princípios

1. **Minimalismo** — Menos é mais. Cada elemento na tela deve ter um propósito
2. **Velocidade percebida** — Mostrar resultados progressivamente, nunca uma tela em branco
3. **Uma ação clara** — O botão "Registrar" é a única call-to-action por domínio
4. **Mobile-first** — A maioria das buscas exploratórias acontece no celular

### 8.2 Páginas do MVP

| Página | Rota | Descrição |
|--------|------|-----------|
| **Home / Busca** | `/[locale]` | Campo de busca centralizado, resultados inline |
| **Resultado** | `/[locale]/search?q=nome` | Resultados detalhados (SEO-friendly, compartilhável) |

### 8.3 Wireframe Conceitual — Home

```
┌─────────────────────────────────────┐
│  FindBrandDomain          [EN│PTBR] │
│                                     │
│     Find the perfect domain         │
│     for your brand                  │
│                                     │
│  ┌───────────────────────────┐      │
│  │  Type a name...           │      │
│  └───────────────────────────┘      │
│                                     │
│  ── Results ─────────────────────   │
│                                     │
│  coolproject.com    Taken       ✗   │
│  coolproject.net    Available   ✓   │
│  coolproject.io     Available   ✓   │
│  coolproject.dev    Checking... ◌   │
│  coolproject.app    Available   ✓   │
│                                     │
│  ── Suggestions ─────────────────   │
│                                     │
│  getcoolproject.com  Available  ✓   │
│  coolprojects.com    Available  ✓   │
│  mycoolproject.com   Available  ✓   │
│                                     │
└─────────────────────────────────────┘
```

## 9. API — Endpoints

### 9.1 REST

```
GET /api/search?q=coolproject
```

**Response** (JSON):
```json
{
  "query": "coolproject",
  "results": [
    {"domain": "coolproject.com", "available": false, "tld": "com", "time_ms": 28},
    {"domain": "coolproject.net", "available": true, "tld": "net", "time_ms": 520},
    {"domain": "coolproject.io", "available": true, "tld": "io", "time_ms": 980}
  ],
  "suggestions": [
    {"domain": "getcoolproject.com", "available": true},
    {"domain": "coolprojects.com", "available": true}
  ]
}
```

### 9.2 WebSocket

```
WS /api/ws/search
```

**Client envia**: `{"query": "coolproject"}`

**Server envia** (streaming, um por vez):
```json
{"type": "result", "domain": "coolproject.com", "available": false, "time_ms": 28}
{"type": "result", "domain": "coolproject.net", "available": true, "time_ms": 520}
{"type": "suggestion", "domain": "getcoolproject.com", "available": true}
{"type": "done", "total": 15, "available": 8}
```

## 10. Pipeline de Verificação

```
Input: "coolproject"
    │
    ▼
┌─────────────────────┐
│ 1. Normalizar        │  Remove caracteres inválidos, lowercase
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. Gerar domínios    │  coolproject.com, .net, .io, .dev, .app, .ai, .co, .xyz
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. Checar cache      │  Redis GET → se existe e TTL válido, retorna
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 4. DNS pré-filtro    │  socket.getaddrinfo() → ~30ms
│    - Tem DNS?        │  → Registrado (certeza alta)
│    - Sem DNS?        │  → Pode estar disponível (confirmar)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 5. RDAP confirmação  │  Só para domínios sem DNS (~10% do total)
│    - HTTP 404?       │  → Disponível ✓
│    - HTTP 200?       │  → Registrado ✗
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 6. Cache resultado   │  Redis SET com TTL de 1 hora
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 7. Gerar sugestões   │  Variações: get*, my*, *app, *hub, plural, hífen
└─────────────────────┘
```

## 11. Motor de Sugestões

### 11.1 Estratégias de Geração

| Estratégia | Exemplo (input: "coolproject") | Prioridade |
|------------|-------------------------------|:----------:|
| Prefixos comuns | get-, my-, try-, use-, go- | Alta |
| Sufixos comuns | -app, -hub, -hq, -io, -dev | Alta |
| Plural | coolprojects | Alta |
| Sem vogais | clprjct (se curto) | Baixa |
| Abreviação | coolproj | Média |
| Composição | coolprojectai, aicoolproject | Média |

### 11.2 Ranking de Sugestões

Ordenar por score combinado:
1. **Disponibilidade** — Só mostrar disponíveis
2. **Comprimento** — Mais curtos primeiro (brandabilidade)
3. **TLD** — .com > .io > .dev > .app > outros
4. **Sem hífen** > com hífen

## 12. Monetização

### 12.1 MVP — Links Afiliados

| Registrador | Comissão estimada | Programa |
|-------------|:-----------------:|----------|
| Namecheap | $3-5 / domínio | Namecheap Affiliate |
| GoDaddy | $3-5 / domínio | GoDaddy Affiliate |
| Cloudflare | — | Sem programa de afiliados |

**Receita estimada**: Se 1.000 buscas/dia → ~2% conversão → ~20 registros/dia → ~$60-100/dia → **$1.800-3.000/mês**

### 12.2 Futuro (pós-MVP)

- Plano Pro com mais sugestões e TLDs
- API para desenvolvedores (SaaS B2B)
- Bulk check (pago)
- Monitoramento de domínios (alertas de expiração)

## 13. Métricas de Sucesso

### 13.1 Métricas Técnicas

| Métrica | Meta MVP | Meta 6 meses |
|---------|:--------:|:------------:|
| Tempo de resposta (primeiro resultado) | < 500ms | < 100ms |
| Tempo de resposta (todos os TLDs) | < 3s | < 1s |
| Uptime | 95% | 99% |
| Domínios verificados/minuto | 500 | 2.000 |

### 13.2 Métricas de Produto

| Métrica | Meta MVP | Meta 6 meses |
|---------|:--------:|:------------:|
| Buscas/dia | 100 | 5.000 |
| Taxa de clique no "Registrar" | 5% | 10% |
| Conversão (clique → registro) | 2% | 5% |
| Receita mensal | $0 (validação) | $1.000+ |
| Bounce rate | < 60% | < 40% |

## 14. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|:-------:|:-------------:|-----------|
| Rate limiting dos servidores RDAP | Alto | Média | Cache agressivo, DNS pré-filtro, retry com backoff |
| Falsos positivos (.co, .ai) | Médio | Alta | Disclaimer na UI, marcar TLDs com confiabilidade |
| Velocidade insuficiente sem zone files | Médio | Alta | DNS pré-filtro resolve 90%; streaming mascara latência |
| Baixa conversão de afiliados | Alto | Média | Testar múltiplos registradores, otimizar CTA |
| Concorrência (instantdomainsearch) | Baixo | Alta | Diferencial em UX limpa e nicho (devs/makers BR) |

## 15. Cronograma MVP

| Fase | Duração | Entregas |
|------|:-------:|---------|
| **Fase 1 — Backend API** | 1 semana | FastAPI com endpoints REST e WebSocket, pipeline DNS→Cache→RDAP, motor de sugestões básico |
| **Fase 2 — Frontend + i18n** | 1 semana | Next.js com busca em tempo real, grid de resultados, links afiliados, responsive, next-intl com en + pt-BR |
| **Fase 3 — Integração e Polish** | 3-5 dias | Conectar frontend↔backend, cache Redis, testes E2E, loading states, error handling |
| **Fase 4 — Deploy e Launch** | 2-3 dias | VPS setup, domínio, SSL, CI básico, soft launch |

**Total estimado**: 3-4 semanas

## 16. Decisões em Aberto

| # | Decisão | Opções | Status |
|---|---------|--------|:------:|
| D1 | Domínio do produto | findbranddomain.com, branddomainfinder.com, outro | Pendente |
| D2 | Registrador principal para afiliados | Namecheap, GoDaddy, ambos | Pendente |
| D3 | Hospedagem | Hetzner, DigitalOcean, Fly.io, Vercel + VPS | Pendente |
| D4 | Redis vs SQLite para cache | Redis (padrão), SQLite (zero-infra) | Pendente |
| D5 | Quantidade de sugestões no MVP | 5, 10, 20 | Pendente |
| D6 | TLDs do MVP | 8-10 curados, quais exatamente? | Pendente |
| D7 | Lib de i18n | next-intl (recomendado), next-i18next, built-in | Pendente |

---

*Documento baseado na pesquisa de viabilidade (docs/projeto/pesquisa1.md) e no código existente do projeto.*
