from precos.extrair import extrair_preco, para_float


def test_para_float():
    assert para_float("1.299,90") == 1299.9
    assert para_float("R$ 1.299,90") == 1299.9
    assert para_float("1299.90") == 1299.9
    assert para_float(1299) == 1299.0


def test_json_ld_com_graph_e_lista_de_ofertas():
    html = """<script type="application/ld+json">
    {"@graph": [{"@type": "BreadcrumbList"},
                {"@type": "Product", "offers": [{"price": "1.299,90",
                 "availability": "https://schema.org/OutOfStock"}]}]}
    </script>"""
    assert extrair_preco(html) == (1299.9, False)


def test_json_ld_aggregate_offer():
    html = '<script type="application/ld+json">{"@type":"Product","offers":{"@type":"AggregateOffer","lowPrice":99.5}}</script>'
    assert extrair_preco(html) == (99.5, True)


def test_meta_tag_com_atributos_em_qualquer_ordem():
    assert extrair_preco('<meta content="49.90" property="product:price:amount">') == (49.9, True)


# Trechos copiados da estrutura real de cada loja (nov/2026), com valores trocados.
def test_pichau_usa_preco_pix_e_nao_o_parcelado_do_json_ld():
    html = ('<script type="application/ld+json">{"@type":"Product","offers":{"price":"1176.47",'
            '"availability":"https://schema.org/InStock"}}</script>'
            r'<script>self.__next_f.push("\"pichau_prices\":{\"avista\":1000.5,\"final_price\":1176.47}")</script>')
    assert extrair_preco(html, "https://www.pichau.com.br/produto-x") == (1000.5, True)


def test_amazon():
    html = '<span class="a-offscreen">R$ 99,90</span><script>{"priceAmount":59.90,"currencySymbol":"R$"}</script>'
    assert extrair_preco(html, "https://www.amazon.com.br/dp/B000000000") == (59.9, True)


def test_loja_especifica_sem_o_padrao_e_falha():
    assert extrair_preco("<html>captcha</html>", "https://www.amazon.com.br/dp/X") is None


def test_sem_preco():
    assert extrair_preco("<html>nada aqui</html>") is None
