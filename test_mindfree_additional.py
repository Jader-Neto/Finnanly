import json
import os
import shutil
from pathlib import Path

import mindfree_pro


TEST_DATA = "mindfree_test_data.json"


def setup_test_data():
    base = {
        "users": [],
        "groups": [],
        "expenses": [],
        "payments": [],
        "categories": mindfree_pro.MindfreeSystem.DEFAULT_CATEGORIES,
        "counters": {
            "next_user_id": 1,
            "next_group_id": 1,
            "next_expense_id": 1,
            "next_payment_id": 1,
        },
    }
    with open(TEST_DATA, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)


def run_tests():
    if Path(TEST_DATA).exists():
        Path(TEST_DATA).unlink()
    setup_test_data()

    # apontar o módulo para usar o arquivo de teste isolado
    mindfree_pro.DATA_FILE = TEST_DATA
    ms = mindfree_pro.MindfreeSystem()

    print("=== Test: registro de usuários ===")
    u1 = ms.register_user("Alice", "alice@example.com", "pwd")
    u2 = ms.register_user("Bob", "bob@example.com", "pwd")
    print("Criados:", u1.user_id, u2.user_id)

    print("\n=== Test: registro duplicado (esperado: erro) ===")
    try:
        ms.register_user("Alice2", "alice@example.com", "pwd")
        print("FALHA: duplicação permitida")
    except Exception as e:
        print("OK (erro esperado):", e)

    print("\n=== Test: login e criação de grupo com membro inválido ===")
    ms.login(u1.email, "pwd")
    try:
        ms.create_group("GInv", [999])
        print("FALHA: grupo criado com membro inexistente")
    except Exception as e:
        print("OK (erro esperado):", e)

    print("\n=== Test: criar grupo válido ===")
    grp = ms.create_group("GrupoTest", [u2.user_id])
    print("Grupo criado:", grp.group_id, grp.membros)

    print("\n=== Test: despesas custom (soma diferente) ===")
    try:
        ms.create_custom_expense(grp.group_id, "Custo", u1.user_id, 100.0, {u1.user_id: 30.0, u2.user_id: 60.0})
        print("FALHA: aceita soma diferente do total")
    except Exception as e:
        print("OK (erro esperado):", e)

    print("\n=== Test: itemized com alocação inconsistente ===")
    item = mindfree_pro.ExpenseItem(nome="X", valor=50.0, categoria="Outros", allocations=[mindfree_pro.ItemAllocation(user_id=u1.user_id, amount=30.0), mindfree_pro.ItemAllocation(user_id=u2.user_id, amount=10.0)])
    try:
        ms.create_itemized_expense(grp.group_id, "Compra", u1.user_id, [item])
        print("FALHA: aceitou alocações que não somam o valor do item")
    except Exception as e:
        print("OK (erro esperado):", e)

    print("\n=== Test: registrar pagamento e listar ===")
    p = ms.register_payment(grp.group_id, from_user=u2.user_id, to_user=u1.user_id, valor=20.0)
    payments = ms.list_group_payments(grp.group_id)
    print("Pagamentos listados:", len(payments), "(esperado >=1)")

    print("\n=== Test: exportar relatórios ===")
    txt_path = ms.export_group_summary_txt(grp.group_id)
    csv_path = ms.export_group_expenses_csv(grp.group_id)
    print("TXT gerado:", txt_path, "exists:", Path(txt_path).exists())
    print("CSV gerado:", csv_path, "exists:", Path(csv_path).exists())

    # cleanup temporário
    try:
        Path(TEST_DATA).unlink()
    except Exception:
        pass


if __name__ == "__main__":
    run_tests()
