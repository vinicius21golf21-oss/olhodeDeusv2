import os
import sys
import re
import json
import hashlib
import uuid
import threading
from pathlib import Path

import requests

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────
BOT_DB_URL = "https://msbot.squareweb.app/api/olhodeus/db"

DB_NOMES = {
    1: "DB Gov",
    2: "DB Gov / Sites em Geral",
    3: "DB Gov V2",
}

# ─────────────────────────────────────────────────────────────────────────────
#  CORES ANSI
# ─────────────────────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
ROXO    = "\033[95m"
AZUL    = "\033[94m"
VERDE   = "\033[92m"
AMARELO = "\033[93m"
VERMELHO= "\033[91m"
CINZA   = "\033[90m"
BRANCO  = "\033[97m"

def limpar():
    os.system("clear" if os.name != "nt" else "cls")

def linha(char="─", n=50):
    print(ROXO + char * n + RESET)

# ─────────────────────────────────────────────────────────────────────────────
#  HWID (só para cabeçalho da requisição, não bloqueia nada)
# ─────────────────────────────────────────────────────────────────────────────

def _hwid() -> str:
    cache = Path.home() / ".olhodeus" / "device_id.txt"
    try:
        if cache.exists():
            return cache.read_text().strip()
        new_id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16].upper()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(new_id)
        return new_id
    except Exception:
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16].upper()

HWID = _hwid()

# ─────────────────────────────────────────────────────────────────────────────
#  API — baixar DB
# ─────────────────────────────────────────────────────────────────────────────

def baixar_db(num: int) -> list | None:
    """Baixa a base de dados do servidor e retorna lista de linhas."""
    try:
        r = requests.get(
            f"{BOT_DB_URL}/{num}",
            headers={"X-HWID": HWID, "User-Agent": "OlhoDeusCLI/2.0"},
            timeout=60,
            stream=True,
        )
        if r.status_code in (403, 404):
            return None
        r.raise_for_status()
        linhas = [l.strip() for l in r.text.split("\n") if l.strip()]
        return linhas
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        print(f"{VERMELHO}Erro inesperado: {e}{RESET}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
#  BUSCA INTELIGENTE
# ─────────────────────────────────────────────────────────────────────────────

def _extrair_campos(linha: str):
    linha = linha.strip()
    if not linha:
        return None
    for sep in [":", "|", ";"]:
        partes = linha.split(sep)
        if len(partes) >= 3:
            for i, p in enumerate(partes):
                p_low = p.lower()
                if (p_low.startswith("http://") or p_low.startswith("https://")
                        or ("." in p and "/" in p and len(p) > 6)):
                    restantes = partes[:i] + partes[i+1:]
                    login = restantes[0] if restantes else ""
                    senha = sep.join(restantes[1:]) if len(restantes) > 1 else ""
                    return (p.strip(), login.strip(), senha.strip())
            url   = sep.join(partes[:-2]).strip() if len(partes) > 3 else partes[0].strip()
            login = partes[-2].strip()
            senha = partes[-1].strip()
            return (url, login, senha)
        elif len(partes) == 2:
            return (linha, partes[0].strip(), partes[1].strip())
    return (linha, "", "")

def _url_match(url_linha: str, url_busca: str) -> bool:
    def sem_proto(u):
        return re.sub(r"^https?://", "", u.lower().strip().rstrip("/"))
    base_l = sem_proto(url_linha)
    base_b = sem_proto(url_busca)
    return (base_b in base_l or base_l in base_b
            or base_l.startswith(base_b) or base_b.startswith(base_l))

def buscar(linhas: list, url_busca: str) -> list:
    resultados = []
    for linha in linhas:
        campos = _extrair_campos(linha)
        if campos is None:
            continue
        url_linha, login, senha = campos
        if _url_match(url_linha, url_busca):
            resultados.append({"url": url_linha, "login": login, "senha": senha, "raw": linha})
    return resultados

# ─────────────────────────────────────────────────────────────────────────────
#  EXIBIÇÃO
# ─────────────────────────────────────────────────────────────────────────────

def cabecalho():
    limpar()
    linha("═")
    print(f"{ROXO}{BOLD}        ◉  OLHO DE DEUS V2  ◉{RESET}")
    print(f"{CINZA}   SISTEMA DE BUSCA EM BASE DE DADOS{RESET}")
    print(f"{CINZA}   discord.com/invite/ksRpjyrKU6{RESET}")
    linha("═")

def menu_principal():
    cabecalho()
    print(f"\n{BRANCO}{BOLD}  Escolha a Base de Dados:{RESET}\n")
    for num, nome in DB_NOMES.items():
        print(f"  {ROXO}[{num}]{RESET}  {BRANCO}{nome}{RESET}")
    print(f"\n  {CINZA}[0]  Sair{RESET}")
    linha()

def exibir_resultados(resultados: list, url_busca: str):
    if not resultados:
        print(f"\n{VERMELHO}✘  Nenhum resultado para '{url_busca}'{RESET}")
        print(f"{CINZA}   Tente um domínio mais genérico (ex: gov.br){RESET}\n")
        return

    print(f"\n{VERDE}{BOLD}✔  {len(resultados):,} resultado(s) para '{url_busca}'{RESET}\n")
    linha()

    for i, r in enumerate(resultados, 1):
        print(f"{AZUL}[{i}]{RESET}")
        print(f"  {ROXO}🔗 URL  :{RESET}  {r['url']}")
        print(f"  {BRANCO}👤 Login:{RESET}  {r['login']}")
        print(f"  {AMARELO}🔑 Senha:{RESET}  {r['senha']}")
        linha("─", 50)

    print(f"{CINZA}Total: {len(resultados):,} registro(s) encontrado(s){RESET}\n")

# ─────────────────────────────────────────────────────────────────────────────
#  ANIMAÇÃO DE LOADING (terminal)
# ─────────────────────────────────────────────────────────────────────────────

_parar_loading = threading.Event()

def _animar_loading(msg: str):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not _parar_loading.is_set():
        sys.stdout.write(f"\r{ROXO}{frames[i % len(frames)]}{RESET}  {CINZA}{msg}{RESET}   ")
        sys.stdout.flush()
        _parar_loading.wait(0.1)
        i += 1
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

def iniciar_loading(msg: str) -> threading.Thread:
    _parar_loading.clear()
    t = threading.Thread(target=_animar_loading, args=(msg,), daemon=True)
    t.start()
    return t

def parar_loading(t: threading.Thread):
    _parar_loading.set()
    t.join()

# ─────────────────────────────────────────────────────────────────────────────
#  FLUXO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def tela_busca(num_db: int):
    nome_db = DB_NOMES[num_db]
    cabecalho()
    print(f"\n{ROXO}{BOLD}  {nome_db}{RESET}")
    print(f"{CINZA}  Baixando base de dados...{RESET}\n")

    # Download da DB
    t = iniciar_loading(f"Baixando {nome_db}")
    linhas = baixar_db(num_db)
    parar_loading(t)

    if linhas is None:
        print(f"{VERMELHO}✘  Erro ao baixar a base de dados.{RESET}")
        print(f"{CINZA}   Verifique sua conexão com a internet.{RESET}\n")
        input(f"{CINZA}Pressione ENTER para voltar...{RESET}")
        return

    print(f"{VERDE}✔  {len(linhas):,} registros carregados — {nome_db}{RESET}\n")
    linha()

    # Loop de buscas nessa DB
    while True:
        try:
            print(f"\n{BRANCO}Digite a URL para buscar {CINZA}(ou ENTER para voltar){RESET}:")
            url_busca = input(f"  {ROXO}>{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not url_busca:
            break

        t = iniciar_loading(f"Buscando '{url_busca}'")
        resultados = buscar(linhas, url_busca)
        parar_loading(t)

        exibir_resultados(resultados, url_busca)

        # Opção de salvar
        if resultados:
            try:
                salvar = input(f"{CINZA}Salvar resultados em arquivo? [s/N]: {RESET}").strip().lower()
            except (KeyboardInterrupt, EOFError):
                salvar = "n"

            if salvar == "s":
                nome_arq = f"resultados_{url_busca.replace('/', '_').replace(':', '')}_{num_db}.txt"
                try:
                    with open(nome_arq, "w", encoding="utf-8") as f:
                        f.write(f"Olho de Deus V2 — Resultados\n")
                        f.write(f"URL buscada: {url_busca}\n")
                        f.write(f"Base: {nome_db}\n")
                        f.write(f"Total: {len(resultados)}\n")
                        f.write("=" * 60 + "\n\n")
                        for r in resultados:
                            f.write(f"URL  : {r['url']}\n")
                            f.write(f"Login: {r['login']}\n")
                            f.write(f"Senha: {r['senha']}\n")
                            f.write("-" * 40 + "\n")
                    print(f"{VERDE}✔  Salvo em: {nome_arq}{RESET}\n")
                except Exception as e:
                    print(f"{VERMELHO}Erro ao salvar: {e}{RESET}\n")

def main():
    while True:
        menu_principal()
        try:
            escolha = input(f"\n{ROXO}Escolha [{'/'.join(str(k) for k in DB_NOMES.keys())}/0]: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{CINZA}Saindo...{RESET}")
            sys.exit(0)

        if escolha == "0" or escolha == "":
            print(f"\n{CINZA}Saindo...{RESET}")
            sys.exit(0)

        if escolha.isdigit() and int(escolha) in DB_NOMES:
            tela_busca(int(escolha))
        else:
            print(f"{VERMELHO}Opção inválida.{RESET}")
            import time
            time.sleep(1)

if __name__ == "__main__":
    main()
