from main.models import StudentProfile, Marks,   SeatAllocation, Notification
from .models import Branch
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import FileResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from django.conf import settings
def rank_and_allocate():
    approved_students = StudentProfile.objects.filter(verification_status="Approved")
    print("Approved students count:", approved_students.count())

    student_scores = []

    for student in approved_students:
        try:
            marks = Marks.objects.get(student=student)
            print(" marks found for:", student.user.username)
        except Marks.DoesNotExist:
            print("No marks found for:", student.user.username)
            continue

        # Calculate weighted score
        pcm = marks.plus2_physics + marks.plus2_chemistry + marks.plus2_math
        pcm_percent = (pcm / 300) * 100
        print("pcm_percent:", pcm_percent)
        tenth_total = (
            marks.highschool_math +
            marks.highschool_science +
            marks.highschool_social_science +
            marks.highschool_english +
            marks.highschool_hindi
        )
        tenth_percent = (tenth_total / 500) * 100
        print("pcm_percent:", tenth_percent)
        rank_score = (0.7 * pcm_percent) + (0.3 * tenth_percent)
        print("rank score:", rank_score)
        student_scores.append((rank_score, student))

    # Sort students by rank score (high to low)
    sorted_students = [student for _, student in sorted(student_scores, key=lambda x: x[0], reverse=True)]
    print("studentsorted:", sorted_students)
         # Clear previous allocations
    SeatAllocation.objects.all().delete()

    for rank, student in enumerate(sorted_students, start=1):
          preferences = [student.branch1, student.branch2]
          print(f"\n➡️ Checking preferences for: {student.user.username} (Rank: {rank})")
          for branch_name in preferences:
              print(f"🔍 Trying branch: {branch_name}")

              try:
                branch = Branch.objects.get(name=branch_name)
                print(f"✅ Branch found: {branch.name}, filled: {branch.filled_seats}/{branch.total_seats}")

 
                if branch.filled_seats < branch.total_seats:
            
                # Assign branch to student profile
                    student.rank = rank
                    student.branch_allotted  = branch.name
                    student.seat_allocated = True
                    student.notification_seen = False
                    student.save()
            
                    branch.filled_seats += 1
                    branch.save()

                # Create seat allocation record
                    SeatAllocation.objects.create(
                     student=student,
                     rank=rank,
                     allocated_branch=branch
                  )
           
                    print(f"✅ {student.user.username} allocated to {branch.name} with rank {rank}")
                    break  # Stop checking next preferences

              except Branch.DoesNotExist:
                print(f"⛔ Branch not found: {branch_name}")
                continue  # Skip if branch doesn't exist



def send_allocation_notifications():
    all_students = StudentProfile.objects.filter(verification_status="Approved")
    for student in all_students:
        try:
            allocation = SeatAllocation.objects.get(student=student)
            Notification.objects.create(
                student=student.user,
                message=f"🎉 You have been allocated a seat in {allocation.allocated_branch}.kindly upload your paymet receipt for confirmation"
            )
        except SeatAllocation.DoesNotExist:
            Notification.objects.create(
                student=student.user,
                message="❌ You have not been allocated any seat."
            )




# def generate_offer_letter(student):
#     buffer=BytesIO()
#     p=canvas.Canvas(buffer,pagesize=A4)

#     p.setFont("Helvetica-Bold", 16)
#     p.drawString(200, 800, "🎓 Offer Letter")

#     p.setFont("Helvetica", 12)
    
#     p.drawString(50, 750, f"Name: {student.full_name}")
#     p.drawString(50, 730, f"Email: {student.profile_email}")
#     p.drawString(50, 710, f"Branch Allotted: {student.branch_allotted}")
#     p.drawString(50, 690, f"Rank: {student.rank}")
#     p.drawString(50, 650, "🎉 Congratulations! You have been allotted a seat.")
#     p.drawString(50, 630, "Please report to college with your documents.")

#     p.drawString(50, 100, "Signed,")
#     p.drawString(50, 80, "Admission Office")

#     p.showPage()
#     p.save()
#     buffer.seek(0)

#     return FileResponse(buffer, as_attachment=True, filename='Offer_Letter.pdf')

def generate_offer_letter(student):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    elements = []

    # -------- College Logo + Name --------

    try:
     logo_path = os.path.join(settings.BASE_DIR, "static", "images", "college_logo.png")
     if os.path.exists(logo_path):
        im = Image(logo_path, width=60, height=60)
     else:
        im = ""
    except:
     im = ""

    header_data = [
        [im, Paragraph(
            "<b><font size=16>ABC Institute of Technology</font></b><br/>"
            "<font size=12>Affiliated to XYZ University</font><br/>"
            "<font size=10>123 College Road, City, State - PIN</font>",
            getSampleStyleSheet()['Normal']
        )]
    ]
    header_table = Table(header_data, colWidths=[70, 400])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # -------- Title --------
    title_style = ParagraphStyle(name="Title", fontSize=16, alignment=TA_CENTER, spaceAfter=20)
    elements.append(Paragraph("🎓 <b>Offer Letter</b>", title_style))

    # -------- Student Info --------
    normal = getSampleStyleSheet()['Normal']
    student_info = (
        f"<b>Name:</b> {student.full_name}<br/>"
        f"<b>Email:</b> {student.profile_email}<br/>"
        f"<b>Branch Allotted:</b> {student.branch_allotted}<br/>"
        f"<b>Rank:</b> {student.rank}<br/>"
    )
    elements.append(Paragraph(student_info, normal))
    elements.append(Spacer(1, 20))

    # -------- Body --------
    body_style = ParagraphStyle(name="Body", fontSize=12, alignment=TA_LEFT, leading=16)
    body_text = (
        "Dear Candidate,<br/><br/>"
        "We are pleased to inform you that you have been <b>successfully allotted a seat</b> "
        f"in the <b>{student.branch_allotted}</b> branch at <b>ABC Institute of Technology</b>.<br/><br/>"
        "🎉 Congratulations on your achievement!<br/><br/>"
        "You are required to report to the Admissions Office with all original documents "
        "and certificates for verification within the stipulated timeline.<br/><br/>"
        "Failure to report within the mentioned time frame may result in cancellation of your admission."
    )
    elements.append(Paragraph(body_text, body_style))
    elements.append(Spacer(1, 40))

    # -------- Signature --------
    elements.append(Paragraph("Sincerely,", normal))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>Admissions Office</b><br/>ABC Institute of Technology", normal))

    # -------- Build PDF --------
    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="Offer_Letter.pdf")