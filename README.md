# Sistema Bancário com Árvores AVL e Rubro-Negra

Trabalho prático de **Algoritmos e Estruturas de Dados II (AED II)** — UFAM.

Um cadastro de contas bancárias em memória, guardado **ao mesmo tempo** em uma árvore **AVL** e em uma árvore **Rubro-Negra**, ambas implementadas pela equipe (sem bibliotecas de árvore). As duas recebem as mesmas operações e os mesmos dados e são comparadas por experimentos reproduzíveis.

## Equipe

| Integrante | Responsabilidade |
| --- | --- |
| **I1** — Luiz Gustavo | Árvore AVL (`avl.py`), cenários A e B (`experimentos_insercao.py`), revisão da Rubro-Negra e do modelo |
| **I2** — Julio Augusto | Árvore Rubro-Negra (`rubro_negra.py`), revisão da aplicação e dos experimentos |
| **I3** — Adriano Monteiro | Modelo, aplicação, menu, gerador, experimentos C e D, gráficos, documentação; revisão da AVL |

## Requisitos

- **Python 3.12 ou superior**
- Árvores, aplicação, menu, experimentos e testes usam **só a biblioteca padrão**
- `matplotlib` é necessário **apenas** para `gerar_graficos.py`

## Instalação

```bash
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux / macOS:         source .venv/bin/activate
pip install -r requirements.txt
```

## Como executar

| O quê | Comando |
| --- | --- |
| Menu interativo | `python main.py` |
| Todos os testes | `python -m unittest discover -s testes -v` |
| Coleta oficial dos experimentos (A, B, C, D) | `python experimentos.py` |
| Resumo estatístico e gráficos | `python gerar_graficos.py` |
| Demonstração passo a passo da AVL | `python demo_avl.py --pausar` |

**Modo detalhado:** no menu, a opção **12** liga e desliga o passo a passo. Com ele ligado, cada inserção, busca e remoção mostra as comparações, os casos de rebalanceamento, as rotações e as recolorações, por exemplo:

```
[AVL] desbalanceado em 30 (FB=+2) → caso LR
[AVL] rotação à esquerda em 10 → 20 sobe
[AVL] rotação à direita em 30 → 20 sobe
[RN] tio 30 vermelho → recolorir 20(P), 30(P), 25(V)
```

### Menu

```
 1  Escolher árvore ativa (AVL / RN)      8  Altura e tamanho
 2  Cadastrar conta                       9  Exibir árvore
 3  Buscar conta                         10  Estatísticas
 4  Remover conta                        11  Validar
 5  Mínimo e máximo                      12  Modo detalhado (liga / desliga)
 6  Caminhamentos (pré / em / pós)       13  Rodar experimentos oficiais
 7  Resetar estatísticas                  0  Sair
```

Cadastro e remoção são aplicados **às duas árvores**; as consultas usam a **árvore ativa**. Se as duas devolverem resultados diferentes, a aplicação interrompe a operação com **ERRO CRÍTICO**.

## Modelo: a entidade `Conta`

`Conta` (`modelos.py`) é um `dataclass` **imutável** que valida e normaliza os campos na criação. Entrada inválida gera `ValueError` com mensagem explicativa.

| Campo | Tipo | Regra | Exemplo |
| --- | --- | --- | --- |
| `numero` | `int` | só dígitos, de 1 a 9, maior que zero; sem sinal nem espaços internos | `" 000123 "` → `123` |
| `titular` | `str` | 2 a 100 caracteres; espaços repetidos são colapsados | `" Ana   Silva "` → `"Ana Silva"` |
| `agencia` | `str` | 1 a 4 dígitos, completada com zeros à esquerda | `"12"` → `"0012"` |
| `tipo` | `str` | `CORRENTE` ou `POUPANCA` (aceita minúsculas e acentos) | `"poupança"` → `"POUPANCA"` |
| `saldo` | `Decimal` | não negativo, até 2 casas, vírgula ou ponto; guardado sempre com 2 casas | `"1500,5"` → `1500.50` |

**Chave de ordenação:** somente `numero`. `000123` e `123` são a mesma conta.

| Situação | Comportamento |
| --- | --- |
| Número já cadastrado | rejeitado; nada é alterado (`inserir` devolve `False`; o menu avisa) |
| Busca ou remoção de número inexistente | "não encontrada"; nada é alterado |
| Árvore vazia | consultas respondem com segurança: `None`, lista vazia, altura `-1`, tamanho `0` |

## Convenções (iguais nas duas árvores)

| Item | Regra |
| --- | --- |
| Altura | em **arestas**: árvore vazia = `-1`, folha = `0`; o NIL não conta |
| NIL (Rubro-Negra) | um sentinela por árvore, sempre preto; nunca retornado nem exibido |
| Nós visitados | contados **só em `buscar()`**: cada nó real cuja chave foi comparada |
| Rotações | simples = 1; dupla (AVL LR/RL, triângulo da RN) = 2 |
| Recolorações (RN) | contam só quando a cor muda; o nó novo nasce vermelho (não conta) |
| Remoção com 2 filhos | o **sucessor** (mínimo da subárvore direita) assume o lugar, com a conta inteira |

## Experimentos e reprodução

| Cenário | O que mede |
| --- | --- |
| **A** | inserção de `1..N` em ordem crescente |
| **B** | inserção de uma permutação aleatória de `1..N` |
| **C** | `2N` buscas (N presentes + N ausentes) numa árvore montada como em B |
| **D** | remoção de 10%, 30% e 50% das chaves de uma árvore montada como em B |

- Tamanhos `N = 100, 1.000, 10.000`; **5 repetições** cada.
- **Sementes** (fonte única em `gerador.py`): `SEMENTE_BASE = 2026`; permutação, contas e buscas usam `2026 + 1000·repetição + N`; o subconjunto removido usa `2026 + 500000 + 1000·repetição + N + percentual`. Mesma semente ⇒ mesmos dados.
- Só o laço de operações é cronometrado (`time.perf_counter`); a validação vem depois.
- A ordem AVL/RN alterna entre as repetições, e uma rodada de aquecimento é descartada.

Para reproduzir:

```bash
python experimentos.py
python gerar_graficos.py
```

## Onde está cada coisa

```
├── modelos.py                 Conta e validações
├── avl.py                     Árvore AVL
├── rubro_negra.py             Árvore Rubro-Negra
├── aplicacao.py               Coleção comum nas duas árvores
├── main.py                    Menu interativo
├── gerador.py                 Dados e sementes reprodutíveis
├── experimentos_insercao.py   Cenários A e B
├── experimentos.py            Executor oficial (A, B, C, D)
├── gerar_graficos.py          Resumo estatístico e gráficos
├── demo_avl.py                Demonstração da AVL
├── testes/                    Testes automatizados (unittest)
├── resultados/                CSVs brutos, resumo, configuração e gráficos (PNG)
└── relatorio/                 Relatório final (PDF) e fonte LaTeX
```

| Arquivo em `resultados/` | Conteúdo |
| --- | --- |
| `resultados_brutos.csv` | uma linha por estrutura × cenário × N × repetição × percentual |
| `buscas.csv` | uma linha por busca do cenário C, com os nós visitados naquela busca |
| `resumo_medias.csv` | média e desvio-padrão das 5 repetições de cada grupo |
| `config_experimentos.json` | parâmetros, sementes e ambiente da coleta |
| `grafico_*.png` | gráficos de tempo, altura, busca e remoção |
