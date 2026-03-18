from django.contrib import admin
from .models import AIRecommendation


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display  = ('project', 'rec_type', 'url', 'tokens_used', 'created_at')
    list_filter   = ('project', 'rec_type')
    search_fields = ('url',)
    readonly_fields = ('input_data', 'result', 'tokens_used', 'created_at')
