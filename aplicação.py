from avl import ArvoreAVL
from modelos import Conta, criar_conta
from rubro_negra import ArvoreRubroNegra


class InconsistenciaEntreArvores(Exception):
  """Exceção lançada quando AVL e Rubro-Negra retornam resultados divergentes."""

  pass


class AplicacaoBancaria:

  def __init__(self):
    self.avl = ArvoreAVL()
    self.rn = ArvoreRubroNegra()
    self.arvore_ativa_nome = "AVL"

  @property
  def arvore_ativa(self):
    return self.avl if self.arvore_ativa_nome == "AVL" else self.rn

  def definir_arvore_ativa(self, nome: str):
    nome_up = nome.upper()
    if nome_up not in ("AVL", "RN", "RUBRO-NEGRA"):
      raise ValueError("Árvore inválida. Escolha 'AVL' ou 'RN'.")
    self.arvore_ativa_nome = "AVL" if nome_up == "AVL" else "RN"

  def cadastrar(self, numero, titular, agencia, tipo, saldo) -> Conta:
    conta = criar_conta(numero, titular, agencia, tipo, saldo)
    res_avl = self.avl.inserir(conta)
    res_rn = self.rn.inserir(conta)

    if res_avl != res_rn:
      raise InconsistenciaEntreArvores(
          f"Divergência na inserção da conta {conta.numero}: AVL={res_avl}, RN={res_rn}"
      )
    return conta

  def remover(self, numero: int) -> Conta | None:
    res_avl = self.avl.remover(numero)
    res_rn = self.rn.remover(numero)

    if (res_avl is None) != (res_rn is None) or (
        res_avl is not None and res_avl.numero != res_rn.numero
    ):
      raise InconsistenciaEntreArvores(
          f"Divergência na remoção da conta {numero}: AVL encontrou={res_avl is not None}, RN encontrou={res_rn is not None}"
      )
    return res_avl

  def buscar(self, numero: int) -> Conta | None:
    return self.arvore_ativa.buscar(numero)

  def minimo(self) -> Conta | None:
    return self.arvore_ativa.minimo()

  def maximo(self) -> Conta | None:
    return self.arvore_ativa.maximo()

  def pre_ordem(self) -> list[Conta]:
    return self.arvore_ativa.pre_ordem()

  def em_ordem(self) -> list[Conta]:
    return self.arvore_ativa.em_ordem()

  def pos_ordem(self) -> list[Conta]:
    return self.arvore_ativa.pos_ordem()

  def altura(self) -> int:
    return self.arvore_ativa.altura()

  def tamanho(self) -> int:
    return self.arvore_ativa.tamanho()

  def exibir(self) -> str:
    return self.arvore_ativa.exibir()

  def estatisticas(self) -> dict:
    return self.arvore_ativa.estatisticas()

  def resetar_estatisticas(self):
    self.avl.resetar_estatisticas()
    self.rn.resetar_estatisticas()

  def definir_modo_detalhado(self, ativo: bool):
    self.avl.definir_modo_detalhado(ativo)
    self.rn.definir_modo_detalhado(ativo)

  def validar(self) -> tuple[bool, list[str]]:
    val_avl, err_avl = self.avl.validar()
    val_rn, err_rn = self.rn.validar()
    erros = []
    if not val_avl:
      erros.append(f"AVL: {err_avl}")
    if not val_rn:
      erros.append(f"RN: {err_rn}")
    return (len(erros) == 0, erros)