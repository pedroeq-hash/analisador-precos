"""Decide se é uma boa hora pra comprar, olhando o histórico de preços."""
from datetime import date, timedelta
from statistics import median

DIAS_MINIMOS = 14


def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def veredito(historico: list[tuple[date, float]], alvo: float | None = None) -> tuple[str, str]:
    """historico: [(data, preço)] em ordem de data; o último item é o preço atual.

    Devolve (status, motivo), com status COMPRA, ESPERA, NEUTRO ou COLETANDO.
    """
    hoje, atual = historico[-1]
    if alvo and atual <= alvo:
        return "COMPRA", f"{brl(atual)} está abaixo do seu alvo de {brl(alvo)}"
    if (hoje - historico[0][0]).days < DIAS_MINIMOS:
        return "COLETANDO", f"histórico de só {(hoje - historico[0][0]).days + 1} dia(s); preciso de {DIAS_MINIMOS}"

    ult90 = [p for d, p in historico if d > hoje - timedelta(days=90)]
    ult30 = [p for d, p in historico if d > hoje - timedelta(days=30)]
    todos = sorted(p for _, p in historico)

    # sem essa trava, um preço parado há semanas seria sempre "o menor dos últimos 90 dias"
    if atual < median(ult90):
        if atual <= min(ult90) * 1.01:
            return "COMPRA", f"{brl(atual)} é o menor preço dos últimos 90 dias"
        if atual <= todos[len(todos) // 10]:
            return "COMPRA", f"{brl(atual)} está entre os 10% mais baratos do histórico"
    if atual > median(ult30):
        return "ESPERA", f"{brl(atual)} está acima da mediana de 30 dias ({brl(median(ult30))})"
    return "NEUTRO", f"{brl(atual)}; mínimo em 90 dias foi {brl(min(ult90))}"
