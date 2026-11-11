"""Gera dados/previsao.json: a chuva prevista hora a hora (próximas horas) para o centro de cada freguesia.

  python ferramentas/previsao.py              # todas as freguesias (≈3.049 pontos, ~60 pedidos, ~6 min)
  python ferramentas/previsao.py --dry-run    # só conta os pontos, não pede nada
  python ferramentas/previsao.py --pontos     # grava dados/pontos.json (para o repo só de dados)
  python ferramentas/previsao.py --horas 24   # quantas horas à frente (por omissão 24)

Fonte: Open-Meteo (https://open-meteo.com). Só lê. Pedidos em lotes, com pausa. Escrita atómica.
Licença: a API gratuita é só para uso não comercial: ver CLAUDE.md antes de publicar.
"""
import argparse, datetime, glob, json, os, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMITES = os.path.join(RAIZ, "dados", "limites")
SAIDA = os.path.join(RAIZ, "dados", "previsao.json")
PONTOS = os.path.join(RAIZ, "dados", "pontos.json")   # centros das freguesias (o repo só de dados usa este ficheiro em vez dos limites)
API = "https://api.open-meteo.com/v1/forecast"
LOTE = 50
PAUSA = 6.0   # a Open-Meteo conta cada local do lote: ~600 por minuto no plano gratuito


def centroide(rings):
    """Centroide do maior anel, em (lat, lon). Cada ponto é [lat, lon]."""
    melhor, area_max = None, -1.0
    for ring in rings:
        a = cx = cy = 0.0
        n = len(ring)
        for i in range(n):
            y1, x1 = ring[i]
            y2, x2 = ring[(i + 1) % n]
            f = x1 * y2 - x2 * y1
            a += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f
        a /= 2
        if a and abs(a) > area_max:
            area_max = abs(a)
            melhor = (cy / (6 * a), cx / (6 * a))
    return melhor or (rings[0][0][0], rings[0][0][1])


def pontos():
    ficheiros = sorted(glob.glob(os.path.join(LIMITES, "[0-9][0-9][0-9][0-9].json")))
    if not ficheiros:      # sem limites (repo só de dados): usa os pontos já calculados
        with open(PONTOS, encoding="utf-8") as fh:
            return {k: tuple(v) for k, v in json.load(fh).items()}
    out = {}
    for ficheiro in ficheiros:
        with open(ficheiro, encoding="utf-8") as fh:
            for fid, f in json.load(fh).items():
                lat, lon = centroide(f["g"])
                out[fid] = (round(lat, 4), round(lon, 4))
    return out


def pedir(lote, horas):
    q = urllib.parse.urlencode({
        "latitude": ",".join(str(p[0]) for p in lote),
        "longitude": ",".join(str(p[1]) for p in lote),
        "hourly": "precipitation",
        "forecast_hours": horas,
        "timezone": "Europe/Lisbon",
    })
    for tentativa in range(5):
        try:
            req = urllib.request.Request(API + "?" + q, headers={"User-Agent": "weather-radar/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
            return d if isinstance(d, list) else [d]
        except Exception as e:
            espera = 5 * (tentativa + 1)
            print("  falhou (%s), nova tentativa em %ds" % (e, espera))
            time.sleep(espera)
    raise SystemExit("Open-Meteo não respondeu; tenta mais tarde.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horas", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pontos", action="store_true", help="grava dados/pontos.json (centro de cada freguesia) e sai")
    a = ap.parse_args()

    pts = pontos()
    ids = list(pts)
    if a.pontos:
        tmp = PONTOS + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({k: list(v) for k, v in pts.items()}, fh, separators=(",", ":"))
        os.replace(tmp, PONTOS)
        print("escrito", PONTOS, len(pts), "freguesias")
        return
    print(len(ids), "freguesias,", -(-len(ids) // LOTE), "pedidos")
    if a.dry_run:
        return

    horas, valores = None, {}
    for i in range(0, len(ids), LOTE):
        parte = ids[i:i + LOTE]
        resp = pedir([pts[x] for x in parte], a.horas)
        if len(resp) != len(parte):
            raise SystemExit("resposta com %d locais em vez de %d" % (len(resp), len(parte)))
        for fid, d in zip(parte, resp):
            h = d["hourly"]
            if horas is None:
                horas = h["time"]
            elif h["time"] != horas:
                raise SystemExit("horas diferentes entre locais")
            valores[fid] = [None if v is None else round(v, 1) for v in h["precipitation"]]
        print("  %d/%d" % (min(i + LOTE, len(ids)), len(ids)))
        time.sleep(PAUSA)

    out = {"gerado": datetime.datetime.now().isoformat(timespec="minutes"), "fonte": "Open-Meteo",
           "unidade": "mm na hora", "horas": horas, "f": valores}
    tmp = SAIDA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, SAIDA)
    print("escrito", SAIDA, "%.0f KB" % (os.path.getsize(SAIDA) / 1024))


if __name__ == "__main__":
    main()
