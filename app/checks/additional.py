"""Deterministic checks added by TASK-004; no function decides risk level or gating."""
import re
from datetime import date,datetime
from difflib import SequenceMatcher


def normalise_name(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower()).replace("ptyltd", "")


def name_matches(value, registered_names):
    candidate=normalise_name(value)
    return bool(candidate) and any(SequenceMatcher(None,candidate,normalise_name(name)).ratio()>.72 for name in registered_names)


def suspicious_metadata(metadata):
    """Online rewriters are a review signal, never tamper proof by themselves."""
    text=" ".join(str(value).lower() for value in (metadata or {}).values())
    products=("ilovepdf","smallpdf","sejda","pdfescape")
    return next((product for product in products if product in text),None)


def parse_date(value):
    text=(value or "").strip()
    for pattern in ("%Y-%m-%d","%d/%m/%Y","%m/%d/%Y","%d %B %Y","%B %d, %Y"):
        try:return datetime.strptime(text,pattern).date()
        except ValueError:pass
    return None


def chronology(invoice,today=date(2026,11,17)):
    issued=parse_date(invoice.invoice_date);due=parse_date(invoice.due_date)
    if not issued:return 'unknown','Invoice issue date could not be parsed'
    if issued>today:return 'risk',f'Invoice is future-dated: {issued.isoformat()}'
    if due and due<issued:return 'risk','Due date is before the invoice issue date'
    if (today-issued).days>730:return 'risk',f'Invoice is unusually old: {issued.isoformat()}'
    return 'neutral','Invoice and due dates are chronologically plausible'


def relationship_state(customer,invoice):
    industry=(customer or {}).get('industry','').lower()
    supplier=invoice.supplier_name.lower()
    if industry=='landscaping':
        plausible=("landscap","irrigation","equipment","hire","mulch","soil","turf","nursery","stone","paver","fuel","machinery","accounting")
        implausible=("aviation","aerial survey","catering")
        if any(word in supplier for word in implausible):return 'risk','Supplier category is unusual for the customer’s landscaping profile'
        if any(word in supplier for word in plausible):return 'neutral','Supplier category is plausible for the customer’s landscaping profile'
    return 'unknown','Not checked: insufficient purchase-category history for relationship comparison'


def foreign_currency(text):
    match=re.search(r'\b(USD|EUR|GBP|NZD|JPY|CAD)\b',text or '',re.I)
    return match.group(1).upper() if match else None


def c5_invoice_fingerprint():
    """Real implementation compares exact SHA/layout hashes with a bank fraud corpus."""
    return 'needs a bank-wide fraud hash and layout-fingerprint corpus'

def c6_duplicate_invoice():
    """Real implementation queries paid invoice numbers and amounts for this supplier."""
    return 'needs paid-invoice history keyed by supplier and invoice number'

def c16_pdf_actions():
    """Real implementation parses raw PDF actions, annotations and launch dictionaries."""
    return 'needs raw PDF action and annotation objects from the forensic parser'

def c29_language_quality():
    """Real implementation uses a calibrated language model and measured false-positive limits."""
    return 'needs a calibrated language-quality model with false-positive controls'

def c32_au_registrant():
    """Real implementation queries authoritative .au registrant eligibility evidence."""
    return 'needs authoritative .au registrant eligibility data'

def c34_official_contacts():
    """Real implementation searches trusted sources and preserves URLs for human review."""
    return 'needs independently sourced official contact search evidence'

def c36_asic_status():
    """Real implementation refreshes and searches ASIC's published company-status dataset."""
    return 'needs a refreshed local ASIC company-status dataset'

def c37_logo_provenance():
    """Real implementation compares rendered logo features with a trusted supplier corpus."""
    return 'needs rendered logo extraction and a trusted supplier logo corpus'

def c38_render_ocr():
    """Real implementation renders pages in a sandbox and OCR-compares payment regions."""
    return 'needs a sandboxed page renderer and OCR comparison'

def c40_officeholders():
    """Real implementation uses authorised ASIC officeholder data and verified fraud links."""
    return 'needs authorised ASIC officeholder data and fraud-link evidence'

def c42_embedded_destinations():
    """Real implementation decodes QR/URI destinations without opening or following them."""
    return 'needs safe URI/QR extraction from raw PDF objects'

def c48_template_reuse():
    """Real implementation compares privacy-reviewed layout fingerprints across suppliers."""
    return 'needs a privacy-reviewed cross-supplier layout fingerprint corpus'

def c25_government_allowlist():
    """Real implementation matches government identities to a versioned official payment allowlist."""
    return 'needs an official government payment-details allowlist'

def c41_human_referral():
    """Real implementation opens an auditable known-number callback or fraud-team workflow."""
    return 'needs an authenticated human callback or fraud-team workflow'

def c52_bpay_consistency():
    """Real implementation uses bank-side BPAY biller identities and biller-specific CRN rules."""
    return 'needs bank-side BPAY biller identity and CRN rules'


SKELETON_CHECKS={
    'C5':c5_invoice_fingerprint,
    'C6':c6_duplicate_invoice,
    'C16':c16_pdf_actions,
    'C29':c29_language_quality,
    'C32':c32_au_registrant,
    'C34':c34_official_contacts,
    'C36':c36_asic_status,
    'C37':c37_logo_provenance,
    'C38':c38_render_ocr,
    'C40':c40_officeholders,
    'C42':c42_embedded_destinations,
    'C48':c48_template_reuse,
}
