"""Coleta o preço de cada produto, salva no CSV e avisa no Telegram.

Uso: python -m precos.main <pasta com produtos.toml e precos.csv>
"""
import csv
import os
import sys
import tomllib
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from precos import extrair
from precos.analise import veredito

CAMPOS = ["data", "url", "preco", "disponivel"]
FALHAS_PRA_AVISAR = 3


def chave(url: str) -> str:
    """Tira query string e âncora: parâmetros de rastreio não podem quebrar o histórico."""
    return url.split("#")[0].split("?")[0]


def avisar(texto: str) -> None:
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print(f"[telegram desligado] {texto}")
        return
    dados = urllib.parse.urlencode({"chat_id": chat, "text": texto}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", dados, timeout=30)
    except OSError as e:  # Telegram fora do ar não pode interromper a coleta dos outros produtos
        print(f"falha ao avisar no Telegram: {e}\n{texto}", file=sys.stderr)


def historico_valido(linhas: list[dict]) -> list[tuple[date, float]]:
    return [(date.fromisoformat(l["data"]), float(l["preco"]))
            for l in linhas if l["preco"] and l["disponivel"] == "1"]


def processar(produto: dict, linhas: list[dict], hoje: str) -> tuple[dict, str | None]:
    """Coleta um produto. Devolve (linha nova do CSV, aviso ou None). `linhas` = histórico só deste produto."""
    try:
        r = extrair.preco(produto["url"])
    except Exception as e:  # loja fora do ar, bloqueio, timeout: vira falha registrada, não derruba os outros
        print(f"erro em {produto['nome']}: {e}", file=sys.stderr)
        r = None
    nova = {"data": hoje, "url": chave(produto["url"]),
            "preco": r[0] if r else "", "disponivel": ("1" if r[1] else "0") if r else ""}
    linhas = linhas + [nova]

    if not r:
        falhas = 0
        for l in reversed(linhas):
            if l["preco"]:
                break
            falhas += 1
        print(f"{produto['nome']}: FALHOU ({falhas} seguida(s))")
        if falhas == FALHAS_PRA_AVISAR:  # avisa uma vez só, não todo dia
            return nova, f"⚠️ {produto['nome']}: não consegui ler o preço há {falhas} dias. A loja pode ter mudado.\n{produto['url']}"
        return nova, None
    if not r[1]:
        print(f"{produto['nome']}: indisponível")
        return nova, None

    hist = historico_valido(linhas)
    alvo = produto.get("alvo")
    status, motivo = veredito(hist, alvo)
    print(f"{produto['nome']}: {status} - {motivo}")
    ultima_lida = next((l for l in reversed(linhas[:-1]) if l["preco"]), None)  # ignora dias de falha
    if ultima_lida and ultima_lida["disponivel"] == "0":
        return nova, f"📦 Voltou ao estoque: {produto['nome']}\n{status}: {motivo}\n{produto['url']}"
    anterior = veredito(hist[:-1], alvo)[0] if len(hist) > 1 else None
    novo_minimo = len(hist) > 1 and hist[-1][1] < min(p for _, p in hist[:-1])
    if status == "COMPRA" and (anterior != "COMPRA" or novo_minimo):
        return nova, f"🟢 Boa hora: {produto['nome']}\n{motivo}\n{produto['url']}"
    return nova, None


def main(pasta: Path) -> None:
    with open(pasta / "produtos.toml", "rb") as f:
        produtos = tomllib.load(f).get("produto", [])
    caminho = pasta / "precos.csv"
    linhas = list(csv.DictReader(open(caminho, encoding="utf-8"))) if caminho.exists() else []
    hoje = date.today().isoformat()

    novo_arquivo = not caminho.exists()
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, CAMPOS)
        if novo_arquivo:
            escritor.writeheader()
        for produto in produtos:
            do_produto = [l for l in linhas if l["url"] == chave(produto["url"])]
            if any(l["data"] == hoje for l in do_produto):
                continue  # já coletado hoje (job rodou duas vezes)
            nova, aviso = processar(produto, do_produto, hoje)
            escritor.writerow(nova)
            f.flush()  # grava produto a produto: se cair no meio, o que já foi coletado fica salvo
            if aviso:
                avisar(aviso)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
