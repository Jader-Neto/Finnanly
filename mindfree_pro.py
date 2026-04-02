#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

DATA_FILE = "mindfree_data.json"

# ============================================================
# Utilidades visuais
# ============================================================

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"

def color(text: str, fg: str) -> str:
    return f"{fg}{text}{C.RESET}"

def banner(title: str):
    line = "=" * 72
    print(color(line, C.CYAN))
    print(color(title.center(72), C.BOLD + C.CYAN))
    print(color(line, C.CYAN))

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input(color("\nPressione Enter para continuar...", C.DIM))

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def file_safe_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def ask_nonempty(msg: str) -> str:
    while True:
        v = input(msg).strip()
        if v:
            return v
        print(color("Campo obrigatório.", C.RED))

def ask_int(msg: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    while True:
        try:
            v = int(input(msg))
            if min_value is not None and v < min_value:
                print(color(f"Valor deve ser >= {min_value}.", C.RED))
                continue
            if max_value is not None and v > max_value:
                print(color(f"Valor deve ser <= {max_value}.", C.RED))
                continue
            return v
        except ValueError:
            print(color("Digite um número inteiro válido.", C.RED))

def ask_float(msg: str, min_value: Optional[float] = None) -> float:
    while True:
        try:
            v = float(input(msg).strip().replace(",", "."))
            if min_value is not None and v < min_value:
                print(color(f"Valor deve ser >= {min_value}.", C.RED))
                continue
            return v
        except ValueError:
            print(color("Digite um número válido.", C.RED))

def draw_table(headers: List[str], rows: List[List[str]]):
    if not rows:
        print(color("Nenhum dado para exibir.", C.YELLOW))
        return

    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def sep():
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    print(color(sep(), C.CYAN))
    print(color("| " + " | ".join(str(headers[i]).ljust(widths[i]) for i in range(len(headers))) + " |", C.BOLD + C.WHITE))
    print(color(sep(), C.CYAN))
    for row in rows:
        print("| " + " | ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))) + " |")
    print(color(sep(), C.CYAN))

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def ensure_reports_dir() -> str:
    path = os.path.join(os.getcwd(), "exports")
    os.makedirs(path, exist_ok=True)
    return path

# ============================================================
# Modelos
# ============================================================

@dataclass
class User:
    user_id: int
    nome: str
    email: str
    password_hash: str
    pix: str = ""
    ativo: bool = True
    created_at: str = field(default_factory=now_str)

@dataclass
class ItemAllocation:
    user_id: int
    amount: float

@dataclass
class ExpenseItem:
    nome: str
    valor: float
    categoria: str
    allocations: List[ItemAllocation] = field(default_factory=list)

@dataclass
class Expense:
    expense_id: int
    group_id: int
    descricao: str
    paid_by: int
    total: float
    split_type: str                # equal | custom | itemized
    participants: List[int]
    shares: Dict[int, float] = field(default_factory=dict)
    items: List[ExpenseItem] = field(default_factory=list)
    currency: str = "BRL"
    categoria: str = "Outros"
    created_at: str = field(default_factory=now_str)
    obs: str = ""

@dataclass
class Payment:
    payment_id: int
    group_id: int
    from_user: int
    to_user: int
    valor: float
    created_at: str = field(default_factory=now_str)
    obs: str = ""

@dataclass
class Group:
    group_id: int
    nome: str
    owner_id: int
    membros: List[int] = field(default_factory=list)
    created_at: str = field(default_factory=now_str)

# ============================================================
# Core
# ============================================================

class MindfreeSystem:
    DEFAULT_CATEGORIES = [
        "Alimentação",
        "Transporte",
        "Moradia",
        "Viagem",
        "Lazer",
        "Saúde",
        "Educação",
        "Mercado",
        "Contas",
        "Outros",
    ]

    def __init__(self):
        self.users: Dict[int, User] = {}
        self.groups: Dict[int, Group] = {}
        self.expenses: Dict[int, Expense] = {}
        self.payments: Dict[int, Payment] = {}
        self.categories: List[str] = list(self.DEFAULT_CATEGORIES)

        self.next_user_id = 1
        self.next_group_id = 1
        self.next_expense_id = 1
        self.next_payment_id = 1

        self.current_user_id: Optional[int] = None
        self.load()

    # ---------------- Persistência ----------------
    def save(self):
        data = {
            "users": [asdict(u) for u in self.users.values()],
            "groups": [asdict(g) for g in self.groups.values()],
            "expenses": [asdict(e) for e in self.expenses.values()],
            "payments": [asdict(p) for p in self.payments.values()],
            "categories": self.categories,
            "counters": {
                "next_user_id": self.next_user_id,
                "next_group_id": self.next_group_id,
                "next_expense_id": self.next_expense_id,
                "next_payment_id": self.next_payment_id,
            },
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        if not os.path.exists(DATA_FILE):
            return

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.users = {u["user_id"]: User(**u) for u in data.get("users", [])}
        self.groups = {g["group_id"]: Group(**g) for g in data.get("groups", [])}

        self.expenses = {}
        for e in data.get("expenses", []):
            items = []
            for item in e.get("items", []):
                allocations = [ItemAllocation(**a) for a in item.get("allocations", [])]
                items.append(
                    ExpenseItem(
                        nome=item["nome"],
                        valor=item["valor"],
                        categoria=item.get("categoria", "Outros"),
                        allocations=allocations,
                    )
                )
            exp = Expense(
                expense_id=e["expense_id"],
                group_id=e["group_id"],
                descricao=e["descricao"],
                paid_by=e["paid_by"],
                total=e["total"],
                split_type=e["split_type"],
                participants=e["participants"],
                shares={int(k): float(v) for k, v in e.get("shares", {}).items()},
                items=items,
                currency=e.get("currency", "BRL"),
                categoria=e.get("categoria", "Outros"),
                created_at=e.get("created_at", now_str()),
                obs=e.get("obs", ""),
            )
            self.expenses[exp.expense_id] = exp

        self.payments = {p["payment_id"]: Payment(**p) for p in data.get("payments", [])}
        self.categories = data.get("categories", list(self.DEFAULT_CATEGORIES))

        counters = data.get("counters", {})
        self.next_user_id = counters.get("next_user_id", 1)
        self.next_group_id = counters.get("next_group_id", 1)
        self.next_expense_id = counters.get("next_expense_id", 1)
        self.next_payment_id = counters.get("next_payment_id", 1)

    # ---------------- Autenticação ----------------
    def register_user(self, nome: str, email: str, password: str, pix: str = "") -> User:
        if self.find_user_by_email(email):
            raise ValueError("Já existe um usuário com esse e-mail.")
        user = User(
            user_id=self.next_user_id,
            nome=nome,
            email=email.lower().strip(),
            password_hash=hash_password(password),
            pix=pix.strip(),
        )
        self.users[user.user_id] = user
        self.next_user_id += 1
        self.save()
        return user

    def login(self, email: str, password: str) -> bool:
        user = self.find_user_by_email(email)
        if not user:
            return False
        if user.password_hash != hash_password(password):
            return False
        self.current_user_id = user.user_id
        return True

    def logout(self):
        self.current_user_id = None

    def require_login(self):
        if self.current_user_id is None:
            raise ValueError("Faça login para continuar.")

    def current_user(self) -> Optional[User]:
        if self.current_user_id is None:
            return None
        return self.users.get(self.current_user_id)

    def find_user_by_email(self, email: str) -> Optional[User]:
        email = email.lower().strip()
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    # ---------------- Usuários ----------------
    def list_users(self) -> List[User]:
        return list(self.users.values())

    def update_current_user(self, nome: Optional[str] = None, email: Optional[str] = None,
                            pix: Optional[str] = None, password: Optional[str] = None):
        self.require_login()
        user = self.users[self.current_user_id]
        if nome:
            user.nome = nome.strip()
        if email:
            existing = self.find_user_by_email(email)
            if existing and existing.user_id != user.user_id:
                raise ValueError("Este e-mail já está em uso.")
            user.email = email.lower().strip()
        if pix is not None:
            user.pix = pix.strip()
        if password:
            user.password_hash = hash_password(password)
        self.save()

    # ---------------- Categorias ----------------
    def list_categories(self) -> List[str]:
        return sorted(set(self.categories))

    def add_category(self, name: str):
        name = name.strip()
        if not name:
            raise ValueError("Categoria inválida.")
        if name not in self.categories:
            self.categories.append(name)
            self.save()

    # ---------------- Grupos ----------------
    def create_group(self, nome: str, membros: List[int]) -> Group:
        self.require_login()
        if self.current_user_id not in membros:
            membros.append(self.current_user_id)

        membros = list(dict.fromkeys(membros))
        for uid in membros:
            if uid not in self.users:
                raise ValueError(f"Usuário {uid} não existe.")

        group = Group(
            group_id=self.next_group_id,
            nome=nome,
            owner_id=self.current_user_id,
            membros=membros
        )
        self.groups[group.group_id] = group
        self.next_group_id += 1
        self.save()
        return group

    def list_groups(self, only_mine: bool = False) -> List[Group]:
        if not only_mine or self.current_user_id is None:
            return list(self.groups.values())
        return [g for g in self.groups.values() if self.current_user_id in g.membros]

    def add_member_to_group(self, group_id: int, user_id: int):
        group = self._get_group(group_id)
        self._assert_group_access(group)
        if user_id not in self.users:
            raise ValueError("Usuário não encontrado.")
        if user_id in group.membros:
            raise ValueError("Usuário já está no grupo.")
        group.membros.append(user_id)
        self.save()

    # ---------------- Despesas ----------------
    def create_equal_expense(self, group_id: int, descricao: str, paid_by: int, total: float,
                             participants: List[int], categoria: str = "Outros", currency: str = "BRL",
                             obs: str = "") -> Expense:
        group = self._get_group(group_id)
        self._assert_group_access(group)
        self._validate_participants(group, participants, paid_by)
        self.add_category(categoria)

        share = round(total / len(participants), 2)
        shares = {uid: share for uid in participants}
        diff = round(total - sum(shares.values()), 2)
        if diff != 0:
            shares[participants[-1]] = round(shares[participants[-1]] + diff, 2)

        expense = Expense(
            expense_id=self.next_expense_id,
            group_id=group_id,
            descricao=descricao,
            paid_by=paid_by,
            total=round(total, 2),
            split_type="equal",
            participants=participants,
            shares=shares,
            currency=currency,
            categoria=categoria,
            obs=obs,
        )
        self.expenses[expense.expense_id] = expense
        self.next_expense_id += 1
        self.save()
        return expense

    def create_custom_expense(self, group_id: int, descricao: str, paid_by: int, total: float,
                              shares: Dict[int, float], categoria: str = "Outros",
                              currency: str = "BRL", obs: str = "") -> Expense:
        group = self._get_group(group_id)
        self._assert_group_access(group)
        participants = list(shares.keys())
        self._validate_participants(group, participants, paid_by)
        self.add_category(categoria)

        if round(sum(shares.values()), 2) != round(total, 2):
            raise ValueError("A soma das cotas deve ser igual ao valor total.")

        expense = Expense(
            expense_id=self.next_expense_id,
            group_id=group_id,
            descricao=descricao,
            paid_by=paid_by,
            total=round(total, 2),
            split_type="custom",
            participants=participants,
            shares={uid: round(v, 2) for uid, v in shares.items()},
            currency=currency,
            categoria=categoria,
            obs=obs,
        )
        self.expenses[expense.expense_id] = expense
        self.next_expense_id += 1
        self.save()
        return expense

    def create_itemized_expense(self, group_id: int, descricao: str, paid_by: int,
                                items: List[ExpenseItem], categoria: str = "Outros",
                                currency: str = "BRL", obs: str = "") -> Expense:
        group = self._get_group(group_id)
        self._assert_group_access(group)
        self.add_category(categoria)

        if paid_by not in group.membros:
            raise ValueError("Quem pagou precisa estar no grupo.")
        if not items:
            raise ValueError("Informe ao menos um item.")

        total = 0.0
        shares: Dict[int, float] = {}
        participants = set()

        for item in items:
            self.add_category(item.categoria)
            total += item.valor
            alloc_sum = round(sum(a.amount for a in item.allocations), 2)
            if round(item.valor, 2) != alloc_sum:
                raise ValueError(f"No item '{item.nome}', a soma das alocações não bate com o valor do item.")
            for alloc in item.allocations:
                if alloc.user_id not in group.membros:
                    raise ValueError("Participante inválido no item.")
                shares[alloc.user_id] = round(shares.get(alloc.user_id, 0.0) + alloc.amount, 2)
                participants.add(alloc.user_id)

        expense = Expense(
            expense_id=self.next_expense_id,
            group_id=group_id,
            descricao=descricao,
            paid_by=paid_by,
            total=round(total, 2),
            split_type="itemized",
            participants=sorted(list(participants)),
            shares=shares,
            items=items,
            currency=currency,
            categoria=categoria,
            obs=obs,
        )
        self.expenses[expense.expense_id] = expense
        self.next_expense_id += 1
        self.save()
        return expense

    def list_group_expenses(self, group_id: int) -> List[Expense]:
        group = self._get_group(group_id)
        self._assert_group_access(group)
        return [e for e in self.expenses.values() if e.group_id == group_id]

    # ---------------- Pagamentos ----------------
    def register_payment(self, group_id: int, from_user: int, to_user: int, valor: float, obs: str = "") -> Payment:
        group = self._get_group(group_id)
        self._assert_group_access(group)
        if from_user not in group.membros or to_user not in group.membros:
            raise ValueError("Os usuários precisam pertencer ao grupo.")
        if from_user == to_user:
            raise ValueError("Pagamento inválido.")
        payment = Payment(
            payment_id=self.next_payment_id,
            group_id=group_id,
            from_user=from_user,
            to_user=to_user,
            valor=round(valor, 2),
            obs=obs,
        )
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1
        self.save()
        return payment

    def list_group_payments(self, group_id: int) -> List[Payment]:
        group = self._get_group(group_id)
        self._assert_group_access(group)
        return [p for p in self.payments.values() if p.group_id == group_id]

    # ---------------- Cálculos ----------------
    def calculate_group_balances(self, group_id: int) -> Dict[int, float]:
        group = self._get_group(group_id)
        self._assert_group_access(group)
        balances = {uid: 0.0 for uid in group.membros}

        for e in self.list_group_expenses(group_id):
            for uid, share in e.shares.items():
                balances[uid] = round(balances.get(uid, 0.0) - share, 2)
            balances[e.paid_by] = round(balances.get(e.paid_by, 0.0) + e.total, 2)

        for p in self.list_group_payments(group_id):
            balances[p.from_user] = round(balances.get(p.from_user, 0.0) + p.valor, 2)
            balances[p.to_user] = round(balances.get(p.to_user, 0.0) - p.valor, 2)

        for uid in list(balances.keys()):
            if abs(balances[uid]) < 0.01:
                balances[uid] = 0.0
        return balances

    def simplify_group_debts(self, group_id: int) -> List[Tuple[int, int, float]]:
        balances = self.calculate_group_balances(group_id)
        creditors = []
        debtors = []

        for uid, bal in balances.items():
            if bal > 0:
                creditors.append([uid, round(bal, 2)])
            elif bal < 0:
                debtors.append([uid, round(-bal, 2)])

        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        i = j = 0
        settlements = []

        while i < len(debtors) and j < len(creditors):
            debtor_id, debt = debtors[i]
            creditor_id, credit = creditors[j]
            amount = round(min(debt, credit), 2)
            if amount > 0:
                settlements.append((debtor_id, creditor_id, amount))
            debtors[i][1] = round(debtors[i][1] - amount, 2)
            creditors[j][1] = round(creditors[j][1] - amount, 2)

            if debtors[i][1] <= 0.009:
                i += 1
            if creditors[j][1] <= 0.009:
                j += 1

        return settlements

    def totals_by_category(self, group_id: int) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for e in self.list_group_expenses(group_id):
            result[e.categoria] = round(result.get(e.categoria, 0.0) + e.total, 2)
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def ranking_paid_by_user(self, group_id: int) -> List[Tuple[int, float]]:
        ranking: Dict[int, float] = {}
        for e in self.list_group_expenses(group_id):
            ranking[e.paid_by] = round(ranking.get(e.paid_by, 0.0) + e.total, 2)
        return sorted(ranking.items(), key=lambda x: x[1], reverse=True)

    # ---------------- Exportação ----------------
    def export_group_summary_txt(self, group_id: int) -> str:
        group = self._get_group(group_id)
        self._assert_group_access(group)

        exports_dir = ensure_reports_dir()
        path = os.path.join(exports_dir, f"grupo_{group_id}_resumo_{file_safe_timestamp()}.txt")

        balances = self.calculate_group_balances(group_id)
        settlements = self.simplify_group_debts(group_id)
        totals_cat = self.totals_by_category(group_id)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Relatório do Grupo: {group.nome}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Gerado em: {now_str()}\n\n")
            f.write("Membros:\n")
            for uid in group.membros:
                f.write(f"- {self.users[uid].nome} ({self.users[uid].email})\n")

            f.write("\nDespesas:\n")
            for e in self.list_group_expenses(group_id):
                f.write(f"- ID {e.expense_id} | {e.descricao} | {e.categoria} | {e.currency} {e.total:.2f} | Pago por {self.users[e.paid_by].nome}\n")

            f.write("\nPagamentos:\n")
            for p in self.list_group_payments(group_id):
                f.write(f"- ID {p.payment_id} | {self.users[p.from_user].nome} -> {self.users[p.to_user].nome} | R$ {p.valor:.2f}\n")

            f.write("\nSaldos:\n")
            for uid, bal in balances.items():
                f.write(f"- {self.users[uid].nome}: R$ {bal:.2f}\n")

            f.write("\nTotais por categoria:\n")
            for cat, total in totals_cat.items():
                f.write(f"- {cat}: R$ {total:.2f}\n")

            f.write("\nLiquidação sugerida:\n")
            if not settlements:
                f.write("- Nada a liquidar.\n")
            else:
                for debtor, creditor, amount in settlements:
                    f.write(f"- {self.users[debtor].nome} paga R$ {amount:.2f} para {self.users[creditor].nome}\n")

        return path

    def export_group_expenses_csv(self, group_id: int) -> str:
        group = self._get_group(group_id)
        self._assert_group_access(group)

        exports_dir = ensure_reports_dir()
        path = os.path.join(exports_dir, f"grupo_{group_id}_despesas_{file_safe_timestamp()}.csv")

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["expense_id", "descricao", "categoria", "split_type", "paid_by", "total", "currency", "created_at", "obs"])
            for e in self.list_group_expenses(group_id):
                writer.writerow([
                    e.expense_id,
                    e.descricao,
                    e.categoria,
                    e.split_type,
                    self.users[e.paid_by].nome,
                    f"{e.total:.2f}",
                    e.currency,
                    e.created_at,
                    e.obs
                ])
        return path

    # ---------------- Auxiliares ----------------
    def _get_group(self, group_id: int) -> Group:
        if group_id not in self.groups:
            raise ValueError("Grupo não encontrado.")
        return self.groups[group_id]

    def _assert_group_access(self, group: Group):
        self.require_login()
        if self.current_user_id not in group.membros:
            raise ValueError("Você não tem acesso a esse grupo.")

    def _validate_participants(self, group: Group, participants: List[int], paid_by: int):
        if not participants:
            raise ValueError("Informe participantes.")
        if paid_by not in group.membros:
            raise ValueError("Quem pagou deve pertencer ao grupo.")
        for uid in participants:
            if uid not in group.membros:
                raise ValueError("Participante inválido.")

# ============================================================
# Interface CLI
# ============================================================

class MindfreeCLI:
    def __init__(self):
        self.app = MindfreeSystem()

    # ---------------- Entrada principal ----------------
    def run(self):
        while True:
            if self.app.current_user_id is None:
                self.auth_menu()
            else:
                self.main_menu()

    # ---------------- Autenticação ----------------
    def auth_menu(self):
        clear()
        banner("MINDFREE TERMINAL PRO")
        print(color("1. Login", C.GREEN))
        print(color("2. Cadastrar conta", C.GREEN))
        print(color("0. Sair", C.YELLOW))
        op = ask_int("\nEscolha: ", 0, 2)

        if op == 1:
            self.login_screen()
        elif op == 2:
            self.register_screen()
        else:
            print(color("Até logo.", C.CYAN))
            raise SystemExit

    def login_screen(self):
        clear()
        banner("LOGIN")
        email = ask_nonempty("E-mail: ")
        password = ask_nonempty("Senha: ")
        if self.app.login(email, password):
            print(color("\nLogin realizado com sucesso.", C.GREEN))
        else:
            print(color("\nE-mail ou senha inválidos.", C.RED))
        pause()

    def register_screen(self):
        clear()
        banner("CADASTRO")
        nome = ask_nonempty("Nome: ")
        email = ask_nonempty("E-mail: ")
        password = ask_nonempty("Senha: ")
        pix = input("Chave Pix (opcional): ").strip()
        try:
            user = self.app.register_user(nome, email, password, pix)
            print(color(f"\nUsuário criado com sucesso. ID {user.user_id}", C.GREEN))
        except Exception as e:
            print(color(f"\nErro: {e}", C.RED))
        pause()

    # ---------------- Menu principal ----------------
    def main_menu(self):
        clear()
        user = self.app.current_user()
        banner(f"MINDFREE - Usuário: {user.nome}")
        print(color("1. Meu perfil", C.GREEN))
        print(color("2. Usuários", C.GREEN))
        print(color("3. Grupos", C.GREEN))
        print(color("4. Categorias", C.GREEN))
        print(color("5. Despesas", C.GREEN))
        print(color("6. Pagamentos", C.GREEN))
        print(color("7. Relatórios", C.GREEN))
        print(color("8. Logout", C.YELLOW))
        print(color("0. Sair", C.YELLOW))
        op = ask_int("\nEscolha: ", 0, 8)

        if op == 1:
            self.profile_menu()
        elif op == 2:
            self.users_menu()
        elif op == 3:
            self.groups_menu()
        elif op == 4:
            self.categories_menu()
        elif op == 5:
            self.expenses_menu()
        elif op == 6:
            self.payments_menu()
        elif op == 7:
            self.reports_menu()
        elif op == 8:
            self.app.logout()
        else:
            raise SystemExit

    # ---------------- Perfil ----------------
    def profile_menu(self):
        while True:
            clear()
            user = self.app.current_user()
            banner("MEU PERFIL")
            draw_table(
                ["Campo", "Valor"],
                [
                    ["ID", user.user_id],
                    ["Nome", user.nome],
                    ["E-mail", user.email],
                    ["Pix", user.pix or "-"],
                    ["Criado em", user.created_at],
                ]
            )
            print(color("1. Editar perfil", C.GREEN))
            print(color("2. Alterar senha", C.GREEN))
            print(color("0. Voltar", C.YELLOW))
            op = ask_int("\nEscolha: ", 0, 2)

            try:
                if op == 1:
                    nome = input("Novo nome (Enter mantém): ").strip() or None
                    email = input("Novo e-mail (Enter mantém): ").strip() or None
                    pix_input = input("Nova chave Pix (Enter mantém): ")
                    pix = None if pix_input == "" else pix_input
                    self.app.update_current_user(nome=nome, email=email, pix=pix)
                    print(color("Perfil atualizado.", C.GREEN))
                    pause()
                elif op == 2:
                    new_password = ask_nonempty("Nova senha: ")
                    self.app.update_current_user(password=new_password)
                    print(color("Senha alterada com sucesso.", C.GREEN))
                    pause()
                else:
                    return
            except Exception as e:
                print(color(f"Erro: {e}", C.RED))
                pause()

    # ---------------- Usuários ----------------
    def users_menu(self):
        clear()
        banner("USUÁRIOS")
        rows = [[u.user_id, u.nome, u.email, u.pix or "-"] for u in self.app.list_users()]
        draw_table(["ID", "Nome", "E-mail", "Pix"], rows)
        pause()

    # ---------------- Grupos ----------------
    def groups_menu(self):
        while True:
            clear()
            banner("GRUPOS")
            print(color("1. Criar grupo", C.GREEN))
            print(color("2. Listar meus grupos", C.GREEN))
            print(color("3. Adicionar membro a um grupo", C.GREEN))
            print(color("0. Voltar", C.YELLOW))
            op = ask_int("\nEscolha: ", 0, 3)

            try:
                if op == 1:
                    self.create_group_screen()
                elif op == 2:
                    self.list_groups_screen()
                elif op == 3:
                    self.add_member_screen()
                else:
                    return
            except Exception as e:
                print(color(f"Erro: {e}", C.RED))
                pause()

    def create_group_screen(self):
        clear()
        banner("CRIAR GRUPO")
        nome = ask_nonempty("Nome do grupo: ")
        self.show_users()
        qtd = ask_int("Quantos membros adicionais deseja informar? ", 0)
        membros = []
        for i in range(qtd):
            uid = ask_int(f"ID do membro {i+1}: ", 1)
            membros.append(uid)
        group = self.app.create_group(nome, membros)
        print(color(f"Grupo criado com sucesso. ID {group.group_id}", C.GREEN))
        pause()

    def list_groups_screen(self):
        clear()
        banner("MEUS GRUPOS")
        groups = self.app.list_groups(only_mine=True)
        rows = []
        for g in groups:
            membros = ", ".join(self.app.users[uid].nome for uid in g.membros)
            rows.append([g.group_id, g.nome, self.app.users[g.owner_id].nome, membros])
        draw_table(["ID", "Nome", "Dono", "Membros"], rows)
        pause()

    def add_member_screen(self):
        clear()
        banner("ADICIONAR MEMBRO")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        self.show_users()
        uid = ask_int("ID do usuário a adicionar: ", 1)
        self.app.add_member_to_group(gid, uid)
        print(color("Membro adicionado com sucesso.", C.GREEN))
        pause()

    # ---------------- Categorias ----------------
    def categories_menu(self):
        while True:
            clear()
            banner("CATEGORIAS")
            rows = [[i + 1, cat] for i, cat in enumerate(self.app.list_categories())]
            draw_table(["#", "Categoria"], rows)
            print(color("1. Adicionar nova categoria", C.GREEN))
            print(color("0. Voltar", C.YELLOW))
            op = ask_int("\nEscolha: ", 0, 1)
            if op == 1:
                cat = ask_nonempty("Nome da categoria: ")
                try:
                    self.app.add_category(cat)
                    print(color("Categoria adicionada.", C.GREEN))
                except Exception as e:
                    print(color(f"Erro: {e}", C.RED))
                pause()
            else:
                return

    # ---------------- Despesas ----------------
    def expenses_menu(self):
        while True:
            clear()
            banner("DESPESAS")
            print(color("1. Registrar despesa igualitária", C.GREEN))
            print(color("2. Registrar despesa personalizada", C.GREEN))
            print(color("3. Registrar despesa por item", C.GREEN))
            print(color("4. Listar despesas de um grupo", C.GREEN))
            print(color("0. Voltar", C.YELLOW))
            op = ask_int("\nEscolha: ", 0, 4)

            try:
                if op == 1:
                    self.register_equal_expense()
                elif op == 2:
                    self.register_custom_expense()
                elif op == 3:
                    self.register_itemized_expense()
                elif op == 4:
                    self.list_expenses_screen()
                else:
                    return
            except Exception as e:
                print(color(f"Erro: {e}", C.RED))
                pause()

    def register_equal_expense(self):
        gid, payer = self.choose_group_and_payer()
        group = self.app.groups[gid]
        descricao = ask_nonempty("Descrição: ")
        total = ask_float("Valor total: R$ ", 0.01)
        categoria = self.choose_category()
        currency = input("Moeda [BRL]: ").strip().upper() or "BRL"
        obs = input("Observação: ").strip()

        print(color("\nParticipantes do grupo:", C.CYAN))
        for uid in group.membros:
            print(f"- {uid}: {self.app.users[uid].nome}")

        everyone = input("Todos participam? (s/n): ").strip().lower()
        if everyone == "s":
            participants = list(group.membros)
        else:
            qtd = ask_int("Quantos participantes? ", 1)
            participants = [ask_int(f"ID do participante {i+1}: ", 1) for i in range(qtd)]

        expense = self.app.create_equal_expense(gid, descricao, payer, total, participants, categoria, currency, obs)
        print(color(f"Despesa registrada. ID {expense.expense_id}", C.GREEN))
        pause()

    def register_custom_expense(self):
        gid, payer = self.choose_group_and_payer()
        group = self.app.groups[gid]
        descricao = ask_nonempty("Descrição: ")
        total = ask_float("Valor total: R$ ", 0.01)
        categoria = self.choose_category()
        currency = input("Moeda [BRL]: ").strip().upper() or "BRL"
        obs = input("Observação: ").strip()

        print(color("\nMembros do grupo:", C.CYAN))
        for uid in group.membros:
            print(f"- {uid}: {self.app.users[uid].nome}")

        qtd = ask_int("Quantos participantes nesta despesa? ", 1)
        shares = {}
        for i in range(qtd):
            uid = ask_int(f"ID do participante {i+1}: ", 1)
            shares[uid] = ask_float(f"Valor da parte de {self.app.users[uid].nome}: R$ ", 0.0)

        expense = self.app.create_custom_expense(gid, descricao, payer, total, shares, categoria, currency, obs)
        print(color(f"Despesa registrada. ID {expense.expense_id}", C.GREEN))
        pause()

    def register_itemized_expense(self):
        gid, payer = self.choose_group_and_payer()
        group = self.app.groups[gid]
        descricao = ask_nonempty("Descrição da compra: ")
        categoria = self.choose_category()
        currency = input("Moeda [BRL]: ").strip().upper() or "BRL"
        obs = input("Observação: ").strip()

        total_items = ask_int("Quantidade de itens: ", 1)
        items = []

        print(color("\nMembros do grupo:", C.CYAN))
        for uid in group.membros:
            print(f"- {uid}: {self.app.users[uid].nome}")

        for i in range(total_items):
            print(color(f"\nItem {i+1}", C.BOLD + C.MAGENTA))
            nome = ask_nonempty("Nome do item: ")
            valor = ask_float("Valor do item: R$ ", 0.01)
            item_cat = self.choose_category(prompt="Categoria do item")
            mode = input("Dividir igualmente neste item? (s/n): ").strip().lower()
            allocations = []

            if mode == "s":
                qtd = ask_int("Quantos participantes neste item? ", 1)
                selected = [ask_int(f"ID do participante {j+1}: ", 1) for j in range(qtd)]
                each = round(valor / len(selected), 2)
                allocated = 0.0
                for uid in selected:
                    allocations.append(ItemAllocation(uid, each))
                    allocated += each
                diff = round(valor - allocated, 2)
                if diff != 0:
                    allocations[-1].amount = round(allocations[-1].amount + diff, 2)
            else:
                qtd = ask_int("Quantos participantes neste item? ", 1)
                total_alloc = 0.0
                for j in range(qtd):
                    uid = ask_int(f"ID do participante {j+1}: ", 1)
                    amount = ask_float(f"Parte de {self.app.users[uid].nome}: R$ ", 0.0)
                    allocations.append(ItemAllocation(uid, amount))
                    total_alloc += amount
                if round(total_alloc, 2) != round(valor, 2):
                    raise ValueError("A soma das alocações do item precisa bater com o valor do item.")

            items.append(ExpenseItem(nome=nome, valor=valor, categoria=item_cat, allocations=allocations))

        expense = self.app.create_itemized_expense(gid, descricao, payer, items, categoria, currency, obs)
        print(color(f"Despesa por item registrada. ID {expense.expense_id} | Total {expense.total:.2f}", C.GREEN))
        pause()

    def list_expenses_screen(self):
        clear()
        banner("LISTAR DESPESAS")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        expenses = self.app.list_group_expenses(gid)

        rows = []
        for e in expenses:
            rows.append([
                e.expense_id,
                e.descricao,
                e.categoria,
                e.split_type,
                self.app.users[e.paid_by].nome,
                f"{e.currency} {e.total:.2f}",
                e.created_at
            ])
        draw_table(["ID", "Descrição", "Categoria", "Tipo", "Pago por", "Total", "Data"], rows)

        if expenses:
            detail = input("\nDeseja ver detalhes de uma despesa? (s/n): ").strip().lower()
            if detail == "s":
                eid = ask_int("ID da despesa: ", 1)
                found = None
                for e in expenses:
                    if e.expense_id == eid:
                        found = e
                        break
                if not found:
                    print(color("Despesa não encontrada.", C.RED))
                else:
                    print(color("\nDetalhes da despesa", C.BOLD + C.CYAN))
                    print(f"Descrição: {found.descricao}")
                    print(f"Categoria: {found.categoria}")
                    print(f"Tipo: {found.split_type}")
                    print(f"Pago por: {self.app.users[found.paid_by].nome}")
                    print(f"Total: {found.currency} {found.total:.2f}")
                    print(f"Obs: {found.obs or '-'}")
                    share_rows = [[self.app.users[uid].nome, f"{found.currency} {val:.2f}"] for uid, val in found.shares.items()]
                    draw_table(["Participante", "Cota"], share_rows)
                    if found.items:
                        item_rows = []
                        for item in found.items:
                            item_rows.append([item.nome, item.categoria, f"{found.currency} {item.valor:.2f}"])
                        draw_table(["Item", "Categoria", "Valor"], item_rows)
        pause()

    # ---------------- Pagamentos ----------------
    def payments_menu(self):
        while True:
            clear()
            banner("PAGAMENTOS")
            print(color("1. Registrar pagamento", C.GREEN))
            print(color("2. Listar pagamentos de um grupo", C.GREEN))
            print(color("3. Ver liquidação sugerida", C.GREEN))
            print(color("0. Voltar", C.YELLOW))
            op = ask_int("\nEscolha: ", 0, 3)

            try:
                if op == 1:
                    self.register_payment_screen()
                elif op == 2:
                    self.list_payments_screen()
                elif op == 3:
                    self.show_settlement_screen()
                else:
                    return
            except Exception as e:
                print(color(f"Erro: {e}", C.RED))
                pause()

    def register_payment_screen(self):
        clear()
        banner("REGISTRAR PAGAMENTO")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        group = self.app.groups[gid]
        for uid in group.membros:
            print(f"- {uid}: {self.app.users[uid].nome}")
        from_user = ask_int("ID do devedor: ", 1)
        to_user = ask_int("ID do credor: ", 1)
        valor = ask_float("Valor pago: R$ ", 0.01)
        obs = input("Observação: ").strip()
        p = self.app.register_payment(gid, from_user, to_user, valor, obs)
        print(color(f"Pagamento registrado. ID {p.payment_id}", C.GREEN))
        pause()

    def list_payments_screen(self):
        clear()
        banner("PAGAMENTOS DO GRUPO")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        rows = []
        for p in self.app.list_group_payments(gid):
            rows.append([
                p.payment_id,
                self.app.users[p.from_user].nome,
                self.app.users[p.to_user].nome,
                f"R$ {p.valor:.2f}",
                p.created_at,
                p.obs or "-"
            ])
        draw_table(["ID", "Devedor", "Credor", "Valor", "Data", "Obs"], rows)
        pause()

    def show_settlement_screen(self):
        clear()
        banner("LIQUIDAÇÃO SUGERIDA")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        settlements = self.app.simplify_group_debts(gid)
        rows = []
        for debtor, creditor, amount in settlements:
            rows.append([
                self.app.users[debtor].nome,
                self.app.users[creditor].nome,
                f"R$ {amount:.2f}",
                self.app.users[creditor].pix or "-"
            ])
        draw_table(["Devedor", "Credor", "Valor", "Pix do credor"], rows)
        pause()

    # ---------------- Relatórios ----------------
    def reports_menu(self):
        while True:
            clear()
            banner("RELATÓRIOS")
            print(color("1. Resumo financeiro do grupo", C.GREEN))
            print(color("2. Totais por categoria", C.GREEN))
            print(color("3. Ranking de quem mais pagou", C.GREEN))
            print(color("4. Exportar resumo em TXT", C.GREEN))
            print(color("5. Exportar despesas em CSV", C.GREEN))
            print(color("0. Voltar", C.YELLOW))
            op = ask_int("\nEscolha: ", 0, 5)

            try:
                if op == 1:
                    self.group_summary_screen()
                elif op == 2:
                    self.category_totals_screen()
                elif op == 3:
                    self.ranking_screen()
                elif op == 4:
                    self.export_txt_screen()
                elif op == 5:
                    self.export_csv_screen()
                else:
                    return
            except Exception as e:
                print(color(f"Erro: {e}", C.RED))
                pause()

    def group_summary_screen(self):
        clear()
        banner("RESUMO FINANCEIRO")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)

        balances = self.app.calculate_group_balances(gid)
        rows = []
        for uid, bal in balances.items():
            status = "a receber" if bal > 0 else ("devendo" if bal < 0 else "quitado")
            rows.append([self.app.users[uid].nome, f"R$ {bal:.2f}", status])
        draw_table(["Membro", "Saldo", "Status"], rows)
        pause()

    def category_totals_screen(self):
        clear()
        banner("TOTAIS POR CATEGORIA")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        totals = self.app.totals_by_category(gid)
        rows = [[cat, f"R$ {val:.2f}"] for cat, val in totals.items()]
        draw_table(["Categoria", "Total"], rows)
        pause()

    def ranking_screen(self):
        clear()
        banner("RANKING DE QUEM MAIS PAGOU")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        ranking = self.app.ranking_paid_by_user(gid)
        rows = [[i + 1, self.app.users[uid].nome, f"R$ {total:.2f}"] for i, (uid, total) in enumerate(ranking)]
        draw_table(["Posição", "Usuário", "Total pago"], rows)
        pause()

    def export_txt_screen(self):
        clear()
        banner("EXPORTAR RESUMO TXT")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        path = self.app.export_group_summary_txt(gid)
        print(color(f"Arquivo gerado com sucesso:\n{path}", C.GREEN))
        pause()

    def export_csv_screen(self):
        clear()
        banner("EXPORTAR CSV")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        path = self.app.export_group_expenses_csv(gid)
        print(color(f"Arquivo gerado com sucesso:\n{path}", C.GREEN))
        pause()

    # ---------------- Helpers visuais ----------------
    def choose_group_and_payer(self) -> Tuple[int, int]:
        clear()
        banner("SELECIONAR GRUPO")
        self.show_groups()
        gid = ask_int("ID do grupo: ", 1)
        group = self.app.groups[gid]
        print(color("\nMembros do grupo:", C.CYAN))
        for uid in group.membros:
            print(f"- {uid}: {self.app.users[uid].nome}")
        payer = ask_int("ID de quem pagou: ", 1)
        return gid, payer

    def choose_category(self, prompt: str = "Categoria") -> str:
        cats = self.app.list_categories()
        print(color(f"\n{prompt}:", C.CYAN))
        for i, cat in enumerate(cats, start=1):
            print(f"{i}. {cat}")
        print("0. Criar nova categoria")
        op = ask_int("Escolha: ", 0, len(cats))
        if op == 0:
            new_cat = ask_nonempty("Nova categoria: ")
            self.app.add_category(new_cat)
            return new_cat
        return cats[op - 1]

    def show_users(self):
        rows = [[u.user_id, u.nome, u.email] for u in self.app.list_users()]
        draw_table(["ID", "Nome", "E-mail"], rows)

    def show_groups(self):
        groups = self.app.list_groups(only_mine=True)
        rows = []
        for g in groups:
            rows.append([g.group_id, g.nome, ", ".join(self.app.users[uid].nome for uid in g.membros)])
        draw_table(["ID", "Grupo", "Membros"], rows)

def main():
    cli = MindfreeCLI()
    cli.run()

if __name__ == "__main__":
    main()
