# AED2_sistema_bancario

# Sistema Bancário — AVL × Rubro-Negra (AED II)

Trabalho prático da disciplina de **Algoritmos e Estruturas de Dados II (AED II)**: um sistema bancário em memória que armazena e indexa contas em duas árvores de busca auto-balanceadas em simultâneo — a **Árvore AVL** e a **Árvore Rubro-Negra** —, permitindo comparar o desempenho, a estrutura e a complexidade de ambas em experimentos reprodutíveis.

## Integrantes

| Identificador | Nome | Responsabilidade principal |
|---|---|---|
| **I1** | Luis Gustavo | Árvore AVL (`avl.py`) |
| **I2** | Julio Augusto | Árvore Rubro-Negra (`rubro_negra.py`) |
| **I3** | Adriano Monteiro | Modelo, aplicação, gerador, menu, experimentos, gráficos, README e consolidação do relatório |

## Minimundo

O sistema representa o cadastro e a gestão de contas de um banco. A entidade central é a **`Conta`** (`modelos.py`), imutável e validada no momento da criação:

| Campo | Regra |
|---|---|
| `numero` | Inteiro de 1 a 9 dígitos, maior que zero; atua como a **chave** de ordenação das árvores. |
| `titular` | Texto de 2 a 100 caracteres (espaços extras são removidos automaticamente). |
| `agencia` | 1 a 4 dígitos, preenchida com zeros à esquerda (ex.: `7` → `0007`). |
| `tipo` | `CORRENTE` ou `POUPANCA` (aceita minúsculas e acentos). |
| `saldo` | `Decimal` não negativo, com até 2 casas decimais (aceita vírgula ou ponto). |

Cada operação de cadastro e remoção é executada **simultaneamente nas duas árvores**. Se os resultados estruturais divergirem, a aplicação lança a exceção `InconsistenciaEntreArvores`. As consultas (busca, mínimo, máximo, caminhamentos, altura e exibição) utilizam a árvore **ativa**, selecionada através do menu.

## Pré-requisitos e Instalação

- **Python 3.12 ou superior** (o código utiliza recursos a partir do Python 3.10; os experimentos oficiais foram validados na versão 3.13.3).
- **Dependências externas:** `matplotlib` (utilizada para o processamento dos experimentos e geração dos gráficos).

```bash
python -m venv .venv
# Linux/macOS:  source .venv/bin/activate
# Windows:      .venv\Scripts\activate
pip install -r requirements.txt