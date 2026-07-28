import os
import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ==========================================
# CONFIGURAÇÕES E CONSTANTES
# ==========================================
COR_FUNDO = "#1A1F26"
COR_BARRA = "#282E3A"
COR_INPUT_BG = "#282E3A"
COR_CIANO = "#00E5FF"
COR_BRANCO = "#FFFFFF"
COR_CINZA_CLARO = "#ADB5BD"
COR_PLACEHOLDER = "#6B7280"

visitantes_do_dia = []

# ==========================================
# FUNÇÕES DE NOMES DE ARQUIVO DINÂMICOS
# ==========================================
def obter_nomes_arquivos():
    """Gera nomes de arquivos únicos baseados na data atual (Ex: visitantes_28-07-2026.xlsx)."""
    data_hoje = datetime.now().strftime("%d-%m-%Y")
    arquivo_excel = f"visitantes_{data_hoje}.xlsx"
    arquivo_pdf = f"ficha_pastor_{data_hoje}.pdf"
    return arquivo_excel, arquivo_pdf

# ==========================================
# FUNÇÕES DE MÁSCARA E FORMATAÇÃO
# ==========================================
def permitir_apenas_letras_e_espacos(event):
    """Permite digitação livre de letras, acentos e espaços em tempo real."""
    widget = event.widget
    texto = widget.get()
    
    texto_limpo = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', texto)
    
    if texto != texto_limpo:
        pos = widget.index(tk.INSERT)
        widget.delete(0, tk.END)
        widget.insert(0, texto_limpo)
        widget.icursor(max(0, pos - 1))

def capitalizar_ao_sair(event):
    """Capitaliza as palavras (Primeira Letra Maiúscula) ao sair do campo."""
    widget = event.widget
    texto = widget.get().strip()
    
    if texto and texto not in placeholders_entry:
        texto_capitalizado = ' '.join(word.capitalize() for word in texto.split())
        widget.delete(0, tk.END)
        widget.insert(0, texto_capitalizado)

def aplicar_mascara_phone(texto):
    """Gera a string formatada de telefone (00) 00000-0000."""
    digitos = re.sub(r'\D', '', texto)[:11]
    if not digitos:
        return ""
    if len(digitos) <= 2:
        return f"({digitos}"
    if len(digitos) <= 7:
        return f"({digitos[:2]}) {digitos[2:]}"
    return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"

def formatar_telefone(event):
    """Aplica a máscara do WhatsApp durante a digitação."""
    widget = event.widget
    texto_atual = widget.get()
    texto_mascarado = aplicar_mascara_phone(texto_atual)
    if texto_atual != texto_mascarado:
        widget.delete(0, tk.END)
        widget.insert(0, texto_mascarado)

# ==========================================
# REGRAS DE NEGÓCIO E PERSISTÊNCIA
# ==========================================
def salvar_visitante():
    nome = entry_nome.get().strip()
    whatsapp = entry_whatsapp.get().strip()
    bairro = entry_bairro.get().strip()
    convidado_por = entry_convite.get().strip()
    pedido_oracao = text_oracao.get("1.0", tk.END).strip()

    # Validação mínima obrigatória
    if not nome or nome == "Nome completo":
        messagebox.showwarning("Atenção", "O campo 'Nome completo' é obrigatório!")
        return

    # Tratamento para placeholders não preenchidos
    whatsapp = "" if whatsapp == "WhatsApp (com DDD)" else whatsapp
    bairro = "Não informado" if (not bairro or bairro == "Bairro") else bairro
    convidado_por = "Veio por conta" if (not convidado_por or convidado_por == "Quem convidou?") else convidado_por
    pedido_oracao = "Sem pedido" if (not pedido_oracao or pedido_oracao == "Pedido de Oração") else pedido_oracao

    horario_atual = datetime.now()
    data_hora_str = horario_atual.strftime("%d/%m/%Y %H:%M")

    # Obter nomes dos arquivos com a DATA ATUAL
    arquivo_excel, arquivo_pdf = obter_nomes_arquivos()

    # 1. Salvar no Excel ESPECÍFICO DO DIA
    novo_registro = {
        "Data/Hora": [data_hora_str],
        "Nome": [nome],
        "WhatsApp": [whatsapp],
        "Bairro": [bairro],
        "Convidado Por": [convidado_por],
        "Pedido de Oração": [pedido_oracao]
    }
    df_novo = pd.DataFrame(novo_registro)

    try:
        if os.path.exists(arquivo_excel):
            df_existente = pd.read_excel(arquivo_excel)
            df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        else:
            df_final = df_novo

        df_final.to_excel(arquivo_excel, index=False)

        # 2. Atualizar lista em memória e gerar PDF ESPECÍFICO DO DIA
        visitantes_do_dia.append({
            "nome": nome,
            "bairro": bairro,
            "convidado": convidado_por,
            "horario": horario_atual.strftime("%H:%M")
        })
        gerar_pdf_pastor(arquivo_pdf)

        messagebox.showinfo("Sucesso", f"Visitante '{nome}' cadastrado com sucesso!\nSalvo em: {arquivo_excel}")
        limpar_formulario()

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar dados:\n{e}")

def gerar_pdf_pastor(nome_arquivo_pdf):
    cnv = canvas.Canvas(nome_arquivo_pdf, pagesize=A4)
    largura, altura = A4

    cnv.setFont("Helvetica-Bold", 16)
    cnv.drawString(50, altura - 50, "VISITANTES PARA APRESENTAÇÃO")

    cnv.setFont("Helvetica", 10)
    cnv.drawString(50, altura - 68, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Total do Dia: {len(visitantes_do_dia)}")

    cnv.setLineWidth(1)
    cnv.line(50, altura - 75, largura - 50, altura - 75)

    y = altura - 110
    for idx, v in enumerate(visitantes_do_dia, start=1):
        cnv.setFont("Helvetica-Bold", 12)
        cnv.drawString(50, y, f"{idx}. {v['nome'].upper()}")

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

def limpar_formulario():
    for entry, ph in zip(inputs_entry, placeholders_entry):
        entry.delete(0, tk.END)
        entry.insert(0, ph)
        entry.config(fg=COR_PLACEHOLDER)
    
    text_oracao.delete("1.0", tk.END)
    text_oracao.insert("1.0", "Pedido de Oração")
    text_oracao.config(fg=COR_PLACEHOLDER)
    entry_nome.focus()

# ==========================================
# INTERFACE GRÁFICA (TKINTER)
# ==========================================
root = tk.Tk()
root.title("Recepção de Visitantes")
root.geometry("420x680")
root.resizable(False, False)
root.configure(bg=COR_FUNDO)

# 1. Barra Superior (App Bar)
frame_barra = tk.Frame(root, bg=COR_BARRA, height=50)
frame_barra.pack(fill=tk.X, side=tk.TOP)

tk.Label(frame_barra, text="←", font=("Segoe UI", 16), bg=COR_BARRA, fg=COR_BRANCO, cursor="hand2").pack(side=tk.LEFT, padx=12)
tk.Label(frame_barra, text="Recepção - Cadastro", font=("Segoe UI", 12, "bold"), bg=COR_BARRA, fg=COR_BRANCO).pack(side=tk.LEFT, expand=True)
tk.Label(frame_barra, text="⚙", font=("Segoe UI", 14), bg=COR_BARRA, fg=COR_CINZA_CLARO, cursor="hand2").pack(side=tk.RIGHT, padx=12)

# 2. Cabeçalho Central
frame_header = tk.Frame(root, bg=COR_FUNDO)
frame_header.pack(fill=tk.X, pady=(15, 10))

tk.Label(frame_header, text="👤+", font=("Segoe UI", 36, "bold"), bg=COR_FUNDO, fg=COR_CIANO).pack()
tk.Label(frame_header, text="Cadastro de Visitante", font=("Segoe UI", 14, "bold"), bg=COR_FUNDO, fg=COR_CIANO).pack()

# 3. Formulário de Campos
frame_form = tk.Frame(root, bg=COR_FUNDO, padx=20)
frame_form.pack(fill=tk.X)

def criar_field(parent, icone, placeholder):
    container = tk.Frame(parent, bg=COR_INPUT_BG, bd=0)
    container.pack(fill=tk.X, pady=4)

    interno = tk.Frame(container, bg=COR_INPUT_BG, padx=10, pady=6)
    interno.pack(fill=tk.X)

    tk.Label(interno, text=icone, font=("Segoe UI", 12), bg=COR_INPUT_BG, fg=COR_CIANO).pack(side=tk.LEFT, padx=(0, 8))

    entry = tk.Entry(interno, font=("Segoe UI", 11), bg=COR_INPUT_BG, fg=COR_PLACEHOLDER, bd=0, relief=tk.FLAT, insertbackground=COR_CIANO)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    entry.insert(0, placeholder)

    def on_in(e):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=COR_BRANCO)

    def on_out(e):
        if not entry.get().strip():
            entry.insert(0, placeholder)
            entry.config(fg=COR_PLACEHOLDER)

    entry.bind("<FocusIn>", on_in)
    entry.bind("<FocusOut>", on_out)
    return entry

entry_nome = criar_field(frame_form, "👤", "Nome completo")
entry_whatsapp = criar_field(frame_form, "📱", "WhatsApp (com DDD)")
entry_bairro = criar_field(frame_form, "📍", "Bairro")
entry_convite = criar_field(frame_form, "👥", "Quem convidou?")

inputs_entry = [entry_nome, entry_whatsapp, entry_bairro, entry_convite]
placeholders_entry = ["Nome completo", "WhatsApp (com DDD)", "Bairro", "Quem convidou?"]

# BINDS
entry_nome.bind("<KeyRelease>", permitir_apenas_letras_e_espacos)
entry_whatsapp.bind("<KeyRelease>", formatar_telefone)

entry_nome.bind("<FocusOut>", capitalizar_ao_sair, add="+")
entry_bairro.bind("<FocusOut>", capitalizar_ao_sair, add="+")
entry_convite.bind("<FocusOut>", capitalizar_ao_sair, add="+")

# Campo: Pedido de Oração (Multiline)
container_oracao = tk.Frame(frame_form, bg=COR_INPUT_BG, bd=0)
container_oracao.pack(fill=tk.X, pady=4)

interno_oracao = tk.Frame(container_oracao, bg=COR_INPUT_BG, padx=10, pady=6)
interno_oracao.pack(fill=tk.X)

tk.Label(interno_oracao, text="❤️", font=("Segoe UI", 12), bg=COR_INPUT_BG, fg=COR_CIANO).pack(side=tk.LEFT, padx=(0, 8), anchor=tk.N)

text_oracao = tk.Text(interno_oracao, font=("Segoe UI", 11), bg=COR_INPUT_BG, fg=COR_PLACEHOLDER, bd=0, height=3, wrap=tk.WORD, insertbackground=COR_CIANO)
text_oracao.pack(side=tk.LEFT, fill=tk.X, expand=True)
text_oracao.insert("1.0", "Pedido de Oração")

def on_in_oracao(e):
    if text_oracao.get("1.0", tk.END).strip() == "Pedido de Oração":
        text_oracao.delete("1.0", tk.END)
        text_oracao.config(fg=COR_BRANCO)

def on_out_oracao(e):
    if not text_oracao.get("1.0", tk.END).strip():
        text_oracao.insert("1.0", "Pedido de Oração")
        text_oracao.config(fg=COR_PLACEHOLDER)

text_oracao.bind("<FocusIn>", on_in_oracao)
text_oracao.bind("<FocusOut>", on_out_oracao)

# 4. Botão Cadastrar
btn_cadastrar = tk.Button(
    root, text="✔  Cadastrar Visitante", font=("Segoe UI", 11, "bold"),
    bg=COR_CIANO, fg="#000000", bd=0, cursor="hand2",
    activebackground="#00CCCC", activeforeground="#000000",
    command=salvar_visitante
)
btn_cadastrar.pack(fill=tk.X, padx=20, pady=(15, 10), ipady=6)

# 5. Rodapé
frame_footer = tk.Frame(root, bg=COR_FUNDO)
frame_footer.pack(side=tk.BOTTOM, pady=10)

tk.Label(frame_footer, text="🔄 Tentar conectar ao Altar", font=("Segoe UI", 9), bg=COR_FUNDO, fg=COR_CINZA_CLARO).pack()

root.mainloop()