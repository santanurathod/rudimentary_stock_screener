import PyPDF2

def read_pdf(file_path):
    """
    Read a PDF file and print its contents.
    
    Args:
        file_path (str): Path to the PDF file
    """
    try:
        # Open the PDF file in binary read mode
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            print(f"Number of pages: {num_pages}")
            
            # Read each page
            for page_num in range(num_pages):
                # Get the page object
                page = pdf_reader.pages[page_num]
                
                # Extract text from the page
                text = page.extract_text()
                print(f"\nPage {page_num + 1}:")
                print(text)
                
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Example usage
    pdf_path = "path/to/your/pdf/file.pdf"  # Replace with your PDF file path
    read_pdf(pdf_path) 