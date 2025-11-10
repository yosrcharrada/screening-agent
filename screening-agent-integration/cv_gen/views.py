import textwrap
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q
from django.contrib import messages
from datetime import date
from io import BytesIO
import os
import subprocess
import tempfile
import shutil
from django.conf import settings
from django.template.loader import render_to_string

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from .models import CVDocument, Skill, WorkExperience, Education
from .services.generation_service import CVGenerationService

def call_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama2",
            "prompt": prompt,
            "stream": False
        }
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()

def home(request):
    try:
        user_cvs = 0
        if request.user.is_authenticated:
            user_cvs = CVDocument.objects.filter(user=request.user).count()
        context = {'user_cvs': user_cvs}
        return render(request, 'cv_gen/home.html', context)
    except Exception as e:
        return render(request, 'cv_gen/home.html', {'error': str(e)})

def signup(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            if not username or not email or not password1 or not password2:
                messages.error(request, "❌ All fields are required!")
                return render(request, 'cv_gen/signup.html')
            if len(password1) < 6:
                messages.error(request, "❌ Password must be at least 6 characters!")
                return render(request, 'cv_gen/signup.html')
            if password1 != password2:
                messages.error(request, "❌ Passwords don't match!")
                return render(request, 'cv_gen/signup.html')
            if User.objects.filter(username=username).exists():
                messages.error(request, "❌ Username already taken!")
                return render(request, 'cv_gen/signup.html')
            if User.objects.filter(email=email).exists():
                messages.error(request, "❌ Email already registered!")
                return render(request, 'cv_gen/signup.html')
            user = User.objects.create_user(username=username, email=email, password=password1)
            messages.success(request, "✅ Account created successfully! Please login.")
            return redirect('login')
        return render(request, 'cv_gen/signup.html')
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
        return render(request, 'cv_gen/signup.html', {'error': str(e)})

@login_required
def cv_list(request):
    try:
        cvs = CVDocument.objects.filter(user=request.user).order_by('-created_at')
        context = {
            'cvs': cvs,
            'total_cvs': cvs.count(),
            'generated_cvs': cvs.filter(is_generated=True).count(),
        }
        return render(request, 'cv_gen/cv_list.html', context)
    except Exception as e:
        messages.error(request, "Error loading CVs")
        return render(request, 'cv_gen/cv_list.html', {'error': str(e)})

@login_required
def cv_create(request):
    try:
        if request.method == 'POST':
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            professional_headline = request.POST.get('professional_headline')
            profession = request.POST.get('profession', 'General')
            professional_summary = request.POST.get('professional_summary', '')
            skills_text = request.POST.get('skills', '')
            cv = CVDocument.objects.create(
                user=request.user,
                full_name=full_name,
                email=email,
                phone=phone,
                location=location,
                professional_headline=professional_headline,
                profession=profession,
                professional_summary=professional_summary,
            )
            if skills_text:
                for skill in skills_text.split(','):
                    skill = skill.strip()
                    if skill:
                        Skill.objects.create(
                            cv_document=cv,
                            skill_name=skill,
                            proficiency_level='Intermediate'
                        )
            experiences_json = request.POST.get('experiences', '')
            if experiences_json:
                try:
                    experiences = json.loads(experiences_json)
                    experiences.sort(key=lambda x: x.get('start_date', ''), reverse=True)
                    for exp in experiences:
                        if exp['job_title'] or exp['company_name']:
                            WorkExperience.objects.create(
                                cv_document=cv,
                                job_title=exp['job_title'],
                                company_name=exp['company_name'],
                                location=exp['location'],
                                start_date=exp['start_date'] or None,
                                end_date=exp['end_date'] or None,
                                job_description=exp['job_description'],
                                generated_bullets=exp['job_description'],
                            )
                except Exception as err:
                    pass
            try:
                CVGenerationService().generate_complete_cv(cv)
            except Exception as e:
                pass
            messages.success(request, f"✅ CV '{full_name}' created successfully!")
            return redirect('cv_gen:cv_preview', cv_id=cv.id)
        professions = CVDocument.PROFESSION_CHOICES
        return render(request, 'cv_gen/cv_form.html', {
            'professions': professions,
            'cv': None
        })
    except Exception as e:
        messages.error(request, f"Error creating CV: {str(e)}")
        return render(request, 'cv_gen/cv_form.html', {'error': str(e)})

@login_required
def cv_edit(request, cv_id):
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        if request.method == 'POST':
            cv.full_name = request.POST.get('full_name', cv.full_name)
            cv.email = request.POST.get('email', cv.email)
            cv.phone = request.POST.get('phone', cv.phone)
            cv.location = request.POST.get('location', cv.location)
            cv.professional_headline = request.POST.get('professional_headline', cv.professional_headline)
            cv.profession = request.POST.get('profession', cv.profession)
            cv.professional_summary = request.POST.get('professional_summary', cv.professional_summary)
            cv.save()
            skills_text = request.POST.get('skills', '')
            cv.skills.all().delete()
            if skills_text:
                for skill in skills_text.split(','):
                    skill = skill.strip()
                    if skill:
                        Skill.objects.create(
                            cv_document=cv,
                            skill_name=skill,
                            proficiency_level='Intermediate'
                        )
            experiences_json = request.POST.get('experiences', '')
            cv.work_experiences.all().delete()
            if experiences_json:
                try:
                    experiences = json.loads(experiences_json)
                    experiences.sort(key=lambda x: x.get('start_date', ''), reverse=True)
                    for exp in experiences:
                        if exp['job_title'] or exp['company_name']:
                            WorkExperience.objects.create(
                                cv_document=cv,
                                job_title=exp['job_title'],
                                company_name=exp['company_name'],
                                location=exp['location'],
                                start_date=exp['start_date'] or None,
                                end_date=exp['end_date'] or None,
                                job_description=exp['job_description'],
                                generated_bullets=exp['job_description'],
                            )
                except Exception as err:
                    pass
            messages.success(request, "✅ CV updated successfully!")
            return redirect('cv_gen:cv_preview', cv_id=cv.id)
        context = {
            'cv': cv,
            'professions': CVDocument.PROFESSION_CHOICES,
        }
        return render(request, 'cv_gen/cv_form.html', context)
    except Exception as e:
        messages.error(request, "Error updating CV")
        return render(request, 'cv_gen/cv_form.html', {'error': str(e)})

@login_required
@require_POST
def ai_experience_summary(request):
    try:
        data = json.loads(request.body)
        job_title = data.get("job_title", "")
        company = data.get("company", "")
        location = data.get("location", "")
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        details = data.get("details", "")

        prompt = f"""
Generate 2-5 strong bullet points suitable for a CV (not a project description or company announcement).
Each bullet should:
- Start with an action verb
- Focus on what the candidate actually did and accomplished
- Include quantifiable, measurable results if given
- Do NOT mention project dates, the company's announcement, or general company marketing
- Do NOT use 'we', 'our', or company-first phrasing—write as for an individual's CV.

Role: {job_title}
Company: {company}
Location: {location}
Time: {start_date} to {end_date}
Details: {details}
"""

        generated = call_ollama(prompt)
        return JsonResponse({"generated": generated})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def cv_preview(request, cv_id):
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        if request.method == 'POST' and request.POST.get('action') == 'generate':
            try:
                CVGenerationService().generate_complete_cv(cv)
                messages.success(request, "✅ AI-powered content generated!")
                cv.refresh_from_db()
            except Exception as e:
                messages.error(request, f"❌ AI generation failed: {e}")
        skills = cv.skills.all()
        work_experiences = []
        for exp in cv.work_experiences.order_by('-start_date'):
            # Always populate bullet_list from generated_bullets, fallback to job_description
            if exp.generated_bullets:
                exp.bullets_list = exp.generated_bullets.split("\n")
            elif exp.job_description:
                exp.bullets_list = exp.job_description.split("\n")
            else:
                exp.bullets_list = []
            work_experiences.append(exp)
        education = cv.education.all()
        context = {
            'cv': cv,
            'skills': skills,
            'work_experiences': work_experiences,
            'education': education,
            'generated_content': cv.generated_cv_content,
            'is_generated': cv.is_generated,
        }
        return render(request, 'cv_gen/cv_preview.html', context)
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('cv_gen:cv_list')

@login_required
def cv_download(request, cv_id):
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 0.5 * inch
        c.setFont("Helvetica-Bold", 24)
        c.drawString(0.5 * inch, y, cv.full_name)
        y -= 0.3 * inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.5 * inch, y, cv.professional_headline)
        y -= 0.2 * inch
        c.setFont("Helvetica", 10)
        contact_info = []
        if cv.email:
            contact_info.append(cv.email)
        if cv.phone:
            contact_info.append(cv.phone)
        if cv.location:
            contact_info.append(cv.location)
        contact_text = " | ".join(contact_info)
        c.drawString(0.5 * inch, y, contact_text)
        y -= 0.3 * inch
        if cv.generated_summary:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(0.5 * inch, y, "Professional Summary")
            y -= 0.2 * inch
            c.setFont("Helvetica", 10)
            summary_lines = cv.generated_summary.split('\n')
            for line in summary_lines[:8]:
                if line.strip():
                    wrapped_lines = textwrap.wrap(line.strip(), width=85)
                    for wrapped_line in wrapped_lines:
                        if y < 0.5 * inch:
                            c.showPage()
                            y = height - 0.5 * inch
                        c.drawString(0.5 * inch, y, wrapped_line)
                        y -= 0.15 * inch
            y -= 0.15 * inch
        if cv.work_experiences.exists():
            c.setFont("Helvetica-Bold", 12)
            c.drawString(0.5 * inch, y, "Work Experience")
            y -= 0.2 * inch
            for exp in cv.work_experiences.order_by('-start_date')[:5]:
                c.setFont("Helvetica-Bold", 10)
                job_info = f"{exp.job_title}"
                if exp.company_name:
                    job_info += f" - {exp.company_name}"
                if y < 0.7 * inch:
                    c.showPage()
                    y = height - 0.5 * inch
                c.drawString(0.5 * inch, y, job_info)
                y -= 0.15 * inch
                c.setFont("Helvetica", 9)
                if exp.start_date:
                    date_str = f"{exp.start_date.strftime('%b %Y')} - "
                    if getattr(exp, "is_current", False):
                        date_str += "Present"
                    elif exp.end_date:
                        date_str += exp.end_date.strftime('%b %Y')
                    c.drawString(0.7 * inch, y, date_str)
                    y -= 0.12 * inch
                if hasattr(exp, "generated_bullets") and exp.generated_bullets:
                    c.setFont("Helvetica", 9)
                    bullets = exp.generated_bullets.split('\n')[:4]
                    for bullet in bullets:
                        if bullet.strip():
                            wrapped = textwrap.wrap(bullet.strip(), width=80)
                            for line in wrapped:
                                if y < 0.5 * inch:
                                    c.showPage()
                                    y = height - 0.5 * inch
                                c.drawString(0.7 * inch, y, f"• {line}")
                                y -= 0.12 * inch
                y -= 0.1 * inch
        if y < 1.0 * inch:
            c.showPage()
            y = height - 0.5 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.5 * inch, y, "Skills")
        y -= 0.2 * inch
        c.setFont("Helvetica", 10)
        skills = list(cv.skills.all())
        if skills:
            for skill in skills:
                if y < 0.5 * inch:
                    c.showPage()
                    y = height - 0.5 * inch
                c.drawString(0.5 * inch, y, f"• {skill.skill_name}")
                y -= 0.15 * inch
        else:
            c.drawString(0.5 * inch, y, "No skills listed.")
            y -= 0.15 * inch
        c.save()
        buffer.seek(0)
        response = FileResponse(buffer, content_type='application/pdf')
        filename = f"{cv.full_name.replace(' ', '_')}_CV.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error downloading PDF: {str(e)}")
        return redirect('cv_gen:cv_preview', cv_id=cv_id)

@login_required
def cv_download_latex(request, cv_id):
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        skills = cv.skills.all()
        work_experiences = cv.work_experiences.order_by('-start_date')
        education = cv.education.all()
        latex_content = render_to_string('cv_gen/cv_latex_template.tex', {
            'cv': cv,
            'skills': skills,
            'work_experiences': work_experiences,
            'education': education,
        })
        response = HttpResponse(latex_content, content_type='application/x-latex')
        filename = f"{cv.full_name.replace(' ', '_')}_CV.tex"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error downloading LaTeX: {str(e)}")
        return redirect('cv_gen:cv_preview', cv_id=cv_id)

@login_required
def cv_delete(request, cv_id):
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        if request.method == 'POST':
            cv_name = cv.full_name
            cv.delete()
            messages.success(request, f"✅ CV '{cv_name}' deleted successfully!")
            return redirect('cv_gen:cv_list')
        return render(request, 'cv_gen/cv_confirm_delete.html', {'cv': cv})
    except Exception as e:
        messages.error(request, "Error deleting CV")
        return redirect('cv_gen:cv_list')

@login_required
@require_http_methods(["POST"])
def cv_feedback(request, cv_id):
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        section_type = request.POST.get('section_type')
        rating = int(request.POST.get('rating', 3))
        feedback_text = request.POST.get('feedback_text', '')
        suggested_improvement = request.POST.get('suggested_improvement', '')
        service = CVGenerationService()
        success = service.collect_user_feedback(
            cv,
            section_type,
            rating,
            feedback_text,
            suggested_improvement
        )
        return JsonResponse({
            'success': success,
            'message': '✅ Feedback saved! Thank you for helping us improve.' if success else '❌ Error saving feedback'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Error: {str(e)}'
        })

@login_required
def cv_download_latex_pdf(request, cv_id):
    cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
    skills = cv.skills.all()
    work_experiences = cv.work_experiences.order_by('-start_date')
    education = cv.education.all()
    latex_content = render_to_string(
        'cv_gen/cv_latex_template.tex',
        {'cv': cv, 'skills': skills, 'work_experiences': work_experiences, 'education': education}
    )
    with tempfile.TemporaryDirectory() as tempdir:
        tex_path = os.path.join(tempdir, "cv.tex")
        pdf_path = os.path.join(tempdir, "cv.pdf")
        cls_path = os.path.join(tempdir, "muratcan_cv.cls")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
        shutil.copy(os.path.join(settings.BASE_DIR, "muratcan_cv.cls"), cls_path)
        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "cv.tex"],
                cwd=tempdir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            return HttpResponse(f"LaTeX compilation error:<br><pre>{e.stderr.decode()}</pre>", status=500)
        with open(pdf_path, "rb") as f:
            response = FileResponse(f, content_type="application/pdf")
            filename = f"{cv.full_name.replace(' ', '_')}_CV.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response