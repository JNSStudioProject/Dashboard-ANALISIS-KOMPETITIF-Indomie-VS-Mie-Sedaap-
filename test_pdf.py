from fpdf import FPDF
pdf = FPDF(orientation='L', unit='mm', format='A4')
pdf.add_page()
pdf.set_font('Helvetica', 'B', 12)
pdf.cell(0, 10, 'Test', new_x="LMARGIN", new_y="NEXT", align='C')
out = pdf.output()
print(type(out))
