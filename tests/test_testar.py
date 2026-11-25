from precos.testar import relatorio

JSON_LD = '<script type="application/ld+json">{"@type":"Product","offers":{"price":"1176.47"}}</script>'


def test_mostra_os_candidatos_e_o_escolhido_na_loja_especifica():
    html = JSON_LD + r'<script>"\"avista\":1000.5"</script>'
    texto = relatorio(html, "https://www.pichau.com.br/x")
    assert "JSON-LD     R$ 1.176,47" in texto
    assert "específico  R$ 1.000,50" in texto
    assert "Preço usado: R$ 1.000,50" in texto


def test_avisa_quando_nao_acha():
    assert "Não consegui" in relatorio("<html></html>", "https://loja.com/x")
