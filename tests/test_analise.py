from datetime import date, timedelta

from precos.analise import brl, veredito

HOJE = date(2026, 11, 25)


def hist(*precos):
    """Um preço por dia, terminando hoje."""
    return [(HOJE - timedelta(days=len(precos) - 1 - i), p) for i, p in enumerate(precos)]


def test_brl():
    assert brl(1299.9) == "R$ 1.299,90"


def test_coletando_com_pouco_historico():
    assert veredito(hist(100, 90))[0] == "COLETANDO"


def test_alvo_vale_mesmo_sem_historico():
    assert veredito(hist(100, 90), alvo=95)[0] == "COMPRA"


def test_menor_preco_em_90_dias():
    assert veredito(hist(*[100] * 20, 80))[0] == "COMPRA"


def test_acima_da_mediana_espera():
    assert veredito(hist(*[100] * 20, 120))[0] == "ESPERA"


def test_desconto_falso_de_black_friday():
    # 2 meses a 100, sobe pra 150 por 10 dias e "cai" pra 130: ainda é mais caro que o normal
    status, _ = veredito(hist(*[100] * 60, *[150] * 10, 130))
    assert status == "ESPERA"


def test_entre_os_10_porcento_mais_baratos():
    # 95 é o 2º menor de 32 preços, mas não o mínimo de 90 dias (80)
    assert "10%" in veredito(hist(80, *[100] * 30, 95))[1]


def test_neutro():
    # abaixo da mediana, mas longe do mínimo (80) e fora dos 10% mais baratos
    assert veredito(hist(*[80] * 10, *[100] * 21, 95))[0] == "NEUTRO"


def test_preco_parado_nao_e_oportunidade():
    assert veredito(hist(*[100] * 30))[0] == "NEUTRO"
