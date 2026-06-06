import sys

try:
    import pypdf
    print("pypdf is installed! Version:", pypdf.__version__)
    
    reader = pypdf.PdfReader("data/annual report pdf.pdf")
    print(f"Number of pages in PDF: {len(reader.pages)}")
    
    # Try extracting text from the first page
    first_page_text = reader.pages[0].extract_text()
    print("\n--- FIRST PAGE TEXT ---")
    print(first_page_text[:1000])
except Exception as e:
    print("Error:", e)
