import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.db.session import SessionLocal
from app.models.document import Document
from app.services.document_service import document_service

db = SessionLocal()
d = db.query(Document).filter(Document.file_name.like('%BHYT%')).first()
if d:
    print('Processing BHYT document:', d.id, d.file_name)
    try:
        document_service.process_and_chunk_document(db, d.id)
        print('Success! Total chunks:', d.total_chunks, 'Status:', d.status)
    except Exception as e:
        print('Error processing BHYT:', e)
db.close()
