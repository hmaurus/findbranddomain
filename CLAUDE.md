# Domain Checker — Instruções para o Agente

Este projeto contém ferramentas para verificar disponibilidade de domínios .com via protocolo RDAP.

## Arquivos do Projeto

- `check_domains.py` — Script principal de verificação via RDAP (sem dependências externas)
- `gen_domains.py` — Gerador de candidatos em massa com variações (prefixos, plurais, hífens)
- `termos-ai.txt` — Lista base de ~160 termos para combinação
- `candidates.txt` — Cache da última geração em massa (pode ser regenerado)

## Como Atender Pedidos de Consulta de Domínios

Quando o usuário pedir para consultar domínios, siga este fluxo:

### 1. Interpretar o pedido

Extrair do pedido:
- **Padrão**: onde fica o `*` (ex: `ai*.com`, `*guide.com`, `ai*guide.com`)
- **Termos**: lista de palavras para substituir o `*`
- **Filtros**: com/sem hífen, tamanho máximo, prefixo específico
- **Quantidade**: quantos resultados mostrar

### 2. Escolher a abordagem

| Cenário | Comando |
|---------|---------|
| Padrão simples + poucos termos | `python3 check_domains.py -p "PADRÃO" -t termo1 termo2 ...` |
| Padrão + muitos termos | Salvar termos em arquivo, usar `-tf arquivo.txt` |
| Padrão + variantes (hífen/invertido) | Adicionar `--variants` |
| Domínios específicos | `python3 check_domains.py -d dominio1.com dominio2.com` |
| Busca massiva com prefixos variados | Usar `gen_domains.py` para gerar candidatos, depois `check_domains.py -df candidates.txt` |

### 3. Executar

```bash
# Busca padrão (top 10, ordenado por tamanho)
python3 check_domains.py -p "ai*.com" -t hub flow kit -n 10

# Busca com muitos resultados em JSON (para pós-processamento)
python3 check_domains.py -p "ai*.com" -tf termos-ai.txt -n 200 --json 2>/dev/null

# Com variantes (gera 4x mais: prefixo, prefixo-hífen, sufixo, sufixo-hífen)
python3 check_domains.py -p "ai*.com" -tf termos-ai.txt --variants -n 50

# Domínios específicos
python3 check_domains.py -d exemplo.com teste.com outro.com
```

### 4. Pós-processar resultados

Para buscas grandes, usar `--json 2>/dev/null` e filtrar com Python inline:

```bash
python3 check_domains.py -df candidates.txt --json -n 5000 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
for r in d['available']:
    name = r['domain'].split('.')[0]
    # Aplicar filtros conforme pedido do usuário
    if len(name) <= 10 and '-' not in name:
        print(r['domain'])
"
```

### 5. Apresentar resultados

- Ordenar por tamanho do nome (mais curtos = mais valiosos)
- Agrupar por categoria quando fizer sentido
- Destacar os melhores com comentários sobre brandabilidade
- Sempre informar totais: disponíveis / registrados / erros

## Lições Aprendidas

- O prefixo `ai` está extremamente saturado — quase tudo com termos bons já foi registrado
- O prefixo `ais` (AIs = plural) tem muito mais disponibilidade
- Sempre incluir **plurais** dos termos (guide → guides) — são nichos diferentes
- Sempre testar **múltiplos prefixos** variantes, não apenas o óbvio
- Domínios com hífen têm mais disponibilidade mas são menos brandáveis
- Para .com, usar endpoint direto da Verisign (mais rápido): `rdap.verisign.com`
- Rate limit: 15-20 workers simultâneos funciona bem sem ser bloqueado

## Limites Técnicos

- RDAP só verifica .com/.net/.org de forma confiável
- ~500 domínios/minuto com 15 workers
- Retry automático em caso de HTTP 429 (rate limit) com backoff
- Timeout padrão: 8 segundos por requisição
- Sem dependências externas — usa apenas stdlib do Python
