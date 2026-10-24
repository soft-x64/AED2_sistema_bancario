from decimal import Decimal, InvalidOperation
from aplicação import AplicacaoBancaria, InconsistenciaEntreArvores


def menu():
  app = AplicacaoBancaria()
  detalhado = False

  while True:
    print("\n" + "=" * 45)
    print("       SISTEMA BANCÁRIO — AVL × RN")
    print("=" * 45)
    print(f" Árvore Ativa: [{app.arvore_ativa_nome}] | Modo Detalhado: {'ON' if detalhado else 'OFF'}")
    print("-" * 45)
    print("1  Escolher árvore ativa (AVL / RN)")
    print("2  Cadastrar conta")
    print("3  Buscar conta")
    print("4  Remover conta")
    print("5  Mínimo e máximo")
    print("6  Caminhamentos (pré / em / pós)")
    print("7  Resetar estatísticas")
    print("8  Altura e tamanho")
    print("9  Exibir árvore")
    print("10 Estatísticas")
    print("11 Validar")
    print("12 Modo detalhado (liga/desliga)")
    print("13 Rodar experimentos")
    print("0  Sair")
    print("-" * 45)

    opcao = input("Escolha uma opção: ").strip()

    try:
      if opcao == "1":
        escolha = input("Digite a árvore ativa (AVL ou RN): ").strip()
        app.definir_arvore_ativa(escolha)
        print(f">> Árvore ativa alterada para: {app.arvore_ativa_nome}")

      elif opcao == "2":
        num_str = input("Número da conta (1 a 9 dígitos): ")
        titular = input("Nome do titular: ")
        agencia = input("Agência (até 4 dígitos): ")
        tipo = input("Tipo (CORRENTE ou POUPANCA): ")
        saldo_str = input("Saldo inicial: ")

        try:
          numero = int(num_str)
          saldo = Decimal(saldo_str.replace(",", "."))
          conta = app.cadastrar(numero, titular, agencia, tipo, saldo)
          print(f">> Conta {conta.numero} cadastrada com sucesso nas duas árvores!")
        except (ValueError, InvalidOperation) as e:
          print(f"[ERRO DE VALIDAÇÃO] {e}")

      elif opcao == "3":
        num_str = input("Número da conta a buscar: ")
        try:
          numero = int(num_str)
          conta = app.buscar(numero)
          if conta:
            print(f">> Conta encontrada na {app.arvore_ativa_nome}: {conta}")
          else:
            print(">> Conta não encontrada.")
        except ValueError:
          print("[ERRO] O número da conta deve ser um inteiro válido.")

      elif opcao == "4":
        num_str = input("Número da conta a remover: ")
        try:
          numero = int(num_str)
          conta = app.remover(numero)
          if conta:
            print(f">> Conta {numero} removida com sucesso das duas árvores.")
          else:
            print(">> Conta não encontrada para remoção.")
        except ValueError:
          print("[ERRO] O número da conta deve ser um inteiro válido.")

      elif opcao == "5":
        mini = app.minimo()
        maxi = app.maximo()
        print(f">> Mínimo: {mini if mini else '(vazia)'}")
        print(f">> Máximo: {maxi if maxi else '(vazia)'}")

      elif opcao == "6":
        print("1. Pré-ordem\n2. Em ordem\n3. Pós-ordem")
        sub = input("Escolha o caminhamento: ").strip()
        if sub == "1":
          res = app.pre_ordem()
        elif sub == "2":
          res = app.em_ordem()
        elif sub == "3":
          res = app.pos_ordem()
        else:
          print("[ERRO] Opção inválida.")
          continue
        print(f">> Caminhamento ({app.arvore_ativa_nome}):")
        for c in res:
          print(f"   - Conta {c.numero} | {c.titular} | Saldo: R$ {c.saldo}")

      elif opcao == "7":
        app.resetar_estatisticas()
        print(">> Estatísticas resetadas em ambas as árvores.")

      elif opcao == "8":
        print(f">> Altura ({app.arvore_ativa_nome}): {app.altura()}")
        print(f">> Tamanho ({app.arvore_ativa_nome}): {app.tamanho()}")

      elif opcao == "9":
        print(f">> Exibição da árvore ({app.arvore_ativa_nome}):")
        print(app.exibir())

      elif opcao == "10":
        stats = app.estatisticas()
        print(f">> Estatísticas ({app.arvore_ativa_nome}): {stats}")

      elif opcao == "11":
        valido, erros = app.validar()
        if valido:
          print(f">> Sucesso! Ambas as árvores estão íntegras e válidas.")
        else:
          print(f"[ERRO DE VALIDAÇÃO] Inconsistências detetadas:")
          for err in erros:
            print(f"   - {err}")

      elif opcao == "12":
        detalhado = not detalhado
        app.definir_modo_detalhado(detalhado)
        print(f">> Modo detalhado {'ligado' if detalhado else 'desligado'}.")

      elif opcao == "13":
        print(">> Para os experimentos oficiais, execute diretamente: python experimentos.py")

      elif opcao == "0":
        print(">> A sair do sistema. Até breve!")
        break
      else:
        print("[ERRO] Opção inválida. Escolha entre 0 e 13.")

    except InconsistenciaEntreArvores as e:
      print(f"\n[ERRO CRÍTICO] Inconsistência detetada entre as árvores!\n{e}")
      print("Recomenda-se executar a opção 11 (Validar) para inspecionar o estado.")

    except Exception as e:
      print(f"\n[ERRO INESPERADO] {e}")


if __name__ == "__main__":
  menu()