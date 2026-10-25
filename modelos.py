
"""Modelos e validações do sistema bancário."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
import unicodedata


def normalizar_numero(valor: str | int) -> int:
    """Valida e normaliza o número da conta."""
    if isinstance(valor, bool) or not isinstance(valor, (str, int)):
        raise ValueError("O número da conta deve conter apenas dígitos.")

    texto = str(valor).strip()

    if not texto or not texto.isascii() or not texto.isdigit():
        raise ValueError("O número da conta deve conter apenas dígitos.")

    if len(texto) > 9:
        raise ValueError("O número da conta deve ter até 9 dígitos.")

    numero = int(texto)

    if numero <= 0:
        raise ValueError("O número da conta deve ser maior que zero.")

    return numero


def normalizar_titular(valor: str) -> str:
    """Remove espaços extras e valida o nome do titular."""
    if not isinstance(valor, str):
        raise ValueError("O titular deve ser um texto.")

    titular = " ".join(valor.split())

    if not 2 <= len(titular) <= 100:
        raise ValueError(
            "O titular deve ter entre 2 e 100 caracteres."
        )

    return titular


def normalizar_agencia(valor: str | int) -> str:
    """Valida a agência e completa com zeros à esquerda."""
    if isinstance(valor, bool) or not isinstance(valor, (str, int)):
        raise ValueError("A agência deve conter de 1 a 4 dígitos.")

    agencia = str(valor).strip()

    if (
        not agencia
        or not agencia.isascii()
        or not agencia.isdigit()
        or len(agencia) > 4
    ):
        raise ValueError("A agência deve conter de 1 a 4 dígitos.")

    return agencia.zfill(4)


def normalizar_tipo(valor: str) -> str:
    """Normaliza o tipo para CORRENTE ou POUPANCA."""
    if not isinstance(valor, str):
        raise ValueError("O tipo deve ser um texto.")

    tipo = unicodedata.normalize("NFD", valor.strip().upper())
    tipo = "".join(
        caractere
        for caractere in tipo
        if unicodedata.category(caractere) != "Mn"
    )

    if tipo not in {"CORRENTE", "POUPANCA"}:
        raise ValueError("O tipo deve ser CORRENTE ou POUPANCA.")

    return tipo


_FORMATO_SALDO = re.compile(r"[0-9]+(?:[.,][0-9]{1,2})?")  # [0-9], não \d: \d aceita dígitos Unicode
_CENTAVOS = Decimal("0.01")


def normalizar_saldo(valor: str | int | Decimal) -> Decimal:
    """Valida o saldo e o padroniza com exatamente 2 casas decimais.

    Texto aceito: só dígitos, com vírgula ou ponto e até 2 casas
    ("1500", "1500,5", "1500.50"). Rejeita sinal, notação científica
    ("1e2"), separador "_" e separador de milhar ("1.234,56").
    """
    if isinstance(valor, bool) or not isinstance(
        valor, (str, int, Decimal)
    ):
        raise ValueError("O saldo deve ser um valor decimal válido.")

    if isinstance(valor, str):
        texto = valor.strip()

        if not texto:
            raise ValueError("O saldo não pode ficar vazio.")

        if texto.startswith("-"):
            raise ValueError("O saldo não pode ser negativo.")

        if not _FORMATO_SALDO.fullmatch(texto):
            raise ValueError(
                "O saldo deve ter só dígitos, com vírgula ou ponto e até "
                "2 casas decimais (ex.: 1500,50)."
            )

        saldo = Decimal(texto.replace(",", "."))
    else:
        saldo = Decimal(valor)

        if not saldo.is_finite():
            raise ValueError("O saldo deve ser um número finito.")

        if saldo < 0:
            raise ValueError("O saldo não pode ser negativo.")

        if saldo.as_tuple().exponent < -2:
            raise ValueError("O saldo deve ter no máximo 2 casas decimais.")

    # copy_abs() elimina o "-0"; quantize fixa sempre 2 casas (1500 → 1500.00)
    return saldo.copy_abs().quantize(_CENTAVOS)


@dataclass(frozen=True, slots=True)
class Conta:
    """Representa uma conta bancária validada e imutável."""

    numero: int
    titular: str
    agencia: str
    tipo: str
    saldo: Decimal

    def __post_init__(self) -> None:
        """Valida e normaliza os campos na criação da conta."""
        object.__setattr__(
            self, "numero", normalizar_numero(self.numero)
        )
        object.__setattr__(
            self, "titular", normalizar_titular(self.titular)
        )
        object.__setattr__(
            self, "agencia", normalizar_agencia(self.agencia)
        )
        object.__setattr__(
            self, "tipo", normalizar_tipo(self.tipo)
        )
        object.__setattr__(
            self, "saldo", normalizar_saldo(self.saldo)
        )


def criar_conta(
    numero: str | int,
    titular: str,
    agencia: str | int,
    tipo: str,
    saldo: str | int | Decimal,
) -> Conta:
    """Cria uma conta aplicando as validações do sistema."""
    return Conta(
        numero=normalizar_numero(numero),
        titular=normalizar_titular(titular),
        agencia=normalizar_agencia(agencia),
        tipo=normalizar_tipo(tipo),
        saldo=normalizar_saldo(saldo),
    )
