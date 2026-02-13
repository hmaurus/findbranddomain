# Domain Checker — Manual do Usuário

Ferramenta de linha de comando para verificar se domínios .com estão disponíveis para registro.

## Requisitos

- Python 3.8+
- Conexão com a internet
- Nenhuma dependência externa (usa apenas a biblioteca padrão do Python)

## Início Rápido

### Verificar domínios específicos

```bash
python3 check_domains.py -d meudominio.com outrodominio.com
```

### Verificar um padrão com termos

```bash
python3 check_domains.py -p "ai*.com" -t hub flow kit lab
```

O `*` é substituído por cada termo. Neste exemplo, verifica: `aihub.com`, `aiflow.com`, `aikit.com`, `ailab.com`.

### Verificar um padrão com arquivo de termos

```bash
python3 check_domains.py -p "ai*.com" -tf meus-termos.txt
```

O arquivo deve ter um termo por linha:

```
hub
flow
kit
lab
```

## Opções

| Flag | Abreviação | Descrição | Default |
|------|------------|-----------|---------|
| `--pattern` | `-p` | Padrão com `*` como placeholder | — |
| `--terms` | `-t` | Termos inline para substituir o `*` | — |
| `--terms-file` | `-tf` | Arquivo com termos (um por linha) | — |
| `--domains` | `-d` | Lista de domínios específicos | — |
| `--domains-file` | `-df` | Arquivo com domínios (um por linha) | — |
| `--top` | `-n` | Quantidade de resultados a mostrar | 10 |
| `--workers` | `-w` | Conexões simultâneas | 15 |
| `--variants` | — | Gerar variantes com hífen e invertidas | off |
| `--all` | — | Mostrar todos os resultados (inclusive registrados) | off |
| `--json` | — | Saída em formato JSON | off |
| `--sort` | — | Ordenação: `length`, `alpha` ou `time` | `length` |
| `--timeout` | — | Timeout por domínio (segundos) | 8 |

## Exemplos de Uso

### Busca simples

```bash
python3 check_domains.py -p "ai*.com" -t hub flow kit lab
```

Saída:
```
  Verificando 4 domínios (15 workers)...
  ██████████████████████████████ 4/4 (100%) | ✓ 0 disponíveis

  ✗ Nenhum domínio disponível encontrado.

  Resumo: 0 disponíveis, 4 registrados, 0 erros (de 4 total)
```

### Busca com variantes

Com `--variants`, cada termo gera 4 combinações. Para o padrão `ai*.com` com o termo `hub`:

- `aihub.com` (prefixo direto)
- `ai-hub.com` (prefixo com hífen)
- `hubai.com` (sufixo direto)
- `hub-ai.com` (sufixo com hífen)

```bash
python3 check_domains.py -p "ai*.com" -t hub flow --variants
```

### Busca com muitos termos

```bash
python3 check_domains.py -p "ai*.com" -tf termos-ai.txt -n 20
```

### Ver todos os resultados

```bash
python3 check_domains.py -p "ai*.com" -t hub flow kit --all
```

### Saída em JSON

```bash
python3 check_domains.py -p "ai*.com" -t hub flow --json 2>/dev/null
```

A barra de progresso vai para stderr, o JSON vai para stdout. O `2>/dev/null` suprime o progresso.

Formato da saída JSON:

```json
{
  "total": 4,
  "available_count": 1,
  "registered_count": 3,
  "error_count": 0,
  "available": [
    {
      "domain": "aiexemplo.com",
      "available": true,
      "status": "available",
      "time_ms": 523
    }
  ]
}
```

### Verificar domínios de um arquivo

```bash
python3 check_domains.py -df minha-lista.txt -n 50
```

O arquivo deve ter um domínio por linha:

```
exemplo.com
meusite.com
outrodominio.com
```

### Padrões flexíveis

O `*` pode estar em qualquer posição:

```bash
# Prefixo: ai + termo
python3 check_domains.py -p "ai*.com" -t hub flow

# Sufixo: termo + ai
python3 check_domains.py -p "*ai.com" -t hub flow

# Infixo: ai + termo + guide
python3 check_domains.py -p "ai*guide.com" -t code dev top

# Outro TLD
python3 check_domains.py -p "ai*.net" -t hub flow
```

## Gerador de Candidatos em Massa

O `gen_domains.py` gera milhares de combinações com múltiplos prefixos e variações:

```bash
# Gerar lista
python3 gen_domains.py > candidatos.txt

# Verificar todos
python3 check_domains.py -df candidatos.txt -n 100 -w 20
```

O gerador combina:
- Prefixos: `ai`, `ais`, `aix`, `aie`, `aio`
- ~200 termos base
- Plural de cada termo
- Variantes com hífen
- Sufixos `ai` e `ais`

## Ordenação dos Resultados

| Opção | Comportamento |
|-------|---------------|
| `--sort length` | Domínios mais curtos primeiro (padrão) |
| `--sort alpha` | Ordem alfabética |
| `--sort time` | Mais rápidos primeiro (menor latência RDAP) |

## Dicas

- **Domínios mais curtos** (5-8 chars no nome) são mais valiosos e memoráveis
- **Sem hífen** é geralmente melhor para branding do que com hífen
- **Plural importa**: `guide` e `guides` são domínios diferentes — sempre teste ambos
- **Ajuste workers** (`-w`): mais workers = mais rápido, mas pode causar rate limiting. 15-20 é o ideal
- **Use `--json`** para pós-processamento com scripts ou piping para outras ferramentas
- **TLDs suportados**: `.com` e `.net` usam o servidor rápido da Verisign; outros TLDs usam `rdap.org` (mais lento)

## Solução de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| Muitos erros de timeout | Workers demais ou conexão lenta | Reduzir `-w 10` ou aumentar `--timeout 15` |
| HTTP 429 (rate limit) | Muitas requisições simultâneas | O script já faz retry automático; reduza `-w` se persistir |
| Erro de rede | Sem internet ou DNS | Verificar conexão; testar `curl https://rdap.verisign.com/com/v1/domain/google.com` |
| Resultado "available" mas domínio não está | RDAP pode ter delay na propagação | Confirmar no registrador oficial (ex: Namecheap, GoDaddy) antes de comprar |
