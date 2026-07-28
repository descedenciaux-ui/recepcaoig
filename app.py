import os
import re
from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_file
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

# ==========================================
# FUNÇÕES DE SUPORTE
# ==========================================
def obter_nomes_arquivos():
    """Gera os nomes dos arquivos baseados na data atual."""
    data_hoje = datetime.now().strftime("%d-%m-%Y")
    return f"visitantes_{data_hoje}.xlsx", f"ficha_pastor_{data_hoje}.pdf"

def carregar_visitantes_do_excel():
    """Lê o Excel do dia atual para recuperar os visitantes caso o servidor reinicie."""
    arquivo_excel, _ = obter_nomes_arquivos()
    visitantes = []

    if os.path.exists(arquivo_excel):
        try:
            df = pd.read_excel(arquivo_excel)
            for _, row in df.iterrows():
                # Extrai apenas o horário do campo Data/Hora
                data_hora = str(row.get("Data/Hora", ""))
                horario = data_hora.split(" ")[1] if " " in data_hora else "00:00"

                visitantes.append({
                    "nome": str(row.get("Nome", "")).upper(),
                    "bairro": str(row.get("Bairro", "Não informado")),
                    "convidado": str(row.get("Convidado Por", "Veio por conta")),
                    "horario": horario
                })
        except Exception as e:
            print(f"Aviso ao carregar Excel existente: {e}")

    return visitantes

def gerar_pdf_pastor(visitantes):
    """Gera o arquivo PDF formatado para o pastor."""
    _, arquivo_pdf = obter_nomes_arquivos()
    cnv = canvas.Canvas(arquivo_pdf, pagesize=A4)
    largura, altura = A4

    # Cabeçalho do PDF
    cnv.setFont("Helvetica-Bold", 16)
    cnv.drawString(50, altura - 50, "VISITANTES PARA APRESENTAÇÃO")

    cnv.setFont("Helvetica", 10)
    cnv.drawString(50, altura - 68, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Total: {len(visitantes)}")
    
    cnv.setLineWidth(1)
    cnv.line(50, altura - 75, largura - 50, altura - 75)

    # Lista de Visitantes
    y = altura - 110
    for idx, v in enumerate(visitantes, start=1):
        cnv.setFont("Helvetica-Bold", 12)
        cnv.drawString(50, y, f"{idx}. {v['nome']}")

        cnv.setFont("Helvetica", 9)
        cnv.drawString(70, y - 14, f"Bairro: {v['bairro']}  |  Convidado por: {v['convidado']}  |  Chegou às: {v['horario']}")

        cnv.setDash(1, 3)
        cnv.line(50, y - 22, largura - 50, y - 22)
        cnv.setDash([])

        y -= 40
        if y < 60:
            cnv.showPage()
            y = altura - 50

    cnv.save()
    return arquivo_pdf

# ==========================================
# ROTAS DA APLICAÇÃO
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    dados = request.json or {}
    
    nome = dados.get('nome', '').strip()
    whatsapp = dados.get('whatsapp', '').strip()
    bairro = dados.get('bairro', '').strip() or "Não informado"
    convidado = dados.get('convidado', '').strip() or "Veio por conta"
    oracao = dados.get('oracao', '').strip() or "Sem pedido"

    if not nome:
        return jsonify({'sucesso': False, 'mensagem': 'O campo Nome é obrigatório!'}), 400

    horario_atual = datetime.now()
    arquivo_excel, _ = obter_nomes_arquivos()

    # 1. Monta o registro
    novo = {
        "Data/Hora": [horario_atual.strftime("%d/%m/%Y %H:%M")],
        "Nome": [nome.title()],
        "WhatsApp": [whatsapp],
        "Bairro": [bairro.title()],
        "Convidado Por": [convidado.title()],
        "Pedido de Oração": [oracao]
    }
    df_novo = pd.DataFrame(novo)

    # 2. Grava ou Atualiza o Excel
    try:
        if os.path.exists(arquivo_excel):
            df_existente = pd.read_excel(arquivo_excel)
            df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        else:
            df_final = df_novo

        df_final.to_excel(arquivo_excel, index=False)

        # 3. Recarrega a lista do dia e re-gera o PDF
        visitantes_do_dia = carregar_visitantes_do_excel()
        gerar_pdf_pastor(visitantes_do_dia)

        return jsonify({'sucesso': True, 'mensagem': f'Visitante "{nome.title()}" cadastrado com sucesso!'})

    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao salvar os dados: {str(e)}'}), 500

@app.route('/pdf')
def ver_pdf():
    """Rota para visualizar/baixar o PDF gerado diretamente pelo navegador."""
    _, arquivo_pdf = obter_nomes_arquivos()
    if os.path.exists(arquivo_pdf):
        return send_file(arquivo_pdf, mimetype='application/pdf')
    
    # Se ainda não houver PDF gerado hoje, gera um vazio com a lista atual
    visitantes_do_dia = carregar_visitantes_do_excel()
    pdf_criado = gerar_pdf_pastor(visitantes_do_dia)
    return send_file(pdf_criado, mimetype='application/pdf')

# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
