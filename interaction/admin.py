from django.contrib import admin
from .models import (
    Rubrique,
    Questionnaire,
    ChoixReponse,
    Enfant,
    Evaluation,
    ReponseParent,
    Interpretation,
    InterpretationGlobale,
)


class QuestionnaireInline(admin.TabularInline):
    model = Questionnaire
    extra = 1
    ordering = ('ordre',)


class InterpretationInline(admin.TabularInline):
    model = Interpretation
    extra = 1


class ReponseParentInline(admin.TabularInline):
    model = ReponseParent
    extra = 0
    autocomplete_fields = ('question',)
    readonly_fields = ('score_obtenu',)


@admin.register(Rubrique)
class RubriqueAdmin(admin.ModelAdmin):
    list_display = ('libelle',)
    search_fields = ('libelle',)
    ordering = ('libelle',)
    inlines = [QuestionnaireInline, InterpretationInline]


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = (
        'question',
        'rubrique',
        'ordre',
        'score_oui',
        'score_parfois',
        'score_non',
    )
    list_filter = ('rubrique',)
    search_fields = ('question', 'rubrique__libelle')
    ordering = ('rubrique', 'ordre', 'id')
    autocomplete_fields = ('rubrique',)


@admin.register(ChoixReponse)
class ChoixReponseAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'score')
    search_fields = ('libelle',)
    ordering = ('id',)


@admin.register(Enfant)
class EnfantAdmin(admin.ModelAdmin):
    list_display = ('code_enfant', 'nom', 'prenom', 'date_naissance', 'age')
    search_fields = ('code_enfant', 'nom', 'prenom')
    list_filter = ('date_naissance',)
    ordering = ('nom', 'prenom')
    readonly_fields = ('code_enfant', 'age')

    fieldsets = (
        ("Informations de l’enfant", {
            'fields': ('code_enfant', 'nom', 'prenom', 'date_naissance', 'age')
        }),
    )


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'enfant',
        'date_evaluation',
        'terminee',
        'score_total_admin',
        'score_maximum_admin',
        'pourcentage_score_admin',
    )
    list_filter = ('terminee', 'date_evaluation')
    search_fields = ('enfant__nom', 'enfant__prenom', 'enfant__code_enfant', 'commentaire')
    readonly_fields = (
        'date_evaluation',
        'score_total_admin',
        'score_maximum_admin',
        'pourcentage_score_admin',
    )
    autocomplete_fields = ('enfant',)
    inlines = [ReponseParentInline]

    fieldsets = (
        ("Informations générales", {
            'fields': ('enfant', 'date_evaluation', 'terminee', 'commentaire')
        }),
        ("Résultats", {
            'fields': ('score_total_admin', 'score_maximum_admin', 'pourcentage_score_admin')
        }),
    )

    def score_total_admin(self, obj):
        return obj.score_total()
    score_total_admin.short_description = "Score total"

    def score_maximum_admin(self, obj):
        return obj.score_maximum()
    score_maximum_admin.short_description = "Score maximum"

    def pourcentage_score_admin(self, obj):
        return f"{obj.pourcentage_score()} %"
    pourcentage_score_admin.short_description = "Pourcentage"


@admin.register(ReponseParent)
class ReponseParentAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'question', 'reponse', 'score_obtenu', 'rubrique')
    list_filter = ('question__rubrique', 'reponse')
    search_fields = (
        'evaluation__enfant__nom',
        'evaluation__enfant__prenom',
        'question__question',
    )
    autocomplete_fields = ('evaluation', 'question')
    readonly_fields = ('score_obtenu',)

    def rubrique(self, obj):
        return obj.question.rubrique.libelle
    rubrique.short_description = "Rubrique"


@admin.register(Interpretation)
class InterpretationAdmin(admin.ModelAdmin):
    list_display = ('rubrique', 'score_min', 'score_max', 'message_court')
    list_filter = ('rubrique',)
    search_fields = ('rubrique__libelle', 'message')
    ordering = ('rubrique', 'score_min')
    autocomplete_fields = ('rubrique',)

    def message_court(self, obj):
        return obj.message[:80] + "..." if len(obj.message) > 80 else obj.message
    message_court.short_description = "Message"


@admin.register(InterpretationGlobale)
class InterpretationGlobaleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'score_min', 'score_max', 'message_court')
    search_fields = ('titre', 'message')
    ordering = ('score_min',)

    def message_court(self, obj):
        return obj.message[:80] + "..." if len(obj.message) > 80 else obj.message
    message_court.short_description = "Message"


admin.site.site_header = "Administration Elongo"
admin.site.site_title = "Elongo Admin"
admin.site.index_title = "Gestion de l’application"