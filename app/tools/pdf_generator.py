import os
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from bs4 import BeautifulSoup
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

def generate_pdf_from_md(md_content: str, output_path: str) -> bool:
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert markdown to html
        html = markdown.markdown(md_content)
        soup = BeautifulSoup(html, "html.parser")
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Add custom style for wrapping long text / URLs
        custom_style = ParagraphStyle(
            'Custom',
            parent=styles['Normal'],
            wordWrap='CJK',
            spaceAfter=6
        )
        title_style = styles['Title']
        heading1 = styles['Heading1']
        heading2 = styles['Heading2']
        
        story = []
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li']):
            text = element.get_text().strip()
            if not text:
                continue
                
            if element.name == 'h1':
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 12))
            elif element.name == 'h2':
                story.append(Paragraph(text, heading1))
                story.append(Spacer(1, 8))
            elif element.name == 'h3':
                story.append(Paragraph(text, heading2))
                story.append(Spacer(1, 6))
            elif element.name == 'li':
                story.append(Paragraph(f"• {text}", custom_style))
            else:
                story.append(Paragraph(text, custom_style))
                story.append(Spacer(1, 6))
                
        doc.build(story)
        logger.info(f"PDF generated successfully at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return False
