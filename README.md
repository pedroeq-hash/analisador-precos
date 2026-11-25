# Analisador de preços

Coleta todo dia o preço de produtos que eu quero comprar e avisa no Telegram quando é uma boa hora: quando o preço está no menor patamar dos últimos 90 dias, entre os 10% mais baratos do histórico ou abaixo de um preço-alvo.

O ponto central é não cair em desconto falso: na Black Friday, "50% off" sobre um preço que subiu na semana anterior é comparado com a mediana real dos últimos meses, não com o "de" que a loja mostra.

## Como funciona

```
produtos.toml ──► extrair.py ──► precos.csv ──► analise.py ──► Telegram
 (links + alvo)   (baixa a página,  (1 linha por    (COMPRA / ESPERA /
                   lê o preço)      produto/dia)     NEUTRO / COLETANDO)
```

- **Coleta** (`precos/extrair.py`): baixa a página imitando o Chrome (`curl_cffi`) e lê o preço dos dados estruturados que as lojas publicam pro Google (JSON-LD `Product`). Só tem código específico onde isso não serve.
- **Análise** (`precos/analise.py`): regras simples e explicáveis; o motivo vai junto com o aviso.

| Status | Quando |
|---|---|
| COMPRA | preço ≤ alvo; ou abaixo da mediana de 90 dias **e** (menor preço de 90 dias ou entre os 10% mais baratos) |
| ESPERA | acima da mediana dos últimos 30 dias |
| NEUTRO | o resto (inclui preço parado há semanas) |
| COLETANDO | menos de 14 dias de histórico (só o alvo vale) |

- **Avisos** (`precos/main.py`): só quando um produto *vira* COMPRA ou bate um novo mínimo, e quando a leitura falha 3 dias seguidos (a loja provavelmente mudou a página).

Os dados (links e histórico) ficam num repositório privado separado. A coleta roda uma vez por dia no meu PC (Agendador do Windows) e faz push do CSV pra lá.

**Por que no PC e não na nuvem:** testei pelo GitHub Actions e Pichau e Terabyte responderam 403 (Cloudflare bloqueia IP de datacenter), e a Amazon devolveu página sem preço (CAPTCHA). Pela internet residencial as seis lojas funcionam.

## Lojas

| Loja | Como | Da nuvem |
|---|---|---|
| Kabum, Renner, Riachuelo | JSON-LD (preço à vista) | ✅ |
| Terabyte | JSON-LD (preço à vista) | ❌ 403 |
| Pichau | específico: o JSON-LD traz o parcelado, o Pix vem de outro campo | ❌ 403 |
| Amazon | específico (sem JSON-LD de produto) | ❌ CAPTCHA |
| Mercado Livre | 🚧 a página não traz preço; caminho: API oficial | |
| Shein, Shopee | ❌ preço só via JavaScript; com navegador automatizado (Playwright) respondem com CAPTCHA/verificação de tráfego | |
| TikTok Shop | ❌ compra acontece dentro do app | |

Antes de adicionar um link, confira o que cada método lê:

```bash
python -m precos.testar <link>
```

Ele mostra o preço de cada método (JSON-LD, meta tag, específico) e qual foi usado. Na Pichau, por exemplo, o JSON-LD dá o parcelado e uma meta tag dá lixo; só o específico acerta o Pix.

## Rodar local

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt pytest   # Linux/Mac: .venv/bin/pip
.venv/Scripts/python -m pytest
```

Crie uma pasta com um `produtos.toml`:

```toml
[[produto]]
nome = "Monitor"
url  = "https://www.kabum.com.br/produto/..."
alvo = 800        # opcional
```

e rode `python -m precos.main <pasta>`. O histórico vai pra `<pasta>/precos.csv`. Sem `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` no ambiente, os avisos saem no terminal.
