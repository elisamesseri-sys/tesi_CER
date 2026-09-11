import pulp

# =========================
# INSIEMI
# =========================

T = range(24)

utenti = [
    "P1", "P2", "P3", "P4",
    "C1", "C2", "C3", "C4", "C5", "C6"
]

prosumer = ["P1", "P2", "P3", "P4"]


# =========================
# PRODUZIONE FOTOVOLTAICA
# =========================

pv_singolo = [
    0.0000, 0.0000, 0.0000, 0.0000,
    0.0096, 0.6215, 1.8913, 3.5258,
    5.0660, 6.0967, 6.6114, 5.6601,
    6.9118, 4.1782, 5.2200, 3.8761,
    2.2244, 0.7514, 0.2000, 0.0000,
    0.0000, 0.0000, 0.0000, 0.0000
]

# Produzione complessiva della CER:

pv_tot = [4 * valore for valore in pv_singolo]


# =========================
# PREZZI DI ACQUISTO
# =========================

c_acq = [
    0.137678, 0.119700, 0.110703, 0.104700,
    0.103889, 0.104280, 0.106985, 0.123400,
    0.140768, 0.145182, 0.127740, 0.124706,
    0.121048, 0.106096, 0.106800, 0.119410,
    0.120162, 0.127533, 0.124767, 0.141823,
    0.171553, 0.191403, 0.170017, 0.157270
]


# =========================
# PREZZI DI VENDITA
# =========================

c_vend = [
    0.13400, 0.11970, 0.11070, 0.10470,
    0.10389, 0.10428, 0.10698, 0.12340,
    0.13767, 0.14445, 0.12601, 0.12280,
    0.11939, 0.10488, 0.10680, 0.11941,
    0.12000, 0.12578, 0.12280, 0.13800,
    0.16660, 0.18746, 0.16473, 0.15115
]


# =========================
# PROFILO MEDIO ARERA
# =========================

domanda_arera = [
    0.169, 0.141, 0.126, 0.119,
    0.116, 0.119, 0.134, 0.160,
    0.167, 0.165, 0.165, 0.172,
    0.188, 0.198, 0.198, 0.190,
    0.184, 0.188, 0.207, 0.253,
    0.272, 0.274, 0.250, 0.209
]


# =========================
# FATTORI DI SCALA UTENTI
# =========================

k = {
    "P1": 0.85,
    "P2": 0.95,
    "P3": 1.05,
    "P4": 1.15,
    "C1": 0.80,
    "C2": 0.90,
    "C3": 0.95,
    "C4": 1.05,
    "C5": 1.10,
    "C6": 1.20
}


# Domanda di ciascun utente in ciascuna ora
D = {
    (u, t): k[u] * domanda_arera[t]
    for u in utenti
    for t in T
}


# Domanda complessiva della CER per ogni ora
D_tot = [
    sum(D[u, t] for u in utenti)
    for t in T
]


# =========================
# PARAMETRI DEL BESS
# =========================

E_nom = 9.50

SOC_min = 0.95
SOC_max = 8.55
SOC_iniz = 4.75

eta_c = 0.96
eta_d = 0.96

e_c_max = 2.76
e_s_max = 2.76


# =========================
# CONTROLLO DATI
# =========================

print("Produzione FV totale giornaliera:", sum(pv_tot), "kWh")
print("Domanda totale giornaliera CER:", sum(D_tot), "kWh")
print("SOC iniziale:", SOC_iniz, "kWh")

# =========================
# CREAZIONE DEL MODELLO MILP
# =========================

modello = pulp.LpProblem(
    "Gestione_energetica_CER",
    pulp.LpMinimize
)


# =========================
# VARIABILI DECISIONALI
# =========================

# Energia acquistata dalla rete [kWh]
e_acq = pulp.LpVariable.dicts(
    "e_acq",
    T,
    lowBound=0,
    cat="Continuous"
)

# Energia immessa in rete [kWh]
e_im = pulp.LpVariable.dicts(
    "e_im",
    T,
    lowBound=0,
    cat="Continuous"
)

# Energia caricata nella batteria [kWh]
e_c = pulp.LpVariable.dicts(
    "e_c",
    T,
    lowBound=0,
    cat="Continuous"
)

# Energia scaricata dalla batteria [kWh]
e_s = pulp.LpVariable.dicts(
    "e_s",
    T,
    lowBound=0,
    cat="Continuous"
)

# Stato di carica della batteria [kWh]
SOC = pulp.LpVariable.dicts(
    "SOC",
    T,
    lowBound=SOC_min,
    upBound=SOC_max,
    cat="Continuous"
)

# Variabile binaria:
# 1 = modalità di carica
# 0 = modalità di scarica
y = pulp.LpVariable.dicts(
    "y",
    T,
    cat="Binary"
)
z = pulp.LpVariable.dicts(
    "z",
    T,
    cat="Binary"
)


# =========================
# FUNZIONE OBIETTIVO
# =========================

modello += pulp.lpSum(
    c_acq[t] * e_acq[t]
    - c_vend[t] * e_im[t]
    for t in T
), "Costo_netto_energia"

# =========================
# VINCOLI
# =========================

# 1. Bilancio energetico
for t in T:
    modello += (
        pv_tot[t]
        + e_acq[t]
        + e_s[t]
        ==
        D_tot[t]
        + e_c[t]
        + e_im[t]
    ), f"Bilancio_energetico_{t}"


# 2. Stato di carica nel primo intervallo
modello += (
    SOC[0]
    ==
    SOC_iniz
    + eta_c * e_c[0]
    - e_s[0] / eta_d
), "SOC_iniziale"


# 3. Dinamica della batteria
for t in range(1, 24):
    modello += (
        SOC[t]
        ==
        SOC[t - 1]
        + eta_c * e_c[t]
        - e_s[t] / eta_d
    ), f"Dinamica_SOC_{t}"


# 4. Stato finale uguale allo stato iniziale
modello += (
    SOC[23] == SOC_iniz
), "SOC_finale"


# 5. Limite di carica e modalità operativa
for t in T:
    modello += (
        e_c[t] <= e_c_max * y[t]
    ), f"Limite_carica_{t}"


# 6. Limite di scarica e modalità operativa
for t in T:
    modello += (
        e_s[t] <= e_s_max * (1 - y[t])
    ), f"Limite_scarica_{t}"

# 7. Modalità di scambio con la rete:
# acquisto e immissione non possono avvenire simultaneamente
for t in T:

    modello += (
        e_acq[t]
        <= (D_tot[t] + e_c_max) * z[t]
    ), f"Modalita_acquisto_{t}"

    modello += (
        e_im[t]
        <= (pv_tot[t] + e_s_max) * (1 - z[t])
    ), f"Modalita_immissione_{t}"

# =========================
# RISOLUZIONE DEL MODELLO
# =========================

solver = pulp.PULP_CBC_CMD(msg=True)

modello.solve(solver)


# =========================
# RISULTATI PRINCIPALI
# =========================

print("\n=========================")
print("RISULTATI OTTIMIZZAZIONE")
print("=========================")

stato = pulp.LpStatus[modello.status]
print("Stato:", stato)

if stato == "Optimal":
    print(
        "Costo netto ottimale:",
        round(pulp.value(modello.objective), 4),
        "euro"
    )
else:
    print("Nessuna soluzione ottima trovata.")
    # =========================
# RISULTATI ORARI
# =========================

if stato == "Optimal":

    print("\n")
    print(
       f"{'Ora':>3} | {'Domanda':>8} | {'FV':>8} | "
f"{'Acquisto':>9} | {'Immissione':>10} | "
f"{'Carica':>8} | {'Scarica':>8} | {'SOC':>8} | {'y':>3} | {'z':>3}"
    )

    print("-" * 100)

    for t in T:
        print(
            f"{t:>3} | "
            f"{D_tot[t]:>8.3f} | "
            f"{pv_tot[t]:>8.3f} | "
            f"{e_acq[t].value():>9.3f} | "
            f"{e_im[t].value():>10.3f} | "
            f"{e_c[t].value():>8.3f} | "
            f"{e_s[t].value():>8.3f} | "
            f"{SOC[t].value():>8.3f} | "
            f"{y[t].value():>3.0f} | "
            f"{z[t].value():>3.0f}"
        )


    # =========================
    # TOTALI GIORNALIERI
    # =========================

    totale_acquisto = sum(e_acq[t].value() for t in T)
    totale_immissione = sum(e_im[t].value() for t in T)
    totale_carica = sum(e_c[t].value() for t in T)
    totale_scarica = sum(e_s[t].value() for t in T)

    print("\nTOTALI GIORNALIERI")
    print("------------------")
    print("Energia acquistata:", round(totale_acquisto, 3), "kWh")
    print("Energia immessa:", round(totale_immissione, 3), "kWh")
    print("Energia caricata:", round(totale_carica, 3), "kWh")
    print("Energia scaricata:", round(totale_scarica, 3), "kWh")
