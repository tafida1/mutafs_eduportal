import json

from django.conf import settings


def rule_based_academic_comment(*, student, insight):
    name = student.full_name

    remarks = []

    if insight["risk_level"] == "HIGH":
        remarks.append(
            f"{name} currently requires urgent academic attention. "
            "The student may benefit from close monitoring, extra lessons, and parental support."
        )
    elif insight["risk_level"] == "MEDIUM":
        remarks.append(
            f"{name} is making progress but still needs improvement in some academic areas."
        )
    else:
        remarks.append(
            f"{name} is performing steadily and should maintain consistent study habits."
        )

    if insight["weak_subjects"]:
        weak_names = ", ".join([item.subject.name for item in insight["weak_subjects"]])
        remarks.append(
            f"More attention should be given to: {weak_names}."
        )

    if insight["strong_subjects"]:
        strong_names = ", ".join([item.subject.name for item in insight["strong_subjects"]])
        remarks.append(
            f"The student shows strength in: {strong_names}."
        )

    if insight["attendance_percentage"] < 75:
        remarks.append(
            "Attendance is below the recommended level and should improve immediately."
        )

    if insight["cbt_average"] < 50:
        remarks.append(
            "CBT performance indicates the need for more practice and revision."
        )

    return " ".join(remarks)


def generate_ai_academic_comment(*, student, insight):
    if not settings.OPENAI_API_KEY:
        return rule_based_academic_comment(student=student, insight=insight)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        payload = {
            "student_name": student.full_name,
            "class": student.current_class.name if student.current_class else "",
            "average_score": str(insight["average_score"]),
            "attendance_percentage": str(insight["attendance_percentage"]),
            "cbt_average": str(insight["cbt_average"]),
            "risk_level": insight["risk_label"],
            "weak_subjects": [item.subject.name for item in insight["weak_subjects"]],
            "strong_subjects": [item.subject.name for item in insight["strong_subjects"]],
            "recommendations": insight["recommendations"],
        }

        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an experienced school academic adviser. "
                        "Write a professional, parent-friendly academic comment. "
                        "Be supportive, clear, concise, and practical. "
                        "Do not invent facts. Use only the supplied data."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(payload),
                },
            ],
        )

        return response.output_text.strip()

    except Exception:
        return rule_based_academic_comment(student=student, insight=insight)




def rule_based_teacher_assistant(*, task_type, subject, school_class, topic):
    topic = topic or "the selected topic"
    subject = subject or "the selected subject"
    school_class = school_class or "the selected class"

    if task_type == "LESSON_NOTE":
        return f"""
LESSON NOTE OUTLINE

Subject: {subject}
Class: {school_class}
Topic: {topic}

1. Introduction
Briefly introduce {topic} and explain why it is important.

2. Lesson Objectives
By the end of the lesson, students should be able to:
- Define the key concept in {topic}.
- Explain the major points.
- Solve or answer examples related to the topic.
- Apply the knowledge in real-life situations.

3. Previous Knowledge
Ask students what they already know about {topic}.

4. Teacher Presentation
Explain the topic step by step using simple examples.

5. Class Activity
Give students a short activity or group discussion.

6. Evaluation
Ask 3 to 5 questions to confirm understanding.

7. Assignment
Give students a short homework task on {topic}.
"""

    if task_type == "CBT_QUESTIONS":
        return f"""
CBT QUESTIONS

Subject: {subject}
Class: {school_class}
Topic: {topic}

1. Which of the following best describes {topic}?
A. Option A
B. Option B
C. Option C
D. Option D
Answer: A

2. One important fact about {topic} is:
A. Option A
B. Option B
C. Option C
D. Option D
Answer: B

3. {topic} is useful because:
A. Option A
B. Option B
C. Option C
D. Option D
Answer: C

Note: Please review and edit these placeholder options before using them in a real exam.
"""

    if task_type == "EXPLANATION":
        return f"""
SIMPLE EXPLANATION

{topic} in {subject} can be explained step by step to {school_class} students.

Start from the basic meaning, give one simple example, then allow students to ask questions.
Use diagrams, calculations, or real-life examples where necessary.
"""

    return f"""
TEACHER ASSISTANT OUTPUT

Subject: {subject}
Class: {school_class}
Topic: {topic}

Create a short teaching activity, examples, and evaluation questions for this topic.
"""


def generate_teacher_ai_content(*, task_type, subject, school_class, topic, extra_instruction=""):
    if not settings.OPENAI_API_KEY:
        return rule_based_teacher_assistant(
            task_type=task_type,
            subject=subject,
            school_class=school_class,
            topic=topic,
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""
Task Type: {task_type}
Subject: {subject}
Class: {school_class}
Topic: {topic}
Extra Instruction: {extra_instruction}

Generate professional school-ready content.

Rules:
- Use clear Nigerian secondary school-friendly language.
- Do not invent school-specific policies.
- For CBT questions, provide A-D options and indicate correct answer.
- For lesson notes, include objectives, previous knowledge, presentation, evaluation, and assignment.
- Keep the content structured and editable by the teacher.
"""

        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=prompt,
        )

        return response.output_text.strip()

    except Exception:
        return rule_based_teacher_assistant(
            task_type=task_type,
            subject=subject,
            school_class=school_class,
            topic=topic,
        )