# Domain Checker — Manual do Desenvolvedor

## Visão Geral da Arquitetura

```
check_domains.py    ← CLI principal: verificação via RDAP
gen_domains.py      ← Gerador de candidatos em massa
termos-ai.txt       ← Lista de termos reutilizável
candidates.txt      ← Cache da última geração em massa
CLAUDE.md           ← Instruções para o agente AI
docs/
  user-manual.md    ← Manual do usuário
  dev-manual.md     ← Este arquivo
```

## Protocolo RDAP

A ferramenta usa o [RDAP (Registration Data Access Protocol)](https://about.rdap.org/) para verificar disponibilidade de domínios. RDAP é o substituto oficial do WHOIS, padronizado pela IETF.

### Como funciona

1. Faz uma requisição HTTP GET ao servidor RDAP do TLD
2. Interpreta o status code:
   - **200 OK** → domínio registrado (resposta inclui dados do registro em JSON)
   - **404 Not Found** → domínio não existe no registro (disponível)
   - **429 Too Many Requests** → rate limit, faz retry com backoff
3. Retorna resultado estruturado: `{domain, available, status, time_ms}`

### Endpoints RDAP

| TLD | Servidor | Operadora |
|-----|----------|-----------|
| `.com` | `rdap.verisign.com/com/v1/domain/{}` | Verisign (direto, rápido) |
| `.net` | `rdap.verisign.com/net/v1/domain/{}` | Verisign (direto, rápido) |
| `.org` | `rdap.org/domain/{}` | Via bootstrap RDAP.org |
| Outros | `rdap.org/domain/{}` | Bootstrap RDAP.org (redireciona) |

O `rdap.org` atua como bootstrap server — recebe a query e redireciona para o servidor RDAP autoritativo do TLD. Para `.com` e `.net`, acessamos a Verisign diretamente para menor latência (~500ms vs ~1000ms).

## check_domains.py — Estrutura do Código

### Dependências

Zero dependências externas. Usa apenas a stdlib do Python 3.8+:

- `argparse` — parsing de argumentos CLI
- `concurrent.futures` — ThreadPoolExecutor para concorrência
- `json` — saída JSON
- `urllib.request` / `urllib.error` — requisições HTTP
- `time` — medição de latência e delays de retry
- `sys` — stderr para progresso, stdout para resultados

### Funções Principais

#### `get_rdap_url(domain: str) -> str`

Resolve o endpoint RDAP correto para o TLD do domínio.

```python
get_rdap_url("exemplo.com")   # → "https://rdap.verisign.com/com/v1/domain/exemplo.com"
get_rdap_url("exemplo.org")   # → "https://rdap.org/domain/exemplo.org"
```

#### `check_domain(domain: str, timeout: int) -> dict`

Verifica um único domínio via RDAP. Retorna:

```python
{
    "domain": "exemplo.com",
    "available": True,       # bool
    "status": "available",   # "available" | "registered" | "error:*"
    "time_ms": 523           # latência em ms
}
```

Implementa retry com backoff exponencial para erros 429 e erros de rede:
- `MAX_RETRIES = 2`
- `RETRY_DELAY = 1.5` (multiplicado pelo número do retry)

#### `generate_domains(pattern: str, terms: list, variants: bool) -> list`

Gera lista de domínios a partir de padrão + termos.

O `*` no padrão é substituído por cada termo. Com `variants=True`, para cada termo gera 4 combinações:

```
Padrão: ai*.com    Termo: hub
→ aihub.com        (prefixo direto)
→ ai-hub.com       (prefixo com hífen)
→ hubai.com        (sufixo direto)
→ hub-ai.com       (sufixo com hífen)
```

Deduplicação automática preservando ordem de inserção.

### Fluxo de Execução

```
1. Parse dos argumentos (argparse)
2. Construção da lista de domínios:
   a. --pattern + --terms/--terms-file → generate_domains()
   b. --domains → lista direta
   c. --domains-file → leitura de arquivo
3. Deduplicação preservando ordem
4. Verificação concorrente:
   - ThreadPoolExecutor(max_workers=N)
   - Submete todas as tasks
   - as_completed() para progresso em tempo real
5. Classificação: available / registered / errors
6. Ordenação dos disponíveis (length/alpha/time)
7. Saída: texto formatado ou JSON
```

### Concorrência

Usa `concurrent.futures.ThreadPoolExecutor` (não `asyncio`) por três motivos:
1. Sem dependências externas (não precisa de `aiohttp`)
2. `urllib.request` é thread-safe para requisições independentes
3. API simples com `as_completed()` para progresso em tempo real

Cada thread faz uma requisição HTTP bloqueante. Com 15 workers e ~500ms por requisição, processa ~30 domínios/segundo (~1800/minuto).

### Constantes Configuráveis

```python
DEFAULT_WORKERS = 15      # Conexões simultâneas
DEFAULT_TIMEOUT = 8       # Timeout por requisição (segundos)
DEFAULT_TOP = 10          # Quantidade de resultados na saída
MAX_RETRIES = 2           # Retries em caso de 429 ou erro de rede
RETRY_DELAY = 1.5         # Delay base entre retries (multiplicado pelo nº do retry)
```

## gen_domains.py — Gerador em Massa

Script auxiliar para gerar milhares de candidatos combinando:

### Configuração

```python
PREFIXES = ["ai", "ais", "aix", "aie", "aio"]  # Prefixos antes do termo
TERMS = [...]                                     # ~200 termos base
```

### Combinações Geradas

Para cada prefixo × cada termo, gera:

| Formato | Exemplo |
|---------|---------|
| `{prefix}{term}.com` | `aiguide.com` |
| `{prefix}{term}s.com` | `aiguides.com` (plural) |
| `{prefix}-{term}.com` | `ai-guide.com` (hífen) |

Para cada sufixo (`ai`, `ais`) × cada termo:

| Formato | Exemplo |
|---------|---------|
| `{term}{suffix}.com` | `guideai.com` |
| `{term}-{suffix}.com` | `guide-ai.com` |
| `{term}s{suffix}.com` | `guidesai.com` (plural) |
| `{term}s-{suffix}.com` | `guides-ai.com` (plural + hífen) |

Total: ~5.600 candidatos únicos com a configuração padrão.

### Uso

```bash
# Gerar para stdout
python3 gen_domains.py > candidatos.txt

# Gerar e verificar diretamente (pipe)
python3 gen_domains.py | head -100 > amostra.txt
python3 check_domains.py -df amostra.txt -n 50 -w 20
```

## Como Estender

### Adicionar novos TLDs

Em `check_domains.py`, adicionar ao dicionário `RDAP_ENDPOINTS`:

```python
RDAP_ENDPOINTS = {
    "com": "https://rdap.verisign.com/com/v1/domain/{}",
    "net": "https://rdap.verisign.com/net/v1/domain/{}",
    "org": "https://rdap.org/domain/{}",
    "io": "https://rdap.org/domain/{}",       # novo
    "dev": "https://rdap.org/domain/{}",      # novo
}
```

O `rdap.org` funciona como fallback para qualquer TLD, mas é mais lento. Se o TLD tiver um servidor RDAP direto, use-o para melhor performance.

### Adicionar novos termos ao gerador

Em `gen_domains.py`, adicionar termos à lista `TERMS`:

```python
TERMS = [
    # ... termos existentes ...
    "newtermo1", "newtermo2",
]
```

### Adicionar novos prefixos ao gerador

Em `gen_domains.py`, adicionar à lista `PREFIXES`:

```python
PREFIXES = ["ai", "ais", "aix", "aie", "aio", "air"]  # air adicionado
```

### Usar como biblioteca Python

Os módulos podem ser importados diretamente:

```python
from check_domains import check_domain, generate_domains

# Verificar um único domínio
result = check_domain("exemplo.com")
print(result)
# {'domain': 'exemplo.com', 'available': False, 'status': 'registered', 'time_ms': 523}

# Gerar lista de domínios
domains = generate_domains("ai*.com", ["hub", "flow", "kit"])
# ['aihub.com', 'aiflow.com', 'aikit.com']

# Verificação em batch
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(check_domain, d): d for d in domains}
    for future in as_completed(futures):
        result = future.result()
        if result["available"]:
            print(f"Disponível: {result['domain']}")
```

## Limitações Conhecidas

| Limitação | Detalhe |
|-----------|---------|
| Apenas RDAP | Não usa WHOIS legado — alguns TLDs podem não ter servidor RDAP |
| Rate limiting | Verisign tolera ~20 req/s; mais que isso pode retornar 429 |
| Falsos positivos | RDAP 404 indica "não no registro" — domínios em período de redenção podem retornar 404 |
| Sem cache | Cada execução faz novas requisições; não há cache local entre execuções |
| Sem DNS check | Não usa DNS como pré-filtro rápido (poderia acelerar buscas grandes) |
| Thread-based | `ThreadPoolExecutor` tem overhead por thread; para >10.000 domínios, `asyncio` + `aiohttp` seria mais eficiente |

## Possíveis Melhorias Futuras

- Cache local com TTL (SQLite ou arquivo JSON) para evitar rechecks
- Pré-filtro via DNS (socket/DoH) para eliminar domínios com registros antes do RDAP
- Migrar para `asyncio` + `aiohttp` para melhor performance em buscas massivas
- Score de brandabilidade (comprimento, pronúncia, memorabilidade)
- Integração com APIs de registradores para preço e disponibilidade exata
- Export para CSV/Excel
