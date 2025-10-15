from app.db.session import engine
from sqlalchemy import text

# Drop alembic_version table
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
    conn.commit()
    print('✓ Alembic version table dropped')

# Drop the investments table
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS investments'))
    conn.commit()
    print('✓ Investments table dropped')

# Drop the itemtype enum
with engine.connect() as conn:
    conn.execute(text('DROP TYPE IF EXISTS itemtype'))
    conn.commit()
    print('✓ ItemType enum dropped')

print('\nDatabase reset complete. You can now run:')
print('alembic revision --autogenerate -m "initial schema"')
print('alembic upgrade head')
