
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import pytesseract, io, re, json
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine("sqlite:///./notas.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Nota(Base):
    __tablename__ = "notas"
    id = Column(Integer, primary_key=True)
    descricao = Column(String)
    evento = Column(String)
    centro = Column(String)

Base.metadata.create_all(bind=engine)

MEMORY_FILE = "ia_memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def aprender(descricao, evento, centro):
    mem = load_memory()
    mem[descricao[:50]] = {"evento": evento, "centro": centro}
    save_memory(mem)

def prever(descricao):
    mem = load_memory()
    for k in mem:
        if k.lower() in descricao.lower():
            return mem[k]
    return None

def extrair_texto(contents):
    try:
        img = Image.open(io.BytesIO(contents))
        return pytesseract.image_to_string(img)
    except:
        return ""

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    texto = extrair_texto(contents)

    pred = prever(texto)

    if pred:
        evento = pred["evento"]
        centro = pred["centro"]
    else:
        evento = "2070"
        centro = "01.01"

    db = SessionLocal()
    db.add(Nota(descricao=texto[:100], evento=evento, centro=centro))
    db.commit()
    db.close()

    return {"texto": texto[:300], "evento": evento, "centro": centro}

@app.post("/aprender")
def aprender_api(data: dict):
    aprender(data["descricao"], data["evento"], data["centro"])
    return {"status": "ok"}
