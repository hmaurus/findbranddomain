#!/usr/bin/env python3
"""
Domain Availability Checker — Verifica disponibilidade de domínios via RDAP.

Usa o protocolo RDAP (Verisign para .com/.net, rdap.org para outros TLDs)
para verificar rapidamente se domínios estão disponíveis para registro.

Uso:
  python3 check_domains.py -p "ai*.com" -t hub flow kit lab
  python3 check_domains.py -p "ai*.com" -tf termos.txt --variants
  python3 check_domains.py -d exemplo.com outro.com
  python3 check_domains.py -df dominios.txt --json
"""

import argparse
import concurrent.futures
import json
import sys
import time
import urllib.request
import urllib.error

# ── RDAP Endpoints ──────────────────────────────────────────────────────────

RDAP_ENDPOINTS = {
    "com": "https://rdap.verisign.com/com/v1/domain/{}",
    "net": "https://rdap.verisign.com/net/v1/domain/{}",
    "org": "https://rdap.org/domain/{}",
}
RDAP_DEFAULT = "https://rdap.org/domain/{}"

# ── Defaults ────────────────────────────────────────────────────────────────

DEFAULT_WORKERS = 15
DEFAULT_TIMEOUT = 8
DEFAULT_TOP = 10
MAX_RETRIES = 2
RETRY_DELAY = 1.5


# ── Core ────────────────────────────────────────────────────────────────────


def get_rdap_url(domain):
    tld = domain.rsplit(".", 1)[-1].lower() if "." in domain else "com"
    template = RDAP_ENDPOINTS.get(tld, RDAP_DEFAULT)
    return template.format(domain)


def check_domain(domain, timeout=DEFAULT_TIMEOUT):
    """
    Verifica disponibilidade de um domínio via RDAP.
    Retorna dict: {domain, available, status, time_ms}
    """
    url = get_rdap_url(domain)
    retries = 0

    while retries <= MAX_RETRIES:
        start = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Accept", "application/rdap+json")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                elapsed = (time.time() - start) * 1000
                return {
                    "domain": domain,
                    "available": False,
                    "status": "registered",
                    "time_ms": round(elapsed),
                }

        except urllib.error.HTTPError as e:
            elapsed = (time.time() - start) * 1000
            if e.code == 404:
                return {
                    "domain": domain,
                    "available": True,
                    "status": "available",
                    "time_ms": round(elapsed),
                }
            if e.code == 429 and retries < MAX_RETRIES:
                retries += 1
                time.sleep(RETRY_DELAY * retries)
                continue
            return {
                "domain": domain,
                "available": False,
                "status": f"error:{e.code}",
                "time_ms": round(elapsed),
            }

        except urllib.error.URLError:
            elapsed = (time.time() - start) * 1000
            if retries < MAX_RETRIES:
                retries += 1
                time.sleep(RETRY_DELAY * retries)
                continue
            return {
                "domain": domain,
                "available": False,
                "status": "error:network",
                "time_ms": round(elapsed),
            }

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return {
                "domain": domain,
                "available": False,
                "status": f"error:{type(e).__name__}",
                "time_ms": round(elapsed),
            }

    return {
        "domain": domain,
        "available": False,
        "status": "error:max_retries",
        "time_ms": 0,
    }


# ── Domain Generation ──────────────────────────────────────────────────────


def generate_domains(pattern, terms, variants=False):
    """
    Gera nomes de domínio a partir de padrão e termos.
    O * no padrão é substituído por cada termo.

    Com --variants, gera também variantes com hífen e invertidas:
      ai*.com → aihub.com, ai-hub.com, hubai.com, hub-ai.com
    """
    if "." not in pattern:
        pattern += ".com"

    patterns = [pattern]

    if variants and "*" in pattern:
        base, tld = pattern.rsplit(".", 1)
        parts = base.split("*", 1)
        prefix, suffix = parts[0], parts[1] if len(parts) > 1 else ""

        if prefix and not suffix:
            # ai* → ai*, ai-*, *ai, *-ai
            patterns = [
                f"{prefix}*.{tld}",
                f"{prefix}-*.{tld}",
                f"*{prefix}.{tld}",
                f"*-{prefix}.{tld}",
            ]
        elif suffix and not prefix:
            # *ai → *ai, *-ai, ai*, ai-*
            patterns = [
                f"*{suffix}.{tld}",
                f"*-{suffix}.{tld}",
                f"{suffix}*.{tld}",
                f"{suffix}-*.{tld}",
            ]
        else:
            patterns = [pattern]

    domains = []
    seen = set()
    for pat in patterns:
        for term in terms:
            domain = pat.replace("*", term).lower()
            if domain not in seen:
                seen.add(domain)
                domains.append(domain)

    return domains


# ── Output ──────────────────────────────────────────────────────────────────


def print_progress(done, total, available):
    pct = done / total * 100
    bar_len = 30
    filled = int(bar_len * done / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    sys.stderr.write(
        f"\r  {bar} {done}/{total} ({pct:.0f}%) | ✓ {available} disponíveis"
    )
    sys.stderr.flush()


def sort_results(results, sort_key):
    if sort_key == "length":
        results.sort(key=lambda r: (len(r["domain"]), r["domain"]))
    elif sort_key == "alpha":
        results.sort(key=lambda r: r["domain"])
    elif sort_key == "time":
        results.sort(key=lambda r: r["time_ms"])
    return results


# ── CLI ─────────────────────────────────────────────────────────────────────


def build_parser():
    parser = argparse.ArgumentParser(
        description="Verifica disponibilidade de domínios via RDAP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s -p "ai*.com" -t hub flow kit lab
  %(prog)s -p "ai*.com" -tf termos.txt -n 20
  %(prog)s -p "ai*.com" -t hub flow --variants
  %(prog)s -d exemplo.com outro.com
  %(prog)s -df dominios.txt --json
  %(prog)s -p "ai*.com" -t hub flow --sort alpha --all
        """,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "-p", "--pattern", help='Padrão com * como placeholder (ex: ai*.com, *dev.com)'
    )
    source.add_argument("-d", "--domains", nargs="+", help="Domínios específicos")
    source.add_argument(
        "-df", "--domains-file", help="Arquivo com domínios (um por linha)"
    )

    parser.add_argument("-t", "--terms", nargs="+", help="Termos para substituir o *")
    parser.add_argument(
        "-tf", "--terms-file", help="Arquivo com termos (um por linha)"
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=DEFAULT_TOP,
        help=f"Mostrar top N disponíveis (default: {DEFAULT_TOP})",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Workers concorrentes (default: {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--variants",
        action="store_true",
        help="Gerar variantes (com hífen e invertido)",
    )
    parser.add_argument(
        "--all", action="store_true", help="Mostrar todos os resultados"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Saída em JSON"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout por requisição em segundos (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--sort",
        choices=["length", "alpha", "time"],
        default="length",
        help="Ordenação dos disponíveis (default: length)",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # ── Construir lista de domínios ─────────────────────────────────────

    domains = []

    if args.pattern:
        terms = []
        if args.terms:
            terms = args.terms
        elif args.terms_file:
            with open(args.terms_file) as f:
                terms = [line.strip() for line in f if line.strip()]
        else:
            parser.error("--pattern requer --terms ou --terms-file")

        domains = generate_domains(args.pattern, terms, args.variants)

    elif args.domains:
        domains = [d.lower() if "." in d else f"{d.lower()}.com" for d in args.domains]

    elif args.domains_file:
        with open(args.domains_file) as f:
            domains = [line.strip().lower() for line in f if line.strip()]

    # Deduplica preservando ordem
    seen = set()
    unique = []
    for d in domains:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    domains = unique

    if not domains:
        print("Nenhum domínio para verificar.", file=sys.stderr)
        sys.exit(1)

    total = len(domains)
    sys.stderr.write(f"\n  Verificando {total} domínios ({args.workers} workers)...\n")

    # ── Verificar domínios concorrentemente ─────────────────────────────

    results = []
    available_count = 0
    done_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(check_domain, domain, args.timeout): domain
            for domain in domains
        }

        for future in concurrent.futures.as_completed(future_map):
            result = future.result()
            results.append(result)
            done_count += 1
            if result["available"]:
                available_count += 1
            print_progress(done_count, total, available_count)

    sys.stderr.write("\n\n")

    # ── Classificar resultados ──────────────────────────────────────────

    available = [r for r in results if r["available"]]
    registered = [r for r in results if r["status"] == "registered"]
    errors = [r for r in results if r["status"].startswith("error")]

    available = sort_results(available, args.sort)

    # ── Saída JSON ──────────────────────────────────────────────────────

    if args.json_output:
        output = {
            "total": total,
            "available_count": len(available),
            "registered_count": len(registered),
            "error_count": len(errors),
            "available": available if args.all else available[: args.top],
        }
        if args.all:
            output["registered"] = sorted(registered, key=lambda r: r["domain"])
            output["errors"] = errors
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # ── Saída texto ─────────────────────────────────────────────────────

    if available:
        top_n = available if args.all else available[: args.top]
        print(f"  ✓ DISPONÍVEIS ({len(available)} de {total}):")
        print()
        for i, r in enumerate(top_n, 1):
            name = r["domain"].split(".")[0]
            print(f"    {i:>3}. {r['domain']:<35} ({len(name)} chars, {r['time_ms']}ms)")

        if not args.all and len(available) > args.top:
            remaining = len(available) - args.top
            print(f"\n    ... e mais {remaining} disponíveis (use --all para ver todos)")
    else:
        print("  ✗ Nenhum domínio disponível encontrado.")

    if args.all and registered:
        print(f"\n  ✗ REGISTRADOS ({len(registered)}):")
        for r in sorted(registered, key=lambda r: r["domain"]):
            print(f"    - {r['domain']}")

    if errors:
        print(f"\n  ⚠ ERROS ({len(errors)}):")
        for r in errors:
            print(f"    - {r['domain']}: {r['status']}")

    print(
        f"\n  Resumo: {len(available)} disponíveis, {len(registered)} registrados, "
        f"{len(errors)} erros (de {total} total)\n"
    )


if __name__ == "__main__":
    main()
