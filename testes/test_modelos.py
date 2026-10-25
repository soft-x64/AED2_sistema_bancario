import unittest
from decimal import Decimal

from modelos import (
    Conta,
    criar_conta,
    normalizar_numero,
    normalizar_titular,
    normalizar_agencia,
    normalizar_tipo,
    normalizar_saldo,
)


class TestModelos(unittest.TestCase):

    def test_criar_conta_valida(self):
        conta = criar_conta(
            "000123", " Ana   Silva ", "12",
            "poupança", "1500,50"
        )

        self.assertEqual(conta.numero, 123)
        self.assertEqual(conta.titular, "Ana Silva")
        self.assertEqual(conta.agencia, "0012")
        self.assertEqual(conta.tipo, "POUPANCA")
        self.assertEqual(conta.saldo, Decimal("1500.50"))

    def test_conta_eh_imutavel(self):
        conta = criar_conta(123, "Ana Silva", "12",
                            "CORRENTE", "100")

        with self.assertRaises(AttributeError):
            conta.numero = 456

    def test_normalizar_numero(self):
        self.assertEqual(normalizar_numero("000123"), 123)

        for valor in ("", "0", "-12", "12 3", "abc",
                      "1234567890", "+123"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    normalizar_numero(valor)

    def test_normalizar_titular(self):
        self.assertEqual(
            normalizar_titular("  Ana   Silva  "),
            "Ana Silva"
        )

        for valor in ("", "A", " " * 5, "A" * 101):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    normalizar_titular(valor)

    def test_normalizar_agencia(self):
        self.assertEqual(normalizar_agencia("12"), "0012")
        self.assertEqual(normalizar_agencia("1234"), "1234")

        for valor in ("", "12345", "1A", "-1"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    normalizar_agencia(valor)

    def test_normalizar_tipo(self):
        self.assertEqual(
            normalizar_tipo("poupança"), "POUPANCA"
        )
        self.assertEqual(
            normalizar_tipo("corrente"), "CORRENTE"
        )

        with self.assertRaises(ValueError):
            normalizar_tipo("investimento")

    def test_normalizar_saldo(self):
        self.assertEqual(
            normalizar_saldo("1500,50"), Decimal("1500.50")
        )
        self.assertEqual(
            normalizar_saldo("1500.50"), Decimal("1500.50")
        )

        for valor in ("-10", "abc", "10.999", ""):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    normalizar_saldo(valor)

    def test_conta_direta_tambem_valida_campos(self):
        conta = Conta(
            123, "Ana Silva", "12",
            "poupança", Decimal("100.00")
        )

        self.assertEqual(conta.agencia, "0012")
        self.assertEqual(conta.tipo, "POUPANCA")


if __name__ == "__main__":
    unittest.main()
