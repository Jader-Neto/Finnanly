# Mindfree Terminal Pro


## Recursos incluídos

- Login e autenticação simples com senha em hash SHA-256
- Cadastro e edição de perfil
- Cadastro de usuários
- Grupos com controle de acesso por membro
- Categorias de gastos personalizáveis
- Despesas:
  - igualitárias
  - personalizadas
  - por item
- Registro de pagamentos
- Cálculo de saldos
- Simplificação de dívidas
- Relatórios no terminal com cores e tabelas
- Exportação de relatório:
  - `.txt` com resumo completo do grupo
  - `.csv` com lista de despesas
- Persistência em `mindfree_data.json`

## Como executar

```bash
python mindfree_pro.py
```

No Windows também pode usar:

```bash
py mindfree_pro.py
```

## Observações

- O sistema usa apenas bibliotecas padrão do Python
- Os relatórios exportados ficam na pasta `exports/`
- As cores do terminal usam ANSI; em terminais muito antigos pode haver limitação visual
