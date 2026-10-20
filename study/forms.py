from pathlib import Path
from django import forms
from django.utils import timezone
from .models import Course
from .services import extract_text

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'exam_date', 'daily_minutes']
        widgets = {'exam_date': forms.DateInput(attrs={'type': 'date'})}

    def clean_exam_date(self):
        value = self.cleaned_data['exam_date']
        if value < timezone.localdate():
            raise forms.ValidationError('Choose today or a future exam date.')
        return value

class LectureForm(forms.Form):
    title = forms.CharField(max_length=200)
    file = forms.FileField(help_text='PDF or DOCX, up to 10 MB. Scanned PDFs need OCR first.')

    def clean_file(self):
        upload = self.cleaned_data['file']
        if upload.size > 10 * 1024 * 1024:
            raise forms.ValidationError('The file must be smaller than 10 MB.')
        if Path(upload.name).suffix.lower() not in {'.pdf', '.docx'}:
            raise forms.ValidationError('Please upload a PDF or DOCX file.')
        try:
            self.extracted_text = extract_text(upload)
        except Exception as exc:
            raise forms.ValidationError('Could not read this document. Use a valid, unencrypted PDF or DOCX with selectable text.') from exc
        if len(self.extracted_text.strip()) < 100:
            raise forms.ValidationError('The document needs at least 100 characters of selectable lecture text.')
        if len(self.extracted_text) > 60000:
            raise forms.ValidationError('Split this lecture into files with fewer than 60,000 characters each.')
        upload.seek(0)
        return upload
