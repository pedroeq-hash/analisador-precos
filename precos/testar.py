"""Confere o preço de um link antes de colocá-lo no produtos.toml.

Uso: python -m precos.testar <link>
"""
import sys

from precos.analise import brl
from precos.extrair import baixar, candidatos, extrair_preco


def formatar(r: tuple[float, bool] | None) -> str:
    if not r:
        return "-"
    return brl(r[0]) + ("" if r[1] else " (indisponível)")


def relatorio(html: str, url_final: str) -> str:
    linhas = [f"URL final: {url_final}"]
    linhas += [f"  {metodo:<11} {formatar(r)}" for metodo, r in candidatos(html, url_final).items()]
    escolhido = extrair_preco(html, url_final)
    if escolhido:
        linhas.append(f"Preço usado: {formatar(escolhido)}. Confira se bate com o preço à vista/Pix na página.")
    else:
        linhas.append("Não consegui ler o preço: loja não suportada ou ela bloqueou o acesso.")
    return "\n".join(linhas)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(relatorio(*baixar(sys.argv[1])))
