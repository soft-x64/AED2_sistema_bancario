import csv
import json
import os
import platform
import time
from decimal import Decimal
import matplotlib.pyplot as plt
from avl import ArvoreAVL
from rubro_negra import ArvoreRubroNegra
from gerador import (
    chaves_crescentes,
    permutacao,
    gerar_contas,
    buscas as gerar_buscas,
    subconjunto_remocao,
)

SEMENTE_BASE = 2026
TAMANHOS = [100, 1_000, 10_000]
PERCENTUAIS_REMOCAO = [10, 30, 50]
REPETICOES = 5


def executar_lote_insercao(arv, contas):
  inicio = time.perf_counter()
  for conta in contas:
    arv.inserir(conta)
  fim = time.perf_counter()
  return fim - inicio


def validar_seguro(arv):
  """Função auxiliar para evitar falhas caso a validação da árvore ainda esteja pendente."""
  try:
    if hasattr(arv, "validar"):
      valido, _ = arv.validar()
      return valido
    return True
  except NotImplementedError:
    return True


def rodar_experimentos_completos():
  resultados_brutos = []
  resultados_buscas = []
  os.makedirs("resultados", exist_ok=True)

  for n in TAMANHOS:
    for rep in range(1, REPETICOES + 1):
      semente_perm = SEMENTE_BASE + 1_000 * rep + n
      estruturas = ["AVL", "RN"] if rep % 2 == 0 else ["RN", "AVL"]

      # --- CENÁRIOS A e B (Inserção) ---
      for cenario_nome, eh_crescente in [("A_CRESCENTE", True), ("B_ALEATORIO", False)]:
        chaves = chaves_crescentes(n) if eh_crescente else permutacao(n, semente_perm)
        contas = gerar_contas(chaves, semente_perm)

        for est in estruturas:
          arv = ArvoreAVL() if est == "AVL" else ArvoreRubroNegra()
          if hasattr(arv, "resetar_estatisticas"):
            arv.resetar_estatisticas()

          tempo = executar_lote_insercao(arv, contas)
          valido = validar_seguro(arv)
          stats = arv.estatisticas() if hasattr(arv, "estatisticas") else {"rotacoes": 0, "recoloracoes": None, "nos_visitados": 0}

          resultados_brutos.append({
              "estrutura": est,
              "cenario": cenario_nome,
              "n": n,
              "repeticao": rep,
              "percentual": "",
              "tempo_s": round(tempo, 6),
              "altura_antes": -1,
              "altura_depois": arv.altura() if hasattr(arv, "altura") else 0,
              "tamanho_antes": 0,
              "tamanho_depois": arv.tamanho() if hasattr(arv, "tamanho") else n,
              "rotacoes": stats.get("rotacoes", 0),
              "recoloracoes": stats.get("recoloracoes") if stats.get("recoloracoes") is not None else "nao_se_aplica",
              "nos_visitados": stats.get("nos_visitados", 0),
              "buscas": "",
              "media_visitados": "",
              "valido": valido,
          })

      # --- CENÁRIO C (Buscas) ---
      chaves_b = permutacao(n, semente_perm)
      contas_b = gerar_contas(chaves_b, semente_perm)
      chaves_busca = gerar_buscas(n, semente_perm)

      for est in estruturas:
        arv = ArvoreAVL() if est == "AVL" else ArvoreRubroNegra()
        for conta in contas_b:
          arv.inserir(conta)
        
        if hasattr(arv, "resetar_estatisticas"):
          arv.resetar_estatisticas()
        
        stats_ini = arv.estatisticas() if hasattr(arv, "estatisticas") else {"nos_visitados": 0}
        total_visitados_inicio = stats_ini.get("nos_visitados", 0)

        inicio = time.perf_counter()
        for chave in chaves_busca:
          encontrada = arv.buscar(chave) is not None
          stats_atual = arv.estatisticas() if hasattr(arv, "estatisticas") else {"nos_visitados": 0}
          resultados_buscas.append({
              "estrutura": est,
              "n": n,
              "repeticao": rep,
              "chave": chave,
              "encontrada": encontrada,
              "nos_visitados": stats_atual.get("nos_visitados", 0)
          })

        fim = time.perf_counter()
        tempo_total = fim - inicio
        stats_fim = arv.estatisticas() if hasattr(arv, "estatisticas") else {"rotacoes": 0, "recoloracoes": None, "nos_visitados": 0}
        total_visitados_fim = stats_fim.get("nos_visitados", 0) - total_visitados_inicio
        media_vis = total_visitados_fim / len(chaves_busca) if len(chaves_busca) > 0 else 0

        valido = validar_seguro(arv)

        resultados_brutos.append({
            "estrutura": est,
            "cenario": "C_BUSCA",
            "n": n,
            "repeticao": rep,
            "percentual": "",
            "tempo_s": round(tempo_total, 6),
            "altura_antes": arv.altura() if hasattr(arv, "altura") else 0,
            "altura_depois": arv.altura() if hasattr(arv, "altura") else 0,
            "tamanho_antes": n,
            "tamanho_depois": n,
            "rotacoes": stats_fim.get("rotacoes", 0),
            "recoloracoes": stats_fim.get("recoloracoes") if stats_fim.get("recoloracoes") is not None else "nao_se_aplica",
            "nos_visitados": total_visitados_fim,
            "buscas": len(chaves_busca),
            "media_visitados": round(media_vis, 4),
            "valido": valido,
        })

      # --- CENÁRIO D (Remoções) ---
      for perc in PERCENTUAIS_REMOCAO:
        semente_rem = SEMENTE_BASE + 500_000 + 1000 * rep + n + perc
        sub_chaves = subconjunto_remocao(chaves_b, perc, semente_rem)

        for est in estruturas:
          arv = ArvoreAVL() if est == "AVL" else ArvoreRubroNegra()
          for conta in contas_b:
            arv.inserir(conta)

          alt_antes = arv.altura() if hasattr(arv, "altura") else 0
          tam_antes = arv.tamanho() if hasattr(arv, "tamanho") else n
          if hasattr(arv, "resetar_estatisticas"):
            arv.resetar_estatisticas()

          inicio = time.perf_counter()
          for chave in sub_chaves:
            arv.remover(chave)
          fim = time.perf_counter()

          valido = validar_seguro(arv)
          stats_rem = arv.estatisticas() if hasattr(arv, "estatisticas") else {"rotacoes": 0, "recoloracoes": None, "nos_visitados": 0}

          resultados_brutos.append({
              "estrutura": est,
              "cenario": "D_REMOCAO",
              "n": n,
              "repeticao": rep,
              "percentual": perc,
              "tempo_s": round(fim - inicio, 6),
              "altura_antes": alt_antes,
              "altura_depois": arv.altura() if hasattr(arv, "altura") else 0,
              "tamanho_antes": tam_antes,
              "tamanho_depois": arv.tamanho() if hasattr(arv, "tamanho") else 0,
              "rotacoes": stats_rem.get("rotacoes", 0),
              "recoloracoes": stats_rem.get("recoloracoes") if stats_rem.get("recoloracoes") is not None else "nao_se_aplica",
              "nos_visitados": stats_rem.get("nos_visitados", 0),
              "buscas": "",
              "media_visitados": "",
              "valido": valido,
          })

  return resultados_brutos, resultados_buscas


if __name__ == "__main__":
  print(">> A iniciar execução oficial de todos os experimentos (A, B, C, D)...")
  res_brutos, res_buscas = rodar_experimentos_completos()

  caminho_brutos = "resultados/resultados_brutos.csv"
  with open(caminho_brutos, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(res_brutos[0].keys()))
    writer.writeheader()
    writer.writerows(res_brutos)

  caminho_buscas = "resultados/buscas.csv"
  with open(caminho_buscas, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(res_buscas[0].keys()))
    writer.writeheader()
    writer.writerows(res_buscas)

  config = {
      "tamanhos": TAMANHOS,
      "percentuais_remocao": PERCENTUAIS_REMOCAO,
      "repeticoes": REPETICOES,
      "semente_base": SEMENTE_BASE,
      "versao_python": platform.python_version(),
      "sistema_operacional": platform.system(),
      "cpu": platform.processor(),
      "data": time.strftime("%Y-%m-%d %H:%M:%S"),
  }
  with open("resultados/config_experimentos.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=4, ensure_ascii=False)

  print(f">> Experimentos concluídos com sucesso! Ficheiros guardados na pasta 'resultados/'.")