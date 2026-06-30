from backend.services.resume_parser import parse_resume_file


file_path = "sample_resume.pdf"

with open(file_path, "rb") as file:
    file_bytes = file.read()

text = parse_resume_file(file_path, file_bytes)

print("Extracted text preview:")
print(text[:1000])