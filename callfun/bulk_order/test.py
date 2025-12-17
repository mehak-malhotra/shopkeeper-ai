import easyocr
reader = easyocr.Reader(['en', 'hi'])
result = reader.readtext('testimage.jpg', detail=0)
text = "\n".join(result)
print(text)