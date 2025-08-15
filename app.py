from flask import Flask, render_template, request
import numpy as np
import numpy_financial as npf

app = Flask(__name__)

def safe_irr(cash_flows):
    try:
        irr = npf.irr(cash_flows)
        if irr is None or (isinstance(irr, float) and np.isnan(irr)):
            return None
        return irr
    except Exception:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    # sempre passe um dict 'valores' ao template para evitar UndefinedError
    valores = {}

    if request.method == "POST":
        # preencher 'valores' com os campos recebidos (seguro)
        valores = request.form.to_dict()

        try:
            # converter campos (usar 0 como fallback para evitar erros)
            entrada = float(request.form.get("entrada", 0) or 0)
            parcelas_anuais = int(request.form.get("parcelas_anuais", 0) or 0)
            valor_parcela_anual = float(request.form.get("valor_parcela_anual", 0) or 0)
            parcelas_mensais = int(request.form.get("parcelas_mensais", 0) or 0)
            valor_parcela_mensal = float(request.form.get("valor_parcela_mensal", 0) or 0)
            mes_venda = int(request.form.get("mes_venda", 0) or 0)
            valor_venda = float(request.form.get("valor_venda", 0) or 0)

            # construir fluxo de caixa (mês 0 = entrada)
            total_meses = max(mes_venda, parcelas_mensais, parcelas_anuais * 12) + 1
            cash_flows = [0.0] * (total_meses)

            # Mês 0
            cash_flows[0] = -entrada

            # parcelas mensais: aplicadas nos meses 1..n
            for i in range(1, parcelas_mensais + 1):
                if i < total_meses:
                    cash_flows[i] -= valor_parcela_mensal

            # parcelas anuais: aplicadas em 12,24,...
            for i in range(1, parcelas_anuais + 1):
                mes = i * 12
                if mes < total_meses:
                    cash_flows[mes] -= valor_parcela_anual

            # venda (entrada positiva no mês escolhido)
            if mes_venda < total_meses:
                cash_flows[mes_venda] += valor_venda
            else:
                # se mes_venda for maior que total_meses, estender lista
                extra = mes_venda - (total_meses - 1)
                cash_flows.extend([0.0] * extra)
                cash_flows.append(valor_venda)

            # calcular TIR (mensal)
            tir_mensal = safe_irr(cash_flows)
            tir_anual = (1 + tir_mensal) ** 12 - 1 if tir_mensal is not None else None

            aporte_total = sum([-v for v in cash_flows if v < 0])
            retorno_total = sum([v for v in cash_flows if v > 0])
            lucro = retorno_total - aporte_total
            rentabilidade = (lucro / aporte_total) if aporte_total != 0 else None

            #agrupado por ano
            anos = []
            valores_anuais = []
            for start in range(0, len(cash_flows), 12):
                ano_idx = start // 12 + 1
                anos.append(f"Ano {ano_idx}")
                valores_anuais.append(round(sum(cash_flows[start:start+12]), 2))

            resultado = {
                "total_aporte": f"R$ {aporte_total:,.2f}",
                "total_recebido": f"R$ {retorno_total:,.2f}",
                "lucro_final": f"R$ {lucro:,.2f}",
                "tir_mensal": f"{tir_mensal*100:.2f}%" if tir_mensal is not None else "Não calculado",
                "tir_anual": f"{tir_anual*100:.2f}%" if tir_anual is not None else "Não calculado",
                "rentabilidade_total": f"{(rentabilidade*100):.2f}%" if rentabilidade is not None else "N/A",
                "grafico": {"labels": anos, "values": valores_anuais},
                "fluxo": cash_flows
            }

        except Exception as e:
            resultado = {"erro": str(e)}

    # sempre passamos as duas variáveis (mesmo em GET) para evitar undefined
    return render_template("index.html", resultado=resultado, valores=valores)


if __name__ == "__main__":
    app.run(debug=True)