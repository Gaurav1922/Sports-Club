from django.contrib import admin
from .models import Club, Review, Sport

@admin.register(Club)
class SportsClubAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'average_rating', 'total_reviews', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location', 'description']
    readonly_fields = ['average_rating', 'total_reviews', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'description', 'is_active')
        }),
        ('Timings', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_clubs', 'deactivate_clubs']

    def activate_clubs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} clubs activated.')
    activate_clubs.short_description = 'Activate selected clubs'

    def deactivate_clubs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} clubs deactivated.')
    deactivate_clubs.short_description = 'Deactivate selected clubs'


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ['name', 'club', 'price_per_hour', 'is_active']
    list_filter = ['is_active', 'club', 'name']
    search_fields = ['name', 'club__name', 'description']
    list_per_page = 50

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'club', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_per_hour',)
        }),
    )

    actions = ['activate_sports', 'deactivate_sports']

    def activate_sports(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} sports activated.')
    activate_sports.short_description = 'Activate selected sports'

    def deactivate_sports(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} sports deactivated.')
    deactivate_sports.short_description = 'Deactivate selected sports'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'club', 'rating', 'created_at', 'get_comment_preview']
    list_filter = ['rating', 'created_at', 'club']
    search_fields = ['user__username', 'user__email', 'club__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'club', 'booking', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    get_comment_preview.short_description = 'Comment Preview'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'club', 'booking')

    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        self.message_user(request, f'{queryset.count()} reviews processed.')
    approve_reviews.short_description = 'Approve selected reviews'


"""from django.contrib import admin
from .models import Club, Review, Sport

# Register your models here.
@admin.register(Club)
class SportsClubAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'rating', 'price_per_hour', 'is_active', 'created_at']
    list_filter = ['is_active', 'sports_available', 'rating', 'created_at']
    search_fields = ['name', 'address', 'description']
    readonly_fields = ['rating', 'total_reviews', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'description', 'is_active')
        }),
        ('Timings', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_clubs', 'deactivate_clubs']
    
    def activate_clubs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} clubs activated.')
    activate_clubs.short_description = 'Activate selected clubs'
    
    def deactivate_clubs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} clubs deactivated.')
    deactivate_clubs.short_description = 'Deactivate selected clubs'


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ['name', 'club', 'price_per_hour', 'is_active']
    list_filter = ['is_active', 'club', 'name']
    search_fields = ['name', 'club__name', 'description']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'club', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_per_hour',)
        }),
    )
    
    actions = ['activate_sports', 'deactivate_sports']
    
    def activate_sports(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} sports activated.')
    activate_sports.short_description = 'Activate selected sports'
    
    def deactivate_sports(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} sports deactivated.')
    deactivate_sports.short_description = 'Deactivate selected sports'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'club', 'rating', 'created_at', 'get_comment_preview']
    list_filter = ['rating', 'created_at', 'club']
    search_fields = ['user__username', 'user__email', 'club__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'club', 'booking', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    get_comment_preview.short_description = 'Comment Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'club', 'booking')
    
    actions = ['approve_reviews', 'delete_selected_reviews']
    
    def approve_reviews(self, request, queryset):
        # Placeholder for future approval system
        self.message_user(request, f'{queryset.count()} reviews processed.')
    approve_reviews.short_description = 'Approve selected reviews'
    """