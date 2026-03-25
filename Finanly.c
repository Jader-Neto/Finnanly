#include <stdio.h>
#include <string.h>

#define MAX_USERS 10
#define MAX_GROUPS 5

typedef struct {
    char nome[50];
    float saldo;
} Usuario;

typedef struct {
    char nome[50];
    Usuario *usuarios[MAX_USERS];
    int totalUsuarios;
} Grupo;

Usuario usuarios[MAX_USERS];
Grupo grupos[MAX_GROUPS];

int totalUsuarios = 0;
int totalGrupos = 0;

void cadastrarUsuario() {
    if (totalUsuarios >= MAX_USERS) {
        printf("Limite de usuarios atingido.\n");
        return;
    }

    printf("Nome do usuario: ");
    scanf(" %[^\n]", usuarios[totalUsuarios].nome);
    usuarios[totalUsuarios].saldo = 0;

    totalUsuarios++;
    printf("Usuario cadastrado com sucesso!\n");
}

void criarGrupo() {
    if (totalGrupos >= MAX_GROUPS) {
        printf("Limite de grupos atingido.\n");
        return;
    }

    printf("Nome do grupo: ");
    scanf(" %[^\n]", grupos[totalGrupos].nome);

    grupos[totalGrupos].totalUsuarios = 0;

    int n;
    printf("Quantos usuarios no grupo? ");
    scanf("%d", &n);

    for (int i = 0; i < n; i++) {
        int idx;
        printf("Indice do usuario %d: ", i);
        scanf("%d", &idx);

        if (idx >= 0 && idx < totalUsuarios) {
            grupos[totalGrupos].usuarios[grupos[totalGrupos].totalUsuarios++] = &usuarios[idx];
        }
    }

    totalGrupos++;
    printf("Grupo criado!\n");
}

void adicionarDespesa() {
    int g;
    printf("Indice do grupo: ");
    scanf("%d", &g);

    if (g < 0 || g >= totalGrupos) return;

    float valor;
    int pagador;

    printf("Valor total da despesa: ");
    scanf("%f", &valor);

    printf("Indice de quem pagou: ");
    scanf("%d", &pagador);

    Grupo *grupo = &grupos[g];
    float dividido = valor / grupo->totalUsuarios;

    for (int i = 0; i < grupo->totalUsuarios; i++) {
        grupo->usuarios[i]->saldo -= dividido;
    }

    grupo->usuarios[pagador]->saldo += valor;

    printf("Despesa registrada!\n");
}

void verSaldos() {
    printf("\n--- SALDOS ---\n");
    for (int i = 0; i < totalUsuarios; i++) {
        printf("%d - %s: %.2f\n", i, usuarios[i].nome, usuarios[i].saldo);
    }
}

void menu() {
    int op;

    do {
        printf("\n===== MIND FREE TERMINAL =====\n");
        printf("1 - Cadastrar usuario\n");
        printf("2 - Criar grupo\n");
        printf("3 - Adicionar despesa\n");
        printf("4 - Ver saldos\n");
        printf("0 - Sair\n");
        printf("Escolha: ");
        scanf("%d", &op);

        switch (op) {
            case 1: cadastrarUsuario(); break;
            case 2: criarGrupo(); break;
            case 3: adicionarDespesa(); break;
            case 4: verSaldos(); break;
        }

    } while (op != 0);
}

int main() {
    menu();
    return 0;
}
