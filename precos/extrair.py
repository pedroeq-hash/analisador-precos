"""Baixa a página de um produto e extrai o preço."""
import json
import re

from curl_cffi import requests


# Lojas em que o JSON-LD não serve. Chave: trecho do domínio; valor: regex com o preço no grupo 1.
ESPECIFICOS = {
    "amazon.com.br": r'"priceAmount":([\d.]+)',  # Amazon não publica JSON-LD de produto
    "pichau.com.br": r'\\?"avista\\?":([\d.]+)',  # o JSON-LD da Pichau traz o parcelado; o Pix fica aqui
}


def para_float(valor) -> float | None:
    """Aceita 1299.9, "1299.90", "1.299,90" ou "R$ 1.299,90"."""
    if isinstance(valor, (int, float)):
        return float(valor)
    s = re.sub(r"[^\d.,]", "", str(valor))
    if "," in s:  # formato brasileiro: ponto é milhar, vírgula é decimal
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _dicts(dado):
    """Percorre o JSON inteiro (listas, @graph, aninhados) devolvendo cada dict."""
    if isinstance(dado, dict):
        yield dado
        for v in dado.values():
            yield from _dicts(v)
    elif isinstance(dado, list):
        for v in dado:
            yield from _dicts(v)


def _do_json_ld(html: str):
    for bloco in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", html, re.S | re.I):
        try:
            dados = json.loads(bloco)
        except ValueError:
            continue
        for d in _dicts(dados):
            tipo = d.get("@type")
            if "Product" not in (tipo if isinstance(tipo, list) else [tipo]):
                continue
            for oferta in _dicts(d.get("offers")):
                preco = para_float(oferta.get("price") or oferta.get("lowPrice") or "")
                if preco:
                    disponivel = "InStock" in str(oferta.get("availability", "InStock"))
                    return preco, disponivel
    return None


def _da_meta(html: str):
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        attrs = dict(re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', tag))
        nome = attrs.get("property") or attrs.get("itemprop") or attrs.get("name")
        if nome in ("product:price:amount", "og:price:amount", "price") and attrs.get("content"):
            preco = para_float(attrs["content"])
            if preco:
                return preco, True
    return None


def extrair_preco(html: str, url: str = "") -> tuple[float, bool] | None:
    """Devolve (preço, disponível) ou None se não achou. `url` é a final, depois dos redirecionamentos."""
    geral = _do_json_ld(html) or _da_meta(html)
    for dominio, padrao in ESPECIFICOS.items():
        if dominio in url:
            m = re.search(padrao, html)
            return (float(m.group(1)), geral[1] if geral else True) if m else None
    return geral


def preco(url: str) -> tuple[float, bool] | None:
    # impersonate imita o TLS/cabeçalhos do Chrome; sem isso o Cloudflare bloqueia várias lojas
    r = requests.get(url, impersonate="chrome", timeout=30)
    r.raise_for_status()
    return extrair_preco(r.text, r.url)
