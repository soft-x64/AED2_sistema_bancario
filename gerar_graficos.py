import csv
import os
from collections import defaultdict
import matplotlib.pyplot as plt


def carregar_dados():
  dados = defaultdict(list)
  with open('resultados/resultados_brutos.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
      cenario = row['cenario']
      est = row['estrutura']
      n = int(row['n'])
      tempo = float(row['tempo_s']) * 1000  # converter s para ms
      rotacoes = int(row['rotacoes']) if row['rotacoes'] else 0
      altura = int(row['altura_depois']) if row['altura_depois'] else 0
      dados[(cenario, est, n)].append(
          {'tempo': tempo, 'rotacoes': rotacoes, 'altura': altura}
      )
  return dados


def calcular_medias(dados):
  medias = {}
  for chave, lista in dados.items():
    med_tempo = sum(item['tempo'] for item in lista) / len(lista)
    med_rot = sum(item['rotacoes'] for item in lista) / len(lista)
    med_alt = sum(item['altura'] for item in lista) / len(lista)
    medias[chave] = {
        'tempo_ms': med_tempo,
        'rotacoes': med_rot,
        'altura': med_alt,
    }
  return medias


def gerar_graficos():
  os.makedirs('resultados', exist_ok=True)
  dados = carregar_dados()
  medias = calcular_medias(dados)

  tamanhos = [100, 1000, 10000]

  # 1. Gráfico Tempo de Inserção Aleatória (Cenário B)
  tempo_avl = [
      medias.get(('B_ALEATORIO', 'AVL', n), {}).get('tempo_ms', 0)
      for n in tamanhos
  ]
  tempo_rn = [
      medias.get(('B_ALEATORIO', 'RN', n), {}).get('tempo_ms', 0)
      for n in tamanhos
  ]

  plt.figure(figsize=(8, 5))
  plt.plot(tamanhos, tempo_avl, marker='o', label='AVL', color='#2b5c8f')
  plt.plot(tamanhos, tempo_rn, marker='s', label='Rubro-Negra', color='#d9534f')
  plt.xscale('log')
  plt.title('Tempo Médio de Inserção Aleatória (Cenário B)')
  plt.xlabel('Tamanho da Árvore (N)')
  plt.ylabel('Tempo (ms)')
  plt.grid(True, which='both', linestyle='--', alpha=0.6)
  plt.legend()
  plt.tight_layout()
  plt.savefig('resultados/grafico_tempo_insercao.png', dpi=300)
  plt.close()

  # 2. Gráfico Comparações de Altura Final (Cenário B)
  alt_avl = [
      medias.get(('B_ALEATORIO', 'AVL', n), {}).get('altura', 0)
      for n in tamanhos
  ]
  alt_rn = [
      medias.get(('B_ALEATORIO', 'RN', n), {}).get('altura', 0)
      for n in tamanhos
  ]

  plt.figure(figsize=(8, 5))
  plt.plot(tamanhos, alt_avl, marker='o', label='AVL', color='#2b5c8f')
  plt.plot(tamanhos, alt_rn, marker='s', label='Rubro-Negra', color='#d9534f')
  plt.xscale('log')
  plt.title('Altura Final das Árvores (Cenário B)')
  plt.xlabel('Tamanho da Árvore (N)')
  plt.ylabel('Altura (arestas)')
  plt.grid(True, which='both', linestyle='--', alpha=0.6)
  plt.legend()
  plt.tight_layout()
  plt.savefig('resultados/grafico_altura_comparacao.png', dpi=300)
  plt.close()

  print('>> Gráficos gerados com sucesso na pasta resultados/!')


if __name__ == '__main__':
  gerar_graficos()