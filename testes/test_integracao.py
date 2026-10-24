import unittest
from aplicação import AplicacaoBancaria, InconsistenciaEntreArvores
from gerador import gerar_contas


class TestIntegracaoAplicacao(unittest.TestCase):

  def setUp(self):
    self.app = AplicacaoBancaria()

  def test_cadastro_e_sincronizacao(self):
    conta = self.app.cadastrar(123, "Maria Silva", "0123", "CORRENTE", 1500.50)
    self.assertEqual(conta.numero, 123)
    self.assertEqual(self.app.tamanho(), 1)

    # Verificar se ambas as árvores contêm a conta em ordem
    em_ordem_avl = self.app.avl.em_ordem()
    em_ordem_rn = self.app.rn.em_ordem()
    self.assertEqual(len(em_ordem_avl), 1)
    self.assertEqual(len(em_ordem_rn), 1)
    self.assertEqual(em_ordem_avl[0].numero, em_ordem_rn[0].numero)

  def test_remocao_sincronizada(self):
    self.app.cadastrar(10, "Teste Um", "0001", "CORRENTE", 100.0)
    self.app.cadastrar(20, "Teste Dois", "0002", "POUPANCA", 200.0)

    removida = self.app.remover(10)
    self.assertIsNotNone(removida)
    self.assertEqual(removida.numero, 10)
    self.assertEqual(self.app.tamanho(), 1)
    self.assertIsNone(self.app.avl.buscar(10))
    self.assertIsNone(self.app.rn.buscar(10))

  def test_validacao_geral(self):
    chaves = [50, 30, 70, 20, 40]
    contas = gerar_contas(chaves, semente=2026)
    for c in contas:
      self.app.cadastrar(c.numero, c.titular, c.agencia, c.tipo, c.saldo)

    valido, erros = self.app.validar()
    self.assertTrue(valido, f"Erros encontrados na validação: {erros}")


if __name__ == "__main__":
  unittest.main()