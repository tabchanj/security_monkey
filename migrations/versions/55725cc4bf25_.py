"""Deprecate AWS specific Account fields (role_name, number, s3_name)

Account.number is being replaced with Account.identifier.

Revision ID: 55725cc4bf25
Revises: 1c847ae1209a
Create Date: 2017-02-16 13:41:08.162000

"""

# revision identifiers, used by Alembic.
revision = '55725cc4bf25'
down_revision = '1c847ae1209a'

from alembic import op
import sqlalchemy as sa

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Session = sessionmaker()
Base = declarative_base()


class Account(Base):
    __tablename__ = 'account'
    id = sa.Column(sa.Integer, primary_key=True)
    account_type_id = sa.Column(sa.Integer())
    identifier = sa.Column(sa.String())
    s3_name = sa.Column(sa.String(64))  # (deprecated-custom)
    role_name = sa.Column(sa.String(256))  # (deprecated-custom)


class AccountTypeCustomValues(Base):
    """
    Defines the values for custom fields defined in AccountTypeCustomFields.
    """
    __tablename__ = "account_type_values"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(64))
    value = sa.Column(sa.String(256))
    account_id = sa.Column(sa.Integer())


def update_custom_value(name, value, session, account_id):
    if not value:
        return

    cv = session.query(AccountTypeCustomValues) \
        .filter(AccountTypeCustomValues.account_id == account_id) \
        .filter(AccountTypeCustomValues.name == name)

    if cv.count():
        cv = cv.one()
        cv.value = value
    else:
        cv = AccountTypeCustomValues(name=name, value=value, account_id=account_id)

    session.add(cv)


def update_from_custom_value(name, session, account):
    cv = session.query(AccountTypeCustomValues) \
        .filter(AccountTypeCustomValues.account_id == account.id) \
        .filter(AccountTypeCustomValues.name == name)

    if not cv.count():
        return

    cv = cv.one()

    setattr(account, name, cv.value)
    session.add(account)

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # copy account.s3_name and account.role_name into custom values.
    accounts = session.query(Account).all()
    for account in accounts:
        update_custom_value('s3_name', account.s3_name, session, account.id)
        update_custom_value('role_name', account.role_name, session, account.id)

    session.commit()

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('account', 'role_name')
    op.drop_column('account', 'number')
    op.drop_column('account', 's3_name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('account', sa.Column('s3_name', sa.VARCHAR(length=64), autoincrement=False, nullable=True))
    op.add_column('account', sa.Column('number', sa.VARCHAR(length=12), autoincrement=False, nullable=True))
    op.add_column('account', sa.Column('role_name', sa.VARCHAR(length=256), autoincrement=False, nullable=True))
    # ### end Alembic commands ###

    bind = op.get_bind()
    session = Session(bind=bind)

    # copy custom values into account.s3_name and into account.role_name
    accounts = session.query(Account).all()
    for account in accounts:
        update_from_custom_value('s3_name', session, account)
        update_from_custom_value('role_name', session, account)

    session.commit()