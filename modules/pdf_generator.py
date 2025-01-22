from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime
import os


class RelatorioPDF:
    def __init__(self, obra_id, numero_medicao):
        self.obra_id = obra_id
        self.numero_medicao = numero_medicao
        self.filename = f"relatorio_medicao_{obra_id}_{numero_medicao}.pdf"
        self.doc = SimpleDocTemplate(
            self.filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        self.styles = getSampleStyleSheet()
        self.elements = []

        # Criar estilo personalizado para títulos
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        ))

    def add_cabecalho(self, dados_obra):
        """Adiciona o cabeçalho do relatório"""
        # Título principal
        title = Paragraph(
            "TERMO DE RECEBIMENTO PROVISÓRIO",
            self.styles['CustomTitle']
        )
        self.elements.append(title)

        # Dados da obra
        dados = [
            ["Contrato nº:", dados_obra['contrato']],
            ["Nº da OS:", dados_obra['ordem_servico']],
            ["Objeto:", dados_obra['nome']],
            ["Contratante:", dados_obra['contratante']],
            ["Contratada:", dados_obra['contratada']],
            ["Valor Total:", f"R$ {dados_obra['valor_total']:,.2f}"]
        ]

        table = Table(dados, colWidths=[120, 350])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))

        self.elements.append(table)
        self.elements.append(Spacer(1, 20))

    def add_medicao(self, dados_medicao):
        """Adiciona os dados da medição"""
        self.elements.append(Paragraph(
            f"Medição #{self.numero_medicao}",
            self.styles['Heading2']
        ))

        dados = [
            ["Valor Previsto:", f"R$ {dados_medicao['valor_previsto']:,.2f}"],
            ["Valor Realizado:", f"R$ {dados_medicao['valor_realizado']:,.2f}"],
            ["Percentual Previsto:", f"{dados_medicao['percentual_previsto']:.2f}%"],
            ["Percentual Realizado:", f"{dados_medicao['percentual_realizado']:.2f}%"],
            ["IDP:", f"{dados_medicao['idp']:.2f}"]
        ]

        table = Table(dados, colWidths=[120, 350])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))

        self.elements.append(table)
        self.elements.append(Spacer(1, 20))

    def add_graficos(self, graficos):
        """Adiciona os gráficos ao relatório"""
        if graficos:  # Verifica se graficos não é None
            for grafico in graficos:
                if grafico:  # Verifica se o caminho do gráfico não é None
                    img = Image(grafico)
                    img.drawHeight = 300
                    img.drawWidth = 450
                    self.elements.append(img)
                    self.elements.append(Spacer(1, 20))

    def add_conclusao(self, dados_medicao):
        """Adiciona a conclusão e análise"""
        texto = f"""
        Ao observar os dados apresentados, entende-se que a obra teve um desempenho 
        {'acima' if dados_medicao['idp'] > 1 else 'abaixo'} do previsto para o período.

        IDP atual: {dados_medicao['idp']:.2f}
        Desvio total: {dados_medicao['desvio']:.2f}%
        Percentual realizado: {dados_medicao['percentual_realizado']:.2f}%
        """

        self.elements.append(Paragraph(texto, self.styles['Normal']))
        self.elements.append(Spacer(1, 30))

    def add_assinaturas(self):
        """Adiciona o espaço para assinaturas"""
        assinaturas = [
            ["_" * 30, "_" * 30],
            ["Fiscal Técnico", "Representante da Contratada"],
            ["Matrícula:", "CPF:"]
        ]

        table = Table(assinaturas, colWidths=[220, 220])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))

        self.elements.append(table)

def gerar(self, dados_obra, dados_medicao, graficos=None):
    """Gera o relatório PDF completo"""
    self.add_cabecalho(dados_obra)
    self.add_medicao(dados_medicao)
    if graficos:  # Só adiciona gráficos se existirem
        self.add_graficos(graficos)
    self.add_conclusao(dados_medicao)
    self.add_assinaturas()

    self.doc.build(self.elements)
    return self.filename


def generate_pdf_report(obra_id, numero_medicao, dados_obra, dados_medicao, graficos):
    """Função principal para gerar o relatório"""
    relatorio = RelatorioPDF(obra_id, numero_medicao)
    relatorio.add_cabecalho(dados_obra)
    relatorio.add_medicao(dados_medicao)
    if graficos:
        relatorio.add_graficos(graficos)
    relatorio.add_conclusao(dados_medicao)
    relatorio.add_assinaturas()
    relatorio.doc.build(relatorio.elements)
    return relatorio.filename
