# transcribe.py
import os
import sys
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('HANDWRITING_OCR_KEY')
BASE_URL = 'https://www.handwritingocr.com/api/v3'

def transcribe_document(file_path):
    """
    Upload a handwritten document and return the transcribed text.
    
    Args:
        file_path: Path to your PDF or image file
    
    Returns:
        str: The transcribed text
    """
    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"📄 Uploading {file_path}...")
    
    # Step 1: Upload the document
    with open(file_path, 'rb') as f:
        response = requests.post(
            f'{BASE_URL}/documents',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Accept': 'application/json'
            },
            files={'file': f},
            data={'action': 'transcribe'}
        )
    
    response.raise_for_status()
    
    doc_id = response.json()['id']
    print(f"✓ Document uploaded successfully!")
    print(f"  Document ID: {doc_id}")
    print(f"  Status: {response.json()['status']}")
    
    # Step 2: Poll for completion
    print("\n⏳ Processing document...")
    while True:
        status_response = requests.get(
            f'{BASE_URL}/documents/{doc_id}',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Accept': 'application/json'
            }
        )
        status_response.raise_for_status()
        
        doc_data = status_response.json()
        status = doc_data['status']
        
        if status == 'processed':
            print("✓ Processing complete!")
            break
        elif status == 'failed':
            raise Exception("OCR processing failed")
        
        print(f"  Status: {status}... checking again in 2 seconds")
        time.sleep(2)
    
    # Step 3: Download the transcribed text
    print("\n📥 Downloading transcription...")
    result = requests.get(
        f'{BASE_URL}/documents/{doc_id}.txt',
        headers={'Authorization': f'Bearer {API_KEY}'}
    )
    result.raise_for_status()
    
    print(f"✓ Success! Downloaded {len(result.text):,} characters")
    return result.text

def main():
    """Main entry point"""
    # Check for command line argument
    if len(sys.argv) != 2:
        print("Usage: python transcribe.py <file_path>")
        print("\nExample:")
        print("  python transcribe.py inspection_report.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Generate output filename (same name, .txt extension)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f'{base_name}_transcription.txt'
    
    try:
        # Transcribe the document
        text = transcribe_document(input_file)
        
        # Save the result
        with open(output_file, 'w') as f:
            f.write(text)
        
        # Show a preview
        print("\n" + "="*60)
        print("TRANSCRIBED TEXT (first 500 characters)")
        print("="*60)
        print(text[:500])
        if len(text) > 500:
            print("...")
        
        print(f"\n✓ Full transcription saved to {output_file}")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()