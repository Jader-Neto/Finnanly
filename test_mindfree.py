from mindfree_pro import MindfreeSystem

def run_smoke():
    ms = MindfreeSystem()
    # garantir estado limpo em memória (não apagar arquivo)
    try:
        user = ms.register_user("Tester", "test@example.com", "pass123")
    except Exception:
        # usuário pode já existir no arquivo de dados
        user = ms.find_user_by_email("test@example.com")

    print("User:", user.user_id, user.nome, user.email)

    # login
    ok = ms.login(user.email, "pass123")
    print("Login ok:", ok)

    # criar grupo
    try:
        group = ms.create_group("Grupo Teste", [])
    except Exception:
        # se já existir, pega primeiro grupo do usuário
        groups = ms.list_groups(only_mine=True)
        group = groups[0] if groups else None

    print("Group:", group.group_id, group.nome)

    # registrar despesa igualitária
    try:
        exp = ms.create_equal_expense(group.group_id, "Compra teste", user.user_id, 100.0, participants=group.membros)
        print("Expense:", exp.expense_id, exp.total)
    except Exception as e:
        print("Expense error:", e)

    balances = ms.calculate_group_balances(group.group_id)
    print("Balances:", balances)

if __name__ == '__main__':
    run_smoke()
