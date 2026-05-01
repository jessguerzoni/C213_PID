const API = "http://localhost:8000";

// ===== TROCA DE MODO =====
function trocarModo() {
    const modo = document.querySelector('input[name="modo"]:checked').value;

    document.getElementById("auto").style.display =
        modo === "auto" ? "block" : "none";

    document.getElementById("manual").style.display =
        modo === "manual" ? "block" : "none";
}


// ===== SIMULAÇÃO =====
async function simular() {

    console.log("clicou");

    const modo = document.querySelector('input[name="modo"]:checked').value;
    const setpoint = parseFloat(document.getElementById("sp").value) || 1;

    let url = "";

    try {

        // ===== MONTA URL =====
        if (modo === "auto") {

            const metodo = document.getElementById("metodo").value;
            url = `${API}/pid/${metodo}`;

        } else {

            const kp = parseFloat(document.getElementById("kp").value);
            const ti = parseFloat(document.getElementById("ti").value);
            const td = parseFloat(document.getElementById("td").value);

            if (isNaN(kp) || isNaN(ti) || isNaN(td)) {
                alert("Digite valores validos!");
                return;
            }

            url = `${API}/pid_manual?kp=${kp}&ti=${ti}&td=${td}`;
        }

        console.log("Chamando:", url);

        // ===== CHAMA BACKEND =====
        const res = await fetch(url);

        if (!res.ok) {
            const erroTexto = await res.text();
            throw new Error(`Erro HTTP ${res.status}: ${erroTexto}`);
        }

        const data = await res.json();

        console.log("Resposta:", data);

        // ===== VALIDAÇÃO =====
        if (!data.tempo || !data.saida || data.tempo.length === 0) {
            throw new Error("Dados invalidos do backend");
        }

        const y = data.saida;
        const final = y[y.length - 1];

        // ===== OVERSHOOT (%) =====
        let overshoot = 0;

        if (final !== 0) {
            overshoot = ((Math.max(...y) - final) / Math.abs(final)) * 100;
        }

        document.getElementById("mp").value =
            isFinite(overshoot) ? overshoot.toFixed(2) + "%" : "0%";


        // ===== GRÁFICO =====
        const canvas = document.getElementById('grafico');

        if (!canvas) {
            throw new Error("Canvas não encontrado");
        }

        const ctx = canvas.getContext('2d');

        // 🔥 DESTRUIR GRÁFICO COM SEGURANÇA
        try {
            if (window.grafico && typeof window.grafico.destroy === "function") {
                window.grafico.destroy();
            }
        } catch (e) {
            console.warn("Erro ao destruir gráfico:", e);
        }

        // ===== CRIAR GRÁFICO =====
        window.grafico = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.tempo,
                datasets: [
                    {
                        label: 'Resposta do Sistema',
                        data: data.saida,
                        borderColor: 'blue',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.2
                    },
                    {
                        label: 'Setpoint',
                        data: data.tempo.map(() => setpoint),
                        borderColor: 'red',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Tempo"
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: "Saída"
                        }
                    }
                }
            }
        });

        console.log("Grafico criado:", window.grafico);

    } catch (erro) {
        console.error("Erro detalhado:", erro);
        alert("Erro: " + erro.message);
    }
}