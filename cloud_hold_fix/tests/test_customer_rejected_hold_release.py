from decimal import Decimal
from types import SimpleNamespace

from app.edge_cloud.routes import _release_rejected_fueling_hold
from app.models import CustomerWallet, WalletHold, WalletTransaction


class _FakeDb:
    def __init__(self, hold, wallet):
        self.hold = hold
        self.wallet = wallet
        self.added = []

    def get(self, model, row_id):
        assert model is WalletHold
        assert row_id == self.hold.id
        return self.hold

    def scalar(self, _statement):
        return self.wallet

    def add(self, row):
        self.added.append(row)


def _objects(status="REJECTED"):
    hold = SimpleNamespace(
        id=4,
        public_id="hold-4",
        status="HELD",
        amount=Decimal("5.00"),
        released_at=None,
    )
    wallet = SimpleNamespace(
        id=7,
        balance=Decimal("10.00"),
        reserved_balance=Decimal("5.00"),
        version=2,
    )
    fueling = SimpleNamespace(
        hold_id=hold.id,
        wallet_id=wallet.id,
        company_id=1,
        public_id="session-1",
    )
    delivery = SimpleNamespace(
        action="AUTHORIZE_FUELING_PRESET",
        status=status,
        delivery_id="delivery-1",
        error_code="CUSTOMER_HARDWARE_FUELING_DISABLED",
    )
    return hold, wallet, fueling, delivery


def test_rejected_authorization_releases_hold_and_restores_available_balance():
    hold, wallet, fueling, delivery = _objects()
    db = _FakeDb(hold, wallet)

    assert _release_rejected_fueling_hold(db, fueling, delivery) is True
    assert hold.status == "RELEASED"
    assert wallet.reserved_balance == Decimal("0")
    assert wallet.version == 3
    assert len(db.added) == 1
    transaction = db.added[0]
    assert isinstance(transaction, WalletTransaction)
    assert transaction.transaction_type == "HOLD_RELEASE"
    assert transaction.balance_before == Decimal("5.00")
    assert transaction.balance_after == Decimal("10.00")


def test_failed_after_execution_boundary_never_releases_hold_automatically():
    hold, wallet, fueling, delivery = _objects(status="FAILED")
    db = _FakeDb(hold, wallet)

    assert _release_rejected_fueling_hold(db, fueling, delivery) is False
    assert hold.status == "HELD"
    assert wallet.reserved_balance == Decimal("5.00")
    assert db.added == []
