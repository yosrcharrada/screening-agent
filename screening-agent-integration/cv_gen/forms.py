from django import forms
from .models import CVDocument, WorkExperience, Education, Skill

class PersonalInfoForm(forms.ModelForm):
    """Form for personal information"""
    
    class Meta:
        model = CVDocument
        fields = [
            'full_name',
            'email',
            'phone',
            'location',
            'professional_headline',
            'professional_summary'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State'
            }),
            'professional_headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Python Developer'
            }),
            'professional_summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Optional: Brief summary of your career'
            }),
        }

class WorkExperienceForm(forms.ModelForm):
    """Form for work experience"""
    
    class Meta:
        model = WorkExperience
        fields = [
            'job_title',
            'company_name',
            'location',
            'start_date',
            'end_date',
            'is_current',
            'job_description',
            'achievements',
            'technologies'
        ]
        widgets = {
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job Title'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country',
                'required': False
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': False
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'job_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of your role and responsibilities'
            }),
            'achievements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Key achievements and accomplishments (one per line)'
            }),
            'technologies': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technologies used (comma-separated)'
            }),
        }

class EducationForm(forms.ModelForm):
    """Form for education"""
    
    class Meta:
        model = Education
        fields = [
            'institution',
            'degree',
            'field_of_study',
            'graduation_date',
            'gpa',
            'honors',
            'relevant_coursework'
        ]
        widgets = {
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'University or School Name'
            }),
            'degree': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bachelor of Science'
            }),
            'field_of_study': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Field of Study'
            }),
            'graduation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gpa': forms.NumberInput(attrs={  # ✅ FIXED: Changed from DecimalInput to NumberInput
                'class': 'form-control',
                'placeholder': '3.8',
                'step': '0.01',
                'min': '0',
                'max': '4',
                'required': False
            }),
            'honors': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Cum Laude',
                'required': False
            }),
            'relevant_coursework': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Relevant coursework (optional)',
                'required': False
            }),
        }

class SkillForm(forms.ModelForm):
    """Form for individual skill"""
    
    class Meta:
        model = Skill
        fields = ['skill_name', 'category', 'proficiency_level']
        widgets = {
            'skill_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Skill name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'proficiency_level': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

class BulkSkillsForm(forms.Form):
    """Form for adding multiple skills at once"""
    
    technical_skills = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter technical skills (comma-separated)\ne.g., Python, Django, PostgreSQL'
        }),
        required=False,
        label='Technical Skills'
    )
    
    soft_skills = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter soft skills (comma-separated)\ne.g., Leadership, Communication'
        }),
        required=False,
        label='Soft Skills'
    )
    
    languages = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Languages (comma-separated)',
        }),
        required=False,
        label='Languages'
    )
    
    certifications = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Certifications (comma-separated)',
        }),
        required=False,
        label='Certifications'
    )