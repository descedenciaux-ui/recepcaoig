from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

visitantes_do_dia = []

def obter_nomes_arquivos():
    data_hoje = datetime.now().strftime("%d-%m-%Y")
    return f"visitantes_{data_hoje}.xlsx", f"ficha_pastor_{data_hoje}.pdf"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    dados = request.json
    nome = dados.get('nome', '').strip()
    whatsapp = dados.get('whatsapp', '').strip()
    bairro = dados.get('bairro', '').strip() or "Não informado"
    convidado = dados.get('convidado', '').strip() or "Veio por conta"
    oracao = dados.get('oracao', '').strip() or "Sem pedido"

    if not nome:
        return jsonify({'sucesso': False, 'mensagem': 'Nome é obrigatório!'}), 400

    horario = datetime.now()
    arquivo_excel, arquivo_pdf = obter_nomes_arquivos()

    # Salva no Excel
    novo = {
        "Data/Hora": [horario.strftime("%d/%m/%Y %H:%M")],
        "Nome": [nome.title()],
        "WhatsApp": [whatsapp],
        "Bairro": [bairro.title()],
        "Convidado Por": [convidado.title()],
        "Pedido de Oração": [oracao]
    }
    df_novo = pd.DataFrame(novo)

    if os.path.exists(arquivo_excel):
        df_existente = pd.read_excel(arquivo_excel)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    df_final.to_excel(arquivo_excel, index=False)

    # Adiciona à lista do PDF do dia
    visitantes_do_dia.append({
        "nome": nome.title(),
        "bairro": bairro.title(),
        "convidado": convidado.title(),
        "horario": horario.strftime("%H:%M")
    })
    
    # Gera o PDF
    cnv = canvas.Canvas(arquivo_pdf, pagesize=A4)
    largura, altura = A4
    cnv.setFont("Helvetica-Bold", 16)
    cnv.drawString(50, altura - 50, "VISITANTES PARA APRESENTAÇÃO")
    cnv.setFont("Helvetica", 10)
    cnv.drawString(50, altura - 68, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Total: {len(visitantes_do_dia)}")
    cnv.line(50, altura - 75, largura - 50, altura - 75)

    y = altura - 110
    for idx, v in enumerate(visitantes_do_dia, start=1):
        cnv.setFont("Helvetica-Bold", 12)
        cnv.drawString(50, y, f"{idx}. {v['nome'].upper()}")
        cnv.setFont("Helvetica", 9)
        cnv.drawString(70, y - 14, f"Bairro: {v['bairro']} | Convidado por: {v['convidado']} | Chegou: {v['horario']}")
        y -= 35

    cnv.save()

    return jsonify({'sucesso': True, 'mensagem': f'Visitante {nome} cadastrado com sucesso!'})

@app.route('/baixar-pdf')
def baixar_pdf():
    _, arquivo_pdf = obter_nomes_arquivos()
    if os.path.exists(arquivo_pdf):
        return send_file(arquivo_pdf, as_attachment=True)
    return "Nenhum relatório PDF gerado para hoje ainda.", 404

@app.route('/baixar-excel')
def baixar_excel():
    arquivo_excel, _ = obter_nomes_arquivos()
    if os.path.exists(arquivo_excel):
        return send_file(arquivo_excel, as_attachment=True)
    return "Nenhuma planilha Excel gerada para hoje ainda.", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
