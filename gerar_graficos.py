"""Resumo estatístico e gráficos a partir de resultados/resultados_brutos.csv (AED II).

Responsável: I3 · Revisor: I2

Uso:
    python gerar_graficos.py

Gera em resultados/:
    resumo_medias.csv            média e desvio-padrão (5 repetições) de cada grupo
    grafico_insercao_tempo.png   tempo de inserção, cenários A e B
    grafico_altura.png           altura final, cenários A e B
    grafico_busca.png            nós visitados por busca e tempo de busca, cenário C
    grafico_remocao.png          tempo e rotações na remoção (N = 10.000), cenário D
"""

from __future__ import annotations

import csv
import os
import statistics as st
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")  # gera arquivos sem abrir janela
import matplotlib.pyplot as plt

PASTA = "resultados"
ESTILO = {  # paleta validada para daltonismo + marcadores diferentes (identidade não só por cor)
    "AVL": {"color": "#1F5A99", "marker": "o", "label": "AVL"},
    "RN": {"color": "#C23B32", "marker": "s", "label": "Rubro-Negra"},
}
METRICAS = ("tempo_ms", "altura_depois", "rotacoes", "recoloracoes", "media_visitados")


def carregar(caminho: str = os.path.join(PASTA, "resultados_brutos.csv")) -> dict:
    """Agrupa as linhas válidas por (cenário, percentual, N, estrutura)."""
    grupos = defaultdict(list)
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if linha["valido"] != "True":
                continue  # medições inválidas ficam fora da análise
            linha["tempo_ms"] = float(linha["tempo_s"]) * 1000
            chave = (linha["cenario"], linha["percentual"], int(linha["n"]), linha["estrutura"])
            grupos[chave].append(linha)
    return grupos


def _numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None  # vazio ou "nao_se_aplica"


def resumir(grupos: dict) -> dict:
    resumo = {}
    for chave, linhas in grupos.items():
        resumo[chave] = {"repeticoes": len(linhas)}
        for metrica in METRICAS:
            valores = [v for v in (_numero(l[metrica]) for l in linhas) if v is not None]
            if valores:
                resumo[chave][metrica] = st.mean(valores)
                resumo[chave][metrica + "_dp"] = st.stdev(valores) if len(valores) > 1 else 0.0
    return resumo


def gravar_resumo(resumo: dict) -> None:
    colunas = ["cenario", "percentual", "n", "estrutura", "repeticoes"]
    for m in METRICAS:
        colunas += [m, m + "_dp"]
    with open(os.path.join(PASTA, "resumo_medias.csv"), "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas)
        escritor.writeheader()
        for (cen, perc, n, est), valores in sorted(resumo.items()):
            escritor.writerow({"cenario": cen, "percentual": perc, "n": n, "estrutura": est,
                               **{k: (round(v, 6) if isinstance(v, float) else v)
                                  for k, v in valores.items()}})


def _serie(resumo, cenario, estrutura, metrica, tamanhos, percentual=""):
    return [resumo.get((cenario, percentual, n, estrutura), {}).get(metrica) for n in tamanhos]


def _eixo(ax, titulo, rotulo_y, rotulo_x="Tamanho da árvore (N)", log_x=True):
    ax.set_title(titulo, fontsize=11)
    ax.set_xlabel(rotulo_x)
    ax.set_ylabel(rotulo_y)
    if log_x:
        ax.set_xscale("log")
    ax.grid(True, which="major", color="#e3e3e3", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)


def _linhas(ax, x, series):
    for estrutura, y in series.items():
        ax.plot(x, y, linewidth=2, markersize=6, **ESTILO[estrutura])


def figura_dupla(nome, paineis, rotulo_y, tamanhos):
    fig, eixos = plt.subplots(1, 2, figsize=(10, 4))
    for ax, (titulo, series) in zip(eixos, paineis):
        _linhas(ax, tamanhos, series)
        _eixo(ax, titulo, rotulo_y)
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA, nome), dpi=200)
    plt.close(fig)


def gerar(resumo: dict) -> None:
    tamanhos = sorted({n for (_, _, n, _) in resumo})
    est = ("AVL", "RN")

    figura_dupla("grafico_insercao_tempo.png", [
        (f"Cenário {c} — inserção {nome}",
         {e: _serie(resumo, c, e, "tempo_ms", tamanhos) for e in est})
        for c, nome in (("A", "crescente"), ("B", "aleatória"))
    ], "Tempo médio (ms)", tamanhos)

    figura_dupla("grafico_altura.png", [
        (f"Cenário {c} — inserção {nome}",
         {e: _serie(resumo, c, e, "altura_depois", tamanhos) for e in est})
        for c, nome in (("A", "crescente"), ("B", "aleatória"))
    ], "Altura final (arestas)", tamanhos)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    _linhas(a1, tamanhos, {e: _serie(resumo, "C", e, "media_visitados", tamanhos) for e in est})
    _eixo(a1, "Cenário C — nós visitados por busca", "Média de nós visitados")
    _linhas(a2, tamanhos, {e: _serie(resumo, "C", e, "tempo_ms", tamanhos) for e in est})
    _eixo(a2, "Cenário C — tempo de 2N buscas", "Tempo médio (ms)")
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA, "grafico_busca.png"), dpi=200)
    plt.close(fig)

    n_max = max(tamanhos)
    percentuais = sorted({int(p) for (c, p, _, _) in resumo if c == "D"})
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    for ax, metrica, rotulo in ((a1, "tempo_ms", "Tempo médio (ms)"), (a2, "rotacoes", "Rotações (média)")):
        _linhas(ax, percentuais, {e: [resumo.get(("D", str(p), n_max, e), {}).get(metrica)
                                      for p in percentuais] for e in est})
        n_txt = f"{n_max:,}".replace(",", ".")  # 10000 → 10.000
        _eixo(ax, f"Cenário D — remoção, N = {n_txt}", rotulo,
              rotulo_x="Chaves removidas (%)", log_x=False)
        ax.set_xticks(percentuais)
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA, "grafico_remocao.png"), dpi=200)
    plt.close(fig)


def main() -> None:
    resumo = resumir(carregar())
    gravar_resumo(resumo)
    gerar(resumo)
    print(f">> resumo_medias.csv e 4 gráficos gravados em {PASTA}/.")


if __name__ == "__main__":
    main()
