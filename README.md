# meteo-dados

Dados da previsão de chuva usados por **meteo.mxm.pt**: a chuva prevista hora a hora (próximas 24 horas) para o centro de cada uma das 3.049 freguesias de Portugal Continental.

- **Ficheiro publicado:** https://jdcaldas.github.io/meteo-dados/previsao.json (atualizado de hora em hora por GitHub Actions).
- **Formato:** `{"gerado", "fonte", "unidade": "mm na hora", "horas": [...], "f": {"<código da freguesia>": [mm, ...]}}`. O código é o da CAOP2025 (DTMN, 6 dígitos).
- **Como se gera:** `python ferramentas/previsao.py` (precisa só do Python 3, sem dependências). `dados/pontos.json` tem o centro de cada freguesia.

## Fontes e licenças

- Previsão: [Open-Meteo](https://open-meteo.com/) (CC BY 4.0, uso não comercial).
- Centros das freguesias: calculados a partir da CAOP2025, © DGT (CC BY 4.0).

Este repositório só tem dados públicos. Nada aqui é pessoal ou secreto.
