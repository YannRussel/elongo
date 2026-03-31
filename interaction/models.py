import uuid
from datetime import date
from django.db import models


class Rubrique(models.Model):
    libelle = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.libelle

    class Meta:
        ordering = ['libelle']
        verbose_name = "Rubrique"
        verbose_name_plural = "Rubriques"


class Questionnaire(models.Model):
    rubrique = models.ForeignKey(
        Rubrique,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question = models.CharField(max_length=255)
    ordre = models.PositiveIntegerField(default=0)

    # Score propre à chaque question
    score_oui = models.IntegerField(default=2)
    score_parfois = models.IntegerField(default=1)
    score_non = models.IntegerField(default=0)

    def __str__(self):
        return self.question

    def get_score_for_response(self, response_value: str) -> int:
        mapping = {
            ReponseParent.OUI: self.score_oui,
            ReponseParent.PARFOIS: self.score_parfois,
            ReponseParent.NON: self.score_non,
        }
        return mapping.get(response_value, 0)

    def score_max_question(self) -> int:
        return max(self.score_oui, self.score_parfois, self.score_non)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Question"
        verbose_name_plural = "Questions"


class ChoixReponse(models.Model):
    """
    Conservé pour compatibilité si tu as déjà des données ou un admin existant.
    Cette table n'est plus utilisée par la nouvelle logique de scoring question par question.
    """
    libelle = models.CharField(max_length=20, unique=True)  # Oui / Non / Parfois
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.libelle} ({self.score})"

    class Meta:
        ordering = ['id']
        verbose_name = "Choix de réponse"
        verbose_name_plural = "Choix de réponse"


class Enfant(models.Model):
    code_enfant = models.CharField(max_length=20, unique=True, blank=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    date_naissance = models.DateField()

    def save(self, *args, **kwargs):
        if not self.code_enfant:
            code = f"ENF-{uuid.uuid4().hex[:8].upper()}"
            while Enfant.objects.filter(code_enfant=code).exists():
                code = f"ENF-{uuid.uuid4().hex[:8].upper()}"
            self.code_enfant = code
        super().save(*args, **kwargs)

    def __str__(self):
        nom_complet = f"{self.nom} {self.prenom or ''}".strip()
        return f"{nom_complet} - {self.code_enfant}"

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )

    def derniere_evaluation(self):
        return self.evaluations.first()

    class Meta:
        ordering = ['nom', 'prenom']
        verbose_name = "Enfant"
        verbose_name_plural = "Enfants"
        constraints = [
            models.UniqueConstraint(
                fields=['nom', 'prenom', 'date_naissance'],
                name='unique_enfant_identite'
            )
        ]


class Evaluation(models.Model):
    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    date_evaluation = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True, null=True)
    terminee = models.BooleanField(default=False)

    def __str__(self):
        return f"Évaluation de {self.enfant} - {self.date_evaluation.strftime('%d/%m/%Y %H:%M')}"

    def score_total(self):
        return sum(rep.score_obtenu for rep in self.reponses.select_related('question'))

    def score_maximum(self):
        return sum(
            rep.question.score_max_question()
            for rep in self.reponses.select_related('question')
        )

    def pourcentage_score(self):
        max_score = self.score_maximum()
        if max_score == 0:
            return 0
        return round((self.score_total() / max_score) * 100, 2)

    def score_par_rubrique(self):
        resultats = {}
        reponses = self.reponses.select_related('question__rubrique')

        for rep in reponses:
            rubrique = rep.question.rubrique.libelle
            resultats[rubrique] = resultats.get(rubrique, 0) + rep.score_obtenu

        return resultats

    def interpretation_par_rubrique(self):
        resultats = []
        scores = self.score_par_rubrique()

        for rubrique_libelle, score in scores.items():
            rubrique = Rubrique.objects.filter(libelle=rubrique_libelle).first()
            interpretation = None

            if rubrique:
                interpretation = rubrique.interpretations.filter(
                    score_min__lte=score,
                    score_max__gte=score
                ).first()

            resultats.append({
                'rubrique': rubrique_libelle,
                'score': score,
                'message': interpretation.message if interpretation else "Aucune interprétation définie pour cette rubrique."
            })

        return resultats

    def interpretation_globale(self):
        score = self.score_total()
        return InterpretationGlobale.objects.filter(
            score_min__lte=score,
            score_max__gte=score
        ).first()

    class Meta:
        ordering = ['-date_evaluation']
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"


class ReponseParent(models.Model):
    OUI = "oui"
    NON = "non"
    PARFOIS = "parfois"

    REPONSES = [
        (OUI, "Oui"),
        (NON, "Non"),
        (PARFOIS, "Parfois"),
    ]

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='reponses'
    )
    question = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='reponses_parents'
    )
    reponse = models.CharField(max_length=20, choices=REPONSES)
    score_obtenu = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.score_obtenu = self.question.get_score_for_response(self.reponse)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.evaluation} - {self.question} - {self.get_reponse_display()}"

    class Meta:
        verbose_name = "Réponse du parent"
        verbose_name_plural = "Réponses des parents"
        constraints = [
            models.UniqueConstraint(
                fields=['evaluation', 'question'],
                name='unique_reponse_par_question'
            )
        ]


class Interpretation(models.Model):
    rubrique = models.ForeignKey(
        Rubrique,
        on_delete=models.CASCADE,
        related_name='interpretations'
    )
    score_min = models.PositiveIntegerField()
    score_max = models.PositiveIntegerField()
    message = models.TextField()

    def __str__(self):
        return f"{self.rubrique.libelle} : {self.score_min} - {self.score_max}"

    class Meta:
        ordering = ['rubrique', 'score_min']
        verbose_name = "Interprétation par rubrique"
        verbose_name_plural = "Interprétations par rubrique"


class InterpretationGlobale(models.Model):
    titre = models.CharField(max_length=150)
    score_min = models.PositiveIntegerField()
    score_max = models.PositiveIntegerField()
    message = models.TextField()

    def __str__(self):
        return f"{self.titre} ({self.score_min} - {self.score_max})"

    class Meta:
        ordering = ['score_min']
        verbose_name = "Interprétation globale"
        verbose_name_plural = "Interprétations globales"