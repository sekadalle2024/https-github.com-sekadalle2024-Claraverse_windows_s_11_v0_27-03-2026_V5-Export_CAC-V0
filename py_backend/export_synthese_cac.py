"""
Export de Synthèse CAC (Commissaire aux Comptes / Expert-Comptable)
Génère des rapports structurés pour la révision des comptes et le contrôle interne comptable
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# === MODÈLES PYDANTIC ===

class FrapPointMetadata(BaseModel):
    """Métadonnées d'un point FRAP"""
    etape: Optional[str] = None
    norme: Optional[str] = None
    methode: Optional[str] = None
    reference: Optional[str] = None


class FrapPoint(BaseModel):
    """Point FRAP (Feuille de Révélation et d'Analyse de Problème)"""
    metadata: FrapPointMetadata
    intitule: str
    observation: Optional[str] = ""
    constat: Optional[str] = ""
    risque: Optional[str] = ""
    recommandation: Optional[str] = ""


class RecosRevisionMetadata(BaseModel):
    """Métadonnées d'un point de recommandation révision"""
    etape: Optional[str] = None
    norme: Optional[str] = None
    methode: Optional[str] = None
    reference: Optional[str] = None


class RecosRevisionPoint(BaseModel):
    """Point de recommandation révision des comptes"""
    metadata: RecosRevisionMetadata
    intitule: str
    description: Optional[str] = ""
    observation: Optional[str] = ""
    ajustement: Optional[str] = ""
    regularisation: Optional[str] = ""


class RecosControleInterneMetadata(BaseModel):
    """Métadonnées d'un point de contrôle interne"""
    etape: Optional[str] = None
    norme: Optional[str] = None
    methode: Optional[str] = None
    reference: Optional[str] = None


class RecosControleInternePoint(BaseModel):
    """Point de recommandation contrôle interne comptable"""
    metadata: RecosControleInterneMetadata
    intitule: str
    observation: Optional[str] = ""
    constat: Optional[str] = ""
    risque: Optional[str] = ""
    recommandation: Optional[str] = ""


class SyntheseCAC_Request(BaseModel):
    """Requête pour générer une synthèse CAC"""
    frap_points: List[FrapPoint] = []
    recos_revision_points: List[RecosRevisionPoint] = []
    recos_controle_interne_points: List[RecosControleInternePoint] = []
    date_rapport: Optional[str] = None
    entite: Optional[str] = "Entité auditée"
    exercice: Optional[str] = None


# === FONCTIONS UTILITAIRES ===

def add_heading_with_numbering(doc: Document, text: str, level: int):
    """Ajouter un titre avec numérotation"""
    heading = doc.add_heading(text, level=level)
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    # Style du titre
    run = heading.runs[0]
    run.font.name = 'Calibri'
    run.font.size = Pt(14 if level == 1 else 12 if level == 2 else 11)
    run.font.bold = True
    run.font.color.rgb = RGBColor(31, 56, 100)  # Bleu foncé professionnel
    
    return heading


def add_formatted_paragraph(doc: Document, text: str, bold: bool = False, italic: bool = False, indent: float = 0):
    """Ajouter un paragraphe formaté"""
    para = doc.add_paragraph()
    
    if indent > 0:
        para.paragraph_format.left_indent = Inches(indent)
    
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.line_spacing = 1.15
    
    run = para.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.bold = bold
    run.font.italic = italic
    
    return para


def add_section_content(doc: Document, label: str, content: str, indent: float = 0.25):
    """Ajouter une section avec label et contenu"""
    if not content or content.strip() == "":
        return
    
    # Label en gras
    para = doc.add_paragraph()
    if indent > 0:
        para.paragraph_format.left_indent = Inches(indent)
    
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.line_spacing = 1.15
    
    run_label = para.add_run(f"{label}: ")
    run_label.font.name = 'Calibri'
    run_label.font.size = Pt(11)
    run_label.font.bold = True
    
    # Contenu normal
    run_content = para.add_run(content)
    run_content.font.name = 'Calibri'
    run_content.font.size = Pt(11)


def create_synthese_cac_document(request: SyntheseCAC_Request) -> BytesIO:
    """
    Créer le document Word de synthèse CAC
    
    Structure:
    1. INTRODUCTION
    2. OBSERVATIONS D'AUDIT (Recos Révision des Comptes)
    3. POINTS DE CONTRÔLE INTERNE (FRAP + Recos Contrôle Interne)
    """
    
    doc = Document()
    
    # Configuration des marges
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    # === EN-TÊTE DU RAPPORT ===
    title = doc.add_heading('SYNTHÈSE DES TRAVAUX DE RÉVISION', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.runs[0]
    title_run.font.name = 'Calibri'
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(31, 56, 100)
    
    # Informations générales
    doc.add_paragraph()
    if request.entite:
        add_formatted_paragraph(doc, f"Entité: {request.entite}", bold=True)
    if request.exercice:
        add_formatted_paragraph(doc, f"Exercice: {request.exercice}", bold=True)
    if request.date_rapport:
        add_formatted_paragraph(doc, f"Date du rapport: {request.date_rapport}", bold=True)
    
    doc.add_paragraph()
    
    # === 1. INTRODUCTION ===
    add_heading_with_numbering(doc, "1. INTRODUCTION", level=1)
    
    intro_text = (
        "Le présent document synthétise les observations et recommandations issues de nos travaux "
        "de révision des comptes et d'évaluation du contrôle interne comptable. "
        "Ces travaux ont été réalisés conformément aux normes professionnelles applicables "
        "et visent à identifier les ajustements comptables nécessaires ainsi que les améliorations "
        "à apporter au dispositif de contrôle interne."
    )
    add_formatted_paragraph(doc, intro_text)
    
    doc.add_paragraph()
    
    # === 2. OBSERVATIONS D'AUDIT (Recos Révision) ===
    add_heading_with_numbering(doc, "2. OBSERVATIONS D'AUDIT", level=1)
    
    if len(request.recos_revision_points) == 0:
        add_formatted_paragraph(doc, "Aucune observation d'audit sur la révision des comptes.", italic=True)
    else:
        intro_obs = (
            f"Nos travaux de révision des comptes ont permis d'identifier {len(request.recos_revision_points)} "
            f"point(s) nécessitant des ajustements ou reclassements comptables."
        )
        add_formatted_paragraph(doc, intro_obs)
        doc.add_paragraph()
        
        for idx, point in enumerate(request.recos_revision_points, 1):
            # Titre du point
            add_heading_with_numbering(doc, f"2.{idx}. {point.intitule}", level=2)
            
            # Référence si disponible
            if point.metadata.reference:
                add_formatted_paragraph(doc, f"Référence: {point.metadata.reference}", italic=True)
            
            # Description
            if point.description:
                add_section_content(doc, "Description", point.description)
            
            # Observation
            if point.observation:
                add_section_content(doc, "Observation", point.observation)
            
            # Ajustement proposé
            if point.ajustement:
                add_section_content(doc, "Ajustement proposé", point.ajustement)
            
            # Régularisation comptable
            if point.regularisation:
                add_section_content(doc, "Régularisation comptable", point.regularisation)
            
            doc.add_paragraph()
    
    doc.add_paragraph()
    
    # === 3. POINTS DE CONTRÔLE INTERNE ===
    add_heading_with_numbering(doc, "3. POINTS DE CONTRÔLE INTERNE", level=1)
    
    # Combiner FRAP et Recos Contrôle Interne
    all_ci_points = []
    
    # Ajouter les FRAP
    for frap in request.frap_points:
        all_ci_points.append({
            'type': 'FRAP',
            'metadata': frap.metadata,
            'intitule': frap.intitule,
            'observation': frap.observation,
            'constat': frap.constat,
            'risque': frap.risque,
            'recommandation': frap.recommandation
        })
    
    # Ajouter les Recos Contrôle Interne
    for reco in request.recos_controle_interne_points:
        all_ci_points.append({
            'type': 'Recos CI',
            'metadata': reco.metadata,
            'intitule': reco.intitule,
            'observation': reco.observation,
            'constat': reco.constat,
            'risque': reco.risque,
            'recommandation': reco.recommandation
        })
    
    if len(all_ci_points) == 0:
        add_formatted_paragraph(doc, "Aucun point de contrôle interne identifié.", italic=True)
    else:
        intro_ci = (
            f"Notre évaluation du contrôle interne comptable a permis d'identifier {len(all_ci_points)} "
            f"point(s) nécessitant une attention particulière et des actions correctives."
        )
        add_formatted_paragraph(doc, intro_ci)
        doc.add_paragraph()
        
        for idx, point in enumerate(all_ci_points, 1):
            # Titre du point
            add_heading_with_numbering(doc, f"3.{idx}. {point['intitule']}", level=2)
            
            # Référence si disponible
            if point['metadata'].reference:
                add_formatted_paragraph(doc, f"Référence: {point['metadata'].reference}", italic=True)
            
            # Type de point
            add_formatted_paragraph(doc, f"Type: {point['type']}", italic=True)
            
            # Observation
            if point.get('observation'):
                add_section_content(doc, "Observation", point['observation'])
            
            # Constat
            if point.get('constat'):
                add_section_content(doc, "Constat", point['constat'])
            
            # Risques
            if point.get('risque'):
                add_section_content(doc, "Risques identifiés", point['risque'])
            
            # Recommandation
            if point.get('recommandation'):
                add_section_content(doc, "Recommandation", point['recommandation'])
            
            doc.add_paragraph()
    
    # === CONCLUSION ===
    doc.add_paragraph()
    add_heading_with_numbering(doc, "4. CONCLUSION", level=1)
    
    total_points = len(request.recos_revision_points) + len(all_ci_points)
    conclusion_text = (
        f"Au total, {total_points} point(s) ont été identifié(s) lors de nos travaux. "
        "Nous recommandons à la Direction de mettre en œuvre les ajustements comptables "
        "et les actions correctives proposées dans les meilleurs délais. "
        "Nous restons à votre disposition pour tout complément d'information."
    )
    add_formatted_paragraph(doc, conclusion_text)
    
    # Sauvegarder dans un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer


# === ENDPOINT API ===

@router.post("/export-synthese-cac")
async def export_synthese_cac(request: SyntheseCAC_Request):
    """
    Exporter une synthèse CAC en document Word structuré
    
    Collecte:
    - Points FRAP (contrôle interne opérationnel)
    - Points Recos Révision des Comptes
    - Points Recos Contrôle Interne Comptable
    
    Génère un rapport structuré au format CAC/Expert-Comptable
    """
    try:
        total_points = (
            len(request.frap_points) + 
            len(request.recos_revision_points) + 
            len(request.recos_controle_interne_points)
        )
        
        logger.info(f"📊 Export Synthèse CAC: {total_points} points au total")
        logger.info(f"   - FRAP: {len(request.frap_points)}")
        logger.info(f"   - Recos Révision: {len(request.recos_revision_points)}")
        logger.info(f"   - Recos CI: {len(request.recos_controle_interne_points)}")
        
        # Créer le document
        doc_buffer = create_synthese_cac_document(request)
        
        # Générer le nom de fichier
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"synthese_cac_{timestamp}.docx"
        
        # Retourner le fichier
        return Response(
            content=doc_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Erreur export synthèse CAC: {e}")
        raise HTTPException(status_code=500, detail=str(e))
