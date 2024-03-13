from django.shortcuts import render
from docx import Document
from .forms import ResumeForm
from .models import Resume
from openai import OpenAI
import fitz
from django.conf import settings
from django.utils.html import linebreaks, mark_safe
from .serializers import PDFSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

OPENAI_API_KEY = settings.SECRET_KEY

def home(request):
    review_feedback = None

    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_by = request.POST.get('uploaded_by')
            uploaded_file = request.FILES['resume_file']
            file_extension = uploaded_file.name.split('.')[-1]
            
            new_resume = Resume(uploaded_by=uploaded_by, resume_file=uploaded_file)
            new_resume.save()

            if file_extension == 'pdf':
                text_content = extract_pdf_text(new_resume.resume_file.path)
            elif file_extension == 'docx':
                text_content = extract_docx_text(new_resume.resume_file.path)
            else:
                text_content = "Unsupported file type"

            if text_content and text_content != "Unsupported file type":
                review_feedback = review_resume(text_content)

    else:
        form = ResumeForm()

    return render(request, 'home.html', {'form': form, 'review_feedback': review_feedback})

def extract_pdf_text(file_path):
    text_content = ""
    try:
        pdf_file = fitz.open(file_path)
        for page_num in range(pdf_file.page_count):
            page = pdf_file[page_num]
            text_content += page.get_text()
        pdf_file.close()
    except Exception as e:
        print(f"Error extracting PDF content: {str(e)}")
        return None
    return text_content

def extract_docx_text(file_path):
    text_content = ""
    try:
        docx_document = Document(file_path)
        for paragraph in docx_document.paragraphs:
            text_content += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting DOCX content: {str(e)}")
        return None
    return text_content

def review_resume(resume_text):
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
            Please review the attached resume based on the following criteria. Provide feedback and assign scores for each aspect. Finally, calculate an overall score out of 100.

            Here's the resume to review "{resume_text}"

            First of all check the given file is resume or not. If it don't look like an resume simple tell "uploaded document is not an resume. And,
            if the document is a resume then follow this criteria.

            Criteria for Assessment:
            Grammar and Spelling:
            Review for typos, grammatical errors, and misspellings.
            Consistency and Formatting:
            Evaluate the consistency in font styles, sizes, spacing, and alignment.
            Look for uniformity in the use of bullet points, headings, and overall formatting.
            Clarity and Conciseness:
            Assess whether the information is presented clearly and concisely.
            Consider the use of bullet points, paragraph lengths, and organization of content.
            Professionalism:
            Evaluate the overall professional appearance of the resume.
            Check for a professional email address, appropriate contact information, and the tone of language used.
            Overall Assessment:
            Total Score: Sum of scores from the above criteria.
            Overall Score (out of 100): Convert the total score to a percentage out of 100.
            Feedback:
            Please provide specific feedback for each aspect and any additional comments on strengths and areas for improvement.
            """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Please review the attached resume."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=500
    )
    content = None
    if response.choices and len(response.choices) > 0:
        content = response.choices[0].message.content

    if content:
        formatted_content = mark_safe(linebreaks(content))
        return formatted_content
    else:
        return "No review feedback available"
    
@api_view(['POST'])
def upload_pdf(request):
    serializer = PDFSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        # Extract text content from the uploaded PDF
        uploaded_pdf = serializer.instance
        file_extension = uploaded_pdf.resume_file.name.split('.')[-1]
        if file_extension == 'pdf':
            text_content = extract_pdf_text(uploaded_pdf.resume_file.path)
        elif file_extension == 'docx':
            text_content = extract_docx_text(uploaded_pdf.resume_file.path)
        else:
            return Response({'error': 'Unsupported file type'}, status=status.HTTP_400_BAD_REQUEST)

        if text_content and text_content != "Unsupported file type":
            review_feedback = review_resume(text_content)
            if review_feedback:
                uploaded_pdf.review_feedback = review_feedback
                uploaded_pdf.save()
                return Response({'message': 'PDF uploaded and review feedback generated.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Failed to generate review feedback'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'Failed to extract text from the PDF'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    