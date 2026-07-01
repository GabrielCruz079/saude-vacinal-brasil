import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Conexão ──────────────────────────────────────────────
conn = mysql.connector.connect(
    host="localhost",
    user="root",        # troque se necessário
    password="",        # troque se necessário
    database="saude_vacinal"
)

# ── Extração ─────────────────────────────────────────────
cobertura = pd.read_sql("""
    SELECT e.nome AS estado, e.regiao, v.nome AS vacina,
           v.doenca_alvo, c.ano, c.doses_aplicadas,
           c.populacao_alvo, c.cobertura_pct
    FROM cobertura_vacinal c
    JOIN estados e ON c.id_estado = e.id_estado
    JOIN vacinas v ON c.id_vacina = v.id_vacina
""", conn)

casos = pd.read_sql("""
    SELECT e.nome AS estado, e.regiao,
           cn.ano, cn.doenca, cn.casos
    FROM casos_notificados cn
    JOIN estados e ON cn.id_estado = e.id_estado
""", conn)

conn.close()

# ── Exportar CSVs para Power BI ──────────────────────────
cobertura.to_csv("cobertura_vacinal.csv", index=False, encoding="utf-8-sig")
casos.to_csv("casos_notificados.csv", index=False, encoding="utf-8-sig")
print("CSVs exportados com sucesso!")

# ── Configuração visual ───────────────────────────────────
sns.set_theme(style="whitegrid")
cores_regiao = {
    "Sudeste": "#4C72B0", "Sul": "#55A868",
    "Nordeste": "#C44E52", "Norte": "#DD8452",
    "Centro-Oeste": "#8172B2"
}

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Análise de Saúde Vacinal — Brasil 2015–2023",
             fontsize=16, fontweight="bold", y=1.01)

# ── Gráfico 1: Cobertura média por região ao longo do tempo ──
ax1 = axes[0, 0]
media_regiao = cobertura.groupby(["ano", "regiao"])["cobertura_pct"].mean().reset_index()
for regiao, grupo in media_regiao.groupby("regiao"):
    ax1.plot(grupo["ano"], grupo["cobertura_pct"],
             marker="o", label=regiao, color=cores_regiao.get(regiao))
ax1.axhline(95, color="red", linestyle="--", linewidth=1, label="Meta OMS (95%)")
ax1.set_title("Cobertura Vacinal Média por Região")
ax1.set_ylabel("Cobertura (%)")
ax1.set_xlabel("Ano")
ax1.legend(fontsize=8)
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

# ── Gráfico 2: Top 5 estados com menor cobertura (média geral) ──
ax2 = axes[0, 1]
media_estado = cobertura.groupby("estado")["cobertura_pct"].mean().nsmallest(5).reset_index()
sns.barplot(data=media_estado, x="cobertura_pct", y="estado",
            palette="Reds_r", ax=ax2)
ax2.axvline(95, color="red", linestyle="--", linewidth=1, label="Meta 95%")
ax2.set_title("Top 5 Estados com Menor Cobertura")
ax2.set_xlabel("Cobertura Média (%)")
ax2.set_ylabel("")
ax2.legend(fontsize=8)

# ── Gráfico 3: Evolução de casos de Sarampo ──────────────
ax3 = axes[1, 0]
sarampo = casos[casos["doenca"] == "Sarampo"].groupby("ano")["casos"].sum().reset_index()
ax3.bar(sarampo["ano"], sarampo["casos"], color="#C44E52", alpha=0.85)
ax3.set_title("Casos de Sarampo por Ano — Brasil")
ax3.set_ylabel("Total de Casos")
ax3.set_xlabel("Ano")

# ── Gráfico 4: Cobertura média por vacina ────────────────
ax4 = axes[1, 1]
media_vacina = cobertura.groupby("vacina")["cobertura_pct"].mean().sort_values()
cores_bar = ["#d73027" if v < 95 else "#4C72B0" for v in media_vacina]
media_vacina.plot(kind="barh", ax=ax4, color=cores_bar)
ax4.axvline(95, color="red", linestyle="--", linewidth=1, label="Meta 95%")
ax4.set_title("Cobertura Média por Vacina")
ax4.set_xlabel("Cobertura (%)")
ax4.set_ylabel("")
ax4.legend(fontsize=8)

plt.tight_layout()
plt.savefig("analise_saude_vacinal.png", dpi=150, bbox_inches="tight")
plt.show()
print("Gráfico salvo!")