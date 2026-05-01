from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import control as ctrl
import numpy as np
import scipy.io

app = FastAPI()

# ===== LIBERA CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== CARREGA DATASET =====
mat = scipy.io.loadmat("Dataset_Grupo4_c213.mat")

# remove metadados
dados = {k: v for k, v in mat.items() if not k.startswith("__")}

print("Variáveis encontradas no .mat:", dados.keys())

# ===== IDENTIFICAÇÃO CORRETA DAS VARIÁVEIS =====

# TEMPO
if "tempo" in dados:
    tempo = dados["tempo"]
elif "tiempo" in dados:
    tempo = dados["tiempo"]
elif "t" in dados:
    tempo = dados["t"]
else:
    raise ValueError("Variável de tempo não encontrada")

# ENTRADA
if "entrada" in dados:
    entrada = dados["entrada"]
elif "dados_entrada" in dados:
    entrada = dados["dados_entrada"]
elif "u" in dados:
    entrada = dados["u"]
else:
    raise ValueError("Variável de entrada não encontrada")

# SAÍDA
if "saida" in dados:
    saida = dados["saida"]
elif "salida" in dados:
    saida = dados["salida"]
elif "dados_saida" in dados:
    saida = dados["dados_saida"]
elif "y" in dados:
    saida = dados["y"]
else:
    raise ValueError("Variável de saída não encontrada")

# flatten (garante vetor 1D)
tempo = tempo.flatten()
entrada = entrada.flatten()
saida = saida.flatten()

# ===== IDENTIFICAÇÃO DO SISTEMA =====

K = saida[-1]

idx_tau = np.where(saida >= 0.63 * K)[0]

if len(idx_tau) == 0:
    raise ValueError("Erro ao calcular tau")

tau = tempo[idx_tau[0]]

def sistema_forno():
    return ctrl.TransferFunction([K], [tau, 1])


# ===== ZIEGLER-NICHOLS =====
@app.get("/pid/zn")
def pid_zn():

    Kp = 1.2 / K
    Ti = 2 * tau
    Td = 0.5 * tau

    G = sistema_forno()
    C = ctrl.TransferFunction([Kp * Td, Kp, Kp / Ti], [1, 0])

    sistema = ctrl.feedback(C * G)
    t, y = ctrl.step_response(sistema)

    return {
        "tempo": t.tolist(),
        "saida": y.tolist(),
        "Kp": float(Kp),
        "Ti": float(Ti),
        "Td": float(Td)
    }


# ===== COHEN-COON =====
@app.get("/pid/cc")
def pid_cc():

    Kp = 0.9 / K
    Ti = 3 * tau
    Td = 0.3 * tau

    G = sistema_forno()
    C = ctrl.TransferFunction([Kp * Td, Kp, Kp / Ti], [1, 0])

    sistema = ctrl.feedback(C * G)
    t, y = ctrl.step_response(sistema)

    return {
        "tempo": t.tolist(),
        "saida": y.tolist(),
        "Kp": float(Kp),
        "Ti": float(Ti),
        "Td": float(Td)
    }


# ===== MANUAL =====
@app.get("/pid_manual")
def pid_manual(kp: float, ti: float, td: float):

    G = sistema_forno()
    C = ctrl.TransferFunction([kp * td, kp, kp / ti], [1, 0])

    sistema = ctrl.feedback(C * G)
    t, y = ctrl.step_response(sistema)

    return {
        "tempo": t.tolist(),
        "saida": y.tolist(),
        "Kp": kp,
        "Ti": ti,
        "Td": td
    }