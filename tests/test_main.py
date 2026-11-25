from datetime import date, timedelta

import pytest

from precos import extrair, main

PRODUTO = {"nome": "Monitor", "url": "https://loja.com/p/1?utm=x"}
HOJE = date(2026, 11, 25)


def linhas(*precos):
    """Histórico do produto, um dia por preço, terminando ontem. None = falha."""
    return [{"data": (HOJE - timedelta(days=len(precos) - i)).isoformat(), "url": "https://loja.com/p/1",
             "preco": "" if p is None else str(p), "disponivel": "" if p is None else "1"}
            for i, p in enumerate(precos)]


@pytest.fixture
def coleta(monkeypatch):
    def configurar(resultado):
        monkeypatch.setattr(extrair, "preco", lambda url: resultado)
        return lambda hist: main.processar(PRODUTO, hist, HOJE.isoformat())
    return configurar


def test_chave_ignora_rastreio():
    assert main.chave("https://loja.com/p/1?utm=x#topo") == "https://loja.com/p/1"


def test_avisa_na_terceira_falha_seguida_e_so_nela(coleta):
    rodar = coleta(None)
    assert rodar(linhas(100, None))[1] is None
    assert "3 dias" in rodar(linhas(100, None, None))[1]
    assert rodar(linhas(100, None, None, None))[1] is None


def test_avisa_quando_vira_compra(coleta):
    nova, aviso = coleta((80.0, True))(linhas(*[100] * 20))
    assert nova == {"data": "2026-11-25", "url": "https://loja.com/p/1", "preco": 80.0, "disponivel": "1"}
    assert "Boa hora" in aviso


def test_nao_repete_aviso_se_continua_compra_sem_novo_minimo(coleta):
    assert coleta((80.0, True))(linhas(*[100] * 20, 80))[1] is None


def test_indisponivel_nao_avisa(coleta):
    assert coleta((10.0, False))(linhas(*[100] * 20))[1] is None


def test_main_grava_csv_e_nao_coleta_duas_vezes_no_dia(tmp_path, monkeypatch):
    (tmp_path / "produtos.toml").write_text('[[produto]]\nnome = "Monitor"\nurl = "https://loja.com/p/1"\n')
    chamadas = []
    monkeypatch.setattr(extrair, "preco", lambda url: chamadas.append(url) or (100.0, True))
    main.main(tmp_path)
    main.main(tmp_path)
    assert len(chamadas) == 1
    assert (tmp_path / "precos.csv").read_text().splitlines()[0] == "data,url,preco,disponivel"
