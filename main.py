"""Menu interativo do Sistema Bancário — AVL × Rubro-Negra (AED II).

Responsável: I3 · Revisor: I2

Uso:
    python main.py

As entradas digitadas são repassadas como texto para a aplicação, que as
valida com as regras de modelos.py (nada é convertido antes aqui).
"""

from aplicacao import AplicacaoBancaria, ContaDuplicada, InconsistenciaEntreArvores

LARGURA = 52

OPCOES = (
    ("1", "Escolher árvore ativa (AVL / RN)"),
    ("2", "Cadastrar conta"),
    ("3", "Buscar conta"),
    ("4", "Remover conta"),
    ("5", "Mínimo e máximo"),
    ("6", "Caminhamentos (pré / em / pós-ordem)"),
    ("7", "Resetar estatísticas"),
    ("8", "Altura e tamanho"),
    ("9", "Exibir árvore"),
    ("10", "Estatísticas"),
    ("11", "Validar"),
    ("12", "Modo detalhado (liga / desliga)"),
    ("13", "Rodar experimentos oficiais"),
    ("0", "Sair"),
)


def formatar_conta(conta) -> str:
    saldo = f"{conta.saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return (f"Conta {conta.numero} | {conta.titular} | Agência {conta.agencia} | "
            f"{conta.tipo} | Saldo R$ {saldo}")


def mostrar_cabecalho(app, detalhado: bool) -> None:
    print("\n" + "=" * LARGURA)
    print("SISTEMA BANCÁRIO — AVL × RUBRO-NEGRA".center(LARGURA))
    print("=" * LARGURA)
    print(f" Árvore ativa: {app.arvore_ativa_nome}   |   "
          f"Modo detalhado: {'LIGADO' if detalhado else 'DESLIGADO'}")
    print("-" * LARGURA)
    for codigo, texto in OPCOES:
        print(f" {codigo:>2}  {texto}")
    print("-" * LARGURA)


def ler(rotulo: str) -> str:
    return input(f"{rotulo}: ")


def cadastrar(app) -> None:
    conta = app.cadastrar(
        ler("Número da conta (1 a 9 dígitos)"),
        ler("Titular"),
        ler("Agência (até 4 dígitos)"),
        ler("Tipo (CORRENTE ou POUPANCA)"),
        ler("Saldo (ex.: 1500,50)"),
    )
    print(f">> Cadastrada nas duas árvores: {formatar_conta(conta)}")


def buscar(app) -> None:
    conta = app.buscar(ler("Número da conta"))
    if conta:
        print(f">> Encontrada na {app.arvore_ativa_nome}: {formatar_conta(conta)}")
    else:
        print(">> Conta não encontrada.")
    visitados = app.estatisticas()["nos_visitados"]
    print(f"   (nós visitados acumulados na {app.arvore_ativa_nome}: {visitados})")


def remover(app) -> None:
    conta = app.remover(ler("Número da conta a remover"))
    if conta:
        print(f">> Removida das duas árvores: {formatar_conta(conta)}")
    else:
        print(">> Conta não encontrada; nada foi alterado.")


def minimo_maximo(app) -> None:
    if app.tamanho() == 0:
        print(">> A árvore está vazia.")
        return
    print(f">> Mínimo: {formatar_conta(app.minimo())}")
    print(f">> Máximo: {formatar_conta(app.maximo())}")


def caminhamentos(app) -> None:
    tipos = {"1": ("Pré-ordem", app.pre_ordem), "2": ("Em ordem", app.em_ordem),
             "3": ("Pós-ordem", app.pos_ordem)}
    escolha = ler("1 Pré-ordem · 2 Em ordem · 3 Pós-ordem").strip()
    if escolha not in tipos:
        print("[ERRO] Opção inválida.")
        return
    nome, metodo = tipos[escolha]
    contas = metodo()
    print(f">> {nome} ({app.arvore_ativa_nome}, {len(contas)} contas):")
    if not contas:
        print("   (árvore vazia)")
    for conta in contas:
        print(f"   {formatar_conta(conta)}")


def estatisticas(app) -> None:
    e = app.estatisticas()
    print(f">> Estatísticas da {app.arvore_ativa_nome} (desde o último reset):")
    print(f"   Rotações ............ {e['rotacoes']}")
    recoloracoes = "não se aplica" if e["recoloracoes"] is None else e["recoloracoes"]
    print(f"   Recolorações ........ {recoloracoes}")
    print(f"   Buscas .............. {e['buscas']}")
    print(f"   Nós visitados ....... {e['nos_visitados']}")
    if e["buscas"]:
        print(f"   Média por busca ..... {e['nos_visitados'] / e['buscas']:.2f}")
    if app.arvore_ativa_nome == "AVL":
        print(f"   Casos (AVL) ......... {app.avl.rotacoes_por_caso()}")


def validar(app) -> None:
    ok, erros = app.validar()
    if ok:
        print(">> As duas árvores são válidas e guardam a mesma coleção.")
    else:
        print("[ERRO DE VALIDAÇÃO] Violações encontradas:")
        for erro in erros:
            print(f"   - {erro}")


def rodar_experimentos() -> None:
    resposta = ler("A coleta completa leva alguns minutos e sobrescreve resultados/. "
                   "Continuar? (s/n)").strip().lower()
    if resposta != "s":
        print(">> Cancelado.")
        return
    import experimentos  # import tardio: o menu não depende do módulo para abrir
    experimentos.main()


def menu() -> None:
    app = AplicacaoBancaria()
    detalhado = False

    while True:
        mostrar_cabecalho(app, detalhado)
        try:
            opcao = ler("Escolha uma opção").strip()
            if opcao == "1":
                app.definir_arvore_ativa(ler("Árvore (AVL ou RN)"))
                print(f">> Árvore ativa: {app.arvore_ativa_nome}")
            elif opcao == "2":
                cadastrar(app)
            elif opcao == "3":
                buscar(app)
            elif opcao == "4":
                remover(app)
            elif opcao == "5":
                minimo_maximo(app)
            elif opcao == "6":
                caminhamentos(app)
            elif opcao == "7":
                app.resetar_estatisticas()
                print(">> Estatísticas zeradas nas duas árvores.")
            elif opcao == "8":
                print(f">> {app.arvore_ativa_nome}: altura {app.altura()} "
                      f"(arestas; vazia = -1) · tamanho {app.tamanho()}")
            elif opcao == "9":
                print(f">> {app.arvore_ativa_nome}:")
                print(app.exibir())
            elif opcao == "10":
                estatisticas(app)
            elif opcao == "11":
                validar(app)
            elif opcao == "12":
                detalhado = not detalhado
                app.definir_modo_detalhado(detalhado)
                print(f">> Modo detalhado {'ligado' if detalhado else 'desligado'}.")
            elif opcao == "13":
                rodar_experimentos()
            elif opcao == "0":
                print(">> Encerrando. Até logo!")
                break
            else:
                print("[ERRO] Opção inválida. Digite um número de 0 a 13.")

        except ContaDuplicada as erro:
            print(f"[AVISO] {erro} Nada foi alterado.")
        except ValueError as erro:
            print(f"[ERRO DE VALIDAÇÃO] {erro}")
        except InconsistenciaEntreArvores as erro:
            print(f"\n[ERRO CRÍTICO] As árvores divergiram!\n{erro}")
            print("Execute a opção 11 (Validar) para inspecionar as duas estruturas.")
        except (KeyboardInterrupt, EOFError):
            print("\n>> Encerrando. Até logo!")
            break


if __name__ == "__main__":
    menu()
