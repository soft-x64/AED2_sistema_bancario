"""Executor oficial dos experimentos A, B, C e D (AED II).

Responsável: I3 · Revisor: I2

Uso:
    python experimentos.py

Gera em resultados/:
    resultados_brutos.csv     uma linha por estrutura × cenário × N × repetição × percentual
    buscas.csv                uma linha por busca do cenário C (visitas DAQUELA busca)
    config_experimentos.json  parâmetros, sementes e ambiente da coleta

Regras de justiça (PLANO.md, seção 9):
- dados gerados uma vez por (cenário, N, repetição) e entregues às duas árvores;
- árvores novas a cada medição; contadores zerados antes do lote medido;
- o cronômetro envolve SÓ o laço de operações (sem print, log, validação,
  leitura de estatísticas ou gravação);
- validação depois do cronômetro; falha marca a linha com valido=False;
- ordem alternada: repetição par AVL → RN, ímpar RN → AVL;
- uma rodada de aquecimento, descartada, antes da coleta.

Cenários A e B vêm de experimentos_insercao.py (I1).
"""

from __future__ import annotations

import csv
import json
import os
import platform
import sys
import time

import gerador
from experimentos_insercao import (
    COLUNAS_CSV,
    NAO_SE_APLICA,
    estruturas_padrao,
    executar_cenario_insercao,
    linha_csv,
    ordem_das_estruturas,
)

TAMANHOS = (100, 1_000, 10_000)
PERCENTUAIS_REMOCAO = (10, 30, 50)
REPETICOES = 5  # numeradas de 1 a 5
PASTA = "resultados"
COLUNAS_BUSCAS = ("estrutura", "n", "repeticao", "chave", "encontrada", "nos_visitados")


# ---------------------------------------------------------------------- #
# Auxiliares
# ---------------------------------------------------------------------- #
def _construir(fabrica, contas):
    """Árvore nova com a base inserida, modo detalhado desligado e contadores zerados."""
    arvore = fabrica()
    arvore.definir_modo_detalhado(False)
    for conta in contas:
        arvore.inserir(conta)
    arvore.resetar_estatisticas()
    return arvore


def _linha_base(nome: str, cenario: str, n: int, repeticao: int) -> dict:
    linha = dict.fromkeys(COLUNAS_CSV, "")
    linha.update(estrutura=nome, cenario=cenario, n=n, repeticao=repeticao)
    return linha


def _recoloracoes(estatisticas: dict):
    valor = estatisticas["recoloracoes"]
    return NAO_SE_APLICA if valor is None else valor


# ---------------------------------------------------------------------- #
# Cenário C — busca
# ---------------------------------------------------------------------- #
def medir_busca(nome, fabrica, contas, chaves_busca, n, repeticao):
    """Devolve (linha do CSV bruto, linhas do buscas.csv)."""
    arvore = _construir(fabrica, contas)
    buscar = arvore.buscar

    # 1ª passada — CRONOMETRADA: só as buscas.
    inicio = time.perf_counter()
    for chave in chaves_busca:
        buscar(chave)
    tempo = time.perf_counter() - inicio
    est = arvore.estatisticas()

    # 2ª passada — fora do cronômetro: visitas de cada busca, individualmente.
    # As buscas não alteram a árvore, então a contagem é idêntica à da 1ª passada.
    arvore.resetar_estatisticas()
    por_busca = []
    for chave in chaves_busca:
        antes = arvore.estatisticas()["nos_visitados"]
        encontrada = buscar(chave) is not None
        por_busca.append({
            "estrutura": nome, "n": n, "repeticao": repeticao, "chave": chave,
            "encontrada": encontrada,
            "nos_visitados": arvore.estatisticas()["nos_visitados"] - antes,
        })

    ok, _ = arvore.validar()
    soma = sum(b["nos_visitados"] for b in por_busca)
    linha = _linha_base(nome, "C", n, repeticao)
    linha.update(
        tempo_s=tempo,
        altura_antes=arvore.altura(), altura_depois=arvore.altura(),
        tamanho_antes=arvore.tamanho(), tamanho_depois=arvore.tamanho(),
        rotacoes=est["rotacoes"], recoloracoes=_recoloracoes(est),
        nos_visitados=est["nos_visitados"], buscas=est["buscas"],
        media_visitados=est["nos_visitados"] / est["buscas"],
        valido=ok and soma == est["nos_visitados"] and est["buscas"] == len(chaves_busca),
    )
    return linha, por_busca


# ---------------------------------------------------------------------- #
# Cenário D — remoção
# ---------------------------------------------------------------------- #
def medir_remocao(nome, fabrica, contas, chaves_remover, n, repeticao, percentual):
    arvore = _construir(fabrica, contas)
    altura_antes, tamanho_antes = arvore.altura(), arvore.tamanho()
    remover = arvore.remover

    inicio = time.perf_counter()
    for chave in chaves_remover:
        remover(chave)
    tempo = time.perf_counter() - inicio

    ok, _ = arvore.validar()
    est = arvore.estatisticas()
    linha = _linha_base(nome, "D", n, repeticao)
    linha.update(
        percentual=percentual, tempo_s=tempo,
        altura_antes=altura_antes, altura_depois=arvore.altura(),
        tamanho_antes=tamanho_antes, tamanho_depois=arvore.tamanho(),
        rotacoes=est["rotacoes"], recoloracoes=_recoloracoes(est),
        valido=ok and arvore.tamanho() == tamanho_antes - len(chaves_remover),
    )
    return linha


# ---------------------------------------------------------------------- #
# Execução
# ---------------------------------------------------------------------- #
def aquecer(estruturas) -> None:
    """Rodada descartada: carrega o código e aquece o interpretador antes da coleta."""
    chaves = gerador.permutacao(2_000, 1)
    contas = gerador.gerar_contas(chaves, 1)
    for _, fabrica in estruturas:
        arvore = _construir(fabrica, contas)
        for k in chaves[:1_000]:
            arvore.buscar(k)
            arvore.remover(k)


def executar(estruturas=None, tamanhos=TAMANHOS, repeticoes=REPETICOES,
             percentuais=PERCENTUAIS_REMOCAO, progresso=True):
    """Roda A, B, C e D. Devolve (linhas brutas, linhas de buscas)."""
    estruturas = estruturas or estruturas_padrao()
    aquecer(estruturas)
    brutos, buscas = [], []

    for n in tamanhos:
        for rep in range(1, repeticoes + 1):
            if progresso:
                print(f"   N = {n:>6}  ·  repetição {rep}/{repeticoes}", flush=True)
            ordem = ordem_das_estruturas(estruturas, rep)

            # A e B — módulo do I1 (já alterna a ordem internamente)
            for cenario in ("A", "B"):
                brutos += [linha_csv(l) for l in executar_cenario_insercao(cenario, n, rep, estruturas)]

            # Base de C e D: a mesma permutação do cenário B
            semente = gerador.semente_permutacao(n, rep)
            chaves_base = gerador.permutacao(n, semente)
            contas_base = gerador.gerar_contas(chaves_base, semente)

            # C — busca
            chaves_busca = gerador.buscas(n, semente)
            for nome, fabrica in ordem:
                linha, por_busca = medir_busca(nome, fabrica, contas_base, chaves_busca, n, rep)
                brutos.append(linha)
                buscas += por_busca

            # D — remoção (base reconstruída do zero para cada percentual)
            for perc in percentuais:
                remover = gerador.subconjunto_remocao(
                    chaves_base, perc, gerador.semente_subconjunto(n, rep, perc))
                for nome, fabrica in ordem:
                    brutos.append(medir_remocao(nome, fabrica, contas_base, remover, n, rep, perc))

    return brutos, buscas


def _gravar_csv(caminho, colunas, linhas) -> None:
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def configuracao() -> dict:
    return {
        "tamanhos": list(TAMANHOS),
        "percentuais_remocao": list(PERCENTUAIS_REMOCAO),
        "repeticoes": REPETICOES,
        "numeracao_repeticoes": "1 a 5",
        "semente_base": gerador.SEMENTE_BASE,
        "semente_permutacao": "SEMENTE_BASE + 1000*repeticao + n (permutação, contas e buscas)",
        "semente_subconjunto": "SEMENTE_BASE + 500000 + 1000*repeticao + n + percentual",
        "ordem_estruturas": "repetição par: AVL → RN; ímpar: RN → AVL",
        "aquecimento": "1 rodada descartada antes da coleta",
        "unidade_tempo": "segundos (time.perf_counter)",
        "python": f"{platform.python_implementation()} {platform.python_version()}",
        "sistema_operacional": platform.platform(),
        "processador": platform.processor() or platform.machine(),
        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> None:
    os.makedirs(PASTA, exist_ok=True)
    print(">> Iniciando a coleta oficial (A, B, C e D)...")
    inicio = time.perf_counter()
    brutos, buscas = executar()

    _gravar_csv(os.path.join(PASTA, "resultados_brutos.csv"), COLUNAS_CSV, brutos)
    _gravar_csv(os.path.join(PASTA, "buscas.csv"), COLUNAS_BUSCAS, buscas)
    with open(os.path.join(PASTA, "config_experimentos.json"), "w", encoding="utf-8") as f:
        json.dump(configuracao(), f, indent=4, ensure_ascii=False)

    invalidas = sum(1 for l in brutos if l["valido"] is not True)
    print(f">> {len(brutos)} medições e {len(buscas)} buscas gravadas em {PASTA}/ "
          f"({time.perf_counter() - inicio:.0f} s).")
    if invalidas:
        print(f"[ATENÇÃO] {invalidas} medição(ões) com valido=False — veja o CSV.")
        sys.exit(1)
    print(">> Todas as medições terminaram com árvores válidas.")


if __name__ == "__main__":
    main()
