from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    Enfant,
    Evaluation,
    Questionnaire,
    ReponseParent,
    Rubrique,
)


def home(request):
    rubriques = Rubrique.objects.prefetch_related("questions").all()
    total_enfants = Enfant.objects.count()
    total_evaluations = Evaluation.objects.count()

    context = {
        "rubriques": rubriques,
        "total_enfants": total_enfants,
        "total_evaluations": total_evaluations,
    }
    return render(request, "interaction/home.html", context)


def enfant_list(request):
    enfants = Enfant.objects.all()
    return render(request, "interaction/enfant_list.html", {"enfants": enfants})


def enfant_lookup(request):
    if request.method == "POST":
        code_enfant = request.POST.get("code_enfant", "").strip().upper()

        if not code_enfant:
            messages.error(request, "Veuillez saisir un code enfant.")
            return redirect("interaction:home")

        enfant = Enfant.objects.filter(code_enfant=code_enfant).first()
        if not enfant:
            messages.error(request, "Aucun enfant trouvé avec ce code.")
            return redirect("interaction:home")

        return redirect("interaction:enfant_detail", code_enfant=enfant.code_enfant)

    return redirect("interaction:home")


def enfant_create(request):
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        prenom = request.POST.get("prenom", "").strip()
        date_naissance = request.POST.get("date_naissance", "").strip()

        if not nom or not date_naissance:
            messages.error(request, "Le nom et la date de naissance sont obligatoires.")
            return render(
                request,
                "interaction/enfant_form.html",
                {"data": request.POST},
            )

        enfant = Enfant.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
        )

        messages.success(
            request,
            f"Enfant enregistré avec succès. Code à conserver : {enfant.code_enfant}"
        )
        return redirect("interaction:enfant_detail", code_enfant=enfant.code_enfant)

    return render(request, "interaction/enfant_form.html")


def enfant_detail(request, code_enfant):
    enfant = get_object_or_404(
        Enfant.objects.prefetch_related("evaluations"),
        code_enfant=code_enfant
    )
    rubriques = Rubrique.objects.prefetch_related("questions").all()
    evaluations = enfant.evaluations.all()
    derniere_evaluation = evaluations.first()

    context = {
        "enfant": enfant,
        "rubriques": rubriques,
        "evaluations": evaluations,
        "derniere_evaluation": derniere_evaluation,
    }
    return render(request, "interaction/enfant_detail.html", context)


def evaluation_create(request, code_enfant, rubrique_id):
    enfant = get_object_or_404(Enfant, code_enfant=code_enfant)
    rubrique = get_object_or_404(
        Rubrique.objects.prefetch_related("questions"),
        id=rubrique_id
    )
    questions = rubrique.questions.all()

    reponse_choices = [
        ("oui", "Oui"),
        ("parfois", "Parfois"),
        ("non", "Non"),
    ]

    if not questions.exists():
        messages.error(request, "Cette rubrique ne contient pas encore de questions.")
        return redirect("interaction:enfant_detail", code_enfant=enfant.code_enfant)

    if request.method == "POST":
        commentaire = request.POST.get("commentaire", "").strip()
        erreurs = []

        for question in questions:
            valeur = request.POST.get(f"question_{question.id}")
            if not valeur:
                erreurs.append(f"La question « {question.question} » n'a pas de réponse.")

        if erreurs:
            for erreur in erreurs:
                messages.error(request, erreur)

            context = {
                "enfant": enfant,
                "rubrique": rubrique,
                "questions": questions,
                "reponse_choices": reponse_choices,
                "data": request.POST,
            }
            return render(request, "interaction/evaluation_form.html", context)

        with transaction.atomic():
            evaluation = Evaluation.objects.create(
                enfant=enfant,
                commentaire=commentaire,
                terminee=True,
            )

            for question in questions:
                valeur = request.POST.get(f"question_{question.id}")

                ReponseParent.objects.create(
                    evaluation=evaluation,
                    question=question,
                    reponse=valeur,
                )

        messages.success(request, "Évaluation enregistrée avec succès.")
        return redirect("interaction:evaluation_result", evaluation_id=evaluation.id)

    context = {
        "enfant": enfant,
        "rubrique": rubrique,
        "questions": questions,
        "reponse_choices": reponse_choices,
    }
    return render(request, "interaction/evaluation_form.html", context)


def evaluation_result(request, evaluation_id):
    evaluation = get_object_or_404(
        Evaluation.objects.select_related("enfant"),
        id=evaluation_id
    )

    interpretation_globale = evaluation.interpretation_globale()

    context = {
        "evaluation": evaluation,
        "score_total": evaluation.score_total(),
        "score_maximum": evaluation.score_maximum(),
        "pourcentage": evaluation.pourcentage_score(),
        "interpretations": evaluation.interpretation_par_rubrique(),
        "interpretation_globale": interpretation_globale,
    }
    return render(request, "interaction/evaluation_result.html", context)