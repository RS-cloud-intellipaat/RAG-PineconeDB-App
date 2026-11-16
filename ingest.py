
from pathlib import Path
from uuid import uuid4

from openai.types import embedding

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from pypdf import PdfReader

from config import *

# Initialize OpenAI and Pinecone
client = OpenAI(api_key=OPENAI_API_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)


# Create Pinecone Index
if INDEX_NAME not in pc.list_indexes().names():

    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=PINECONE_CLOUD,
            region=PINECONE_REGION
        )
    )

# Connect to Pinecone Index
index = pc.Index(INDEX_NAME)


# Read PDF files
chunks = []

for pdf in Path("documents").glob("*.pdf"):

    reader = PdfReader(str(pdf))

    for page_no, page in enumerate(reader.pages, 1):

        text = page.extract_text()

        if text:
            chunks.append({
                "text": text,
                "source": pdf.name,
                "page": page_no
            })

for chunk in chunks:
    print(chunk)
    print("*"*50)

#Generated embedding and upload to Pinecone

for chunk in chunks:
    response = client.embeddings.create(
        model = EMBEDDING_MODEL,
        input = chunk["text"]
    )
    embedding = response.data[0].embedding

    index.upsert(
        vectors=[{
            "id": str(uuid4()),
            "values": embedding,
            "metadata": chunk
        }],
        namespace=NAMESPACE
    )

    print("Uploaded:", chunk["source"], "Page:", chunk["page"])

print("PDF ingestion completed successfully!")

