from decimal import Decimal

from app.models import Despesa, Divida, Meta, Patrimonio, Renda, Usuario


def criar_usuario(db, email="u@example.com") -> Usuario:
    user = Usuario(email=email, senha_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_basico(db, user_id: int) -> None:
    db.add_all(
        [
            Renda(user_id=user_id, descricao="Salário", valor=Decimal("5000"), frequencia="mensal"),
            Despesa(user_id=user_id, descricao="Aluguel", valor=Decimal("2000"), categoria="moradia", frequencia="mensal", essencial=True),
            Despesa(user_id=user_id, descricao="Seguro", valor=Decimal("600"), categoria="seguros", frequencia="anual", essencial=False),
            Divida(user_id=user_id, credor="Banco", saldo=Decimal("3000"), juros_mensal=Decimal("2.5"), parcela=Decimal("300")),
            Patrimonio(user_id=user_id, tipo="conta", descricao="Conta corrente", valor=Decimal("8000")),
            Patrimonio(user_id=user_id, tipo="bem", descricao="Carro", valor=Decimal("30000")),
            Meta(user_id=user_id, titulo="Reserva", valor_alvo=Decimal("10000"), acumulado=Decimal("4000"), prioridade=1),
        ]
    )
    db.commit()
