from django.contrib import admin
from .models import Statement, StatementDetail, Account


class StatementDetailInline(admin.TabularInline):
    model = StatementDetail
    extra = 0
    readonly_fields = ['id']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'account_abbr', 'account_number', 'account_type', 'created_at']
    list_filter = ['bank_name', 'account_type', 'created_at']
    search_fields = ['bank_name', 'account_abbr', 'account_number']
    readonly_fields = ['id', 'created_at']


@admin.register(Statement)
class StatementAdmin(admin.ModelAdmin):
    list_display = [
        'account', 'statement_from_date', 'statement_to_date', 
        'statement_type', 'total_credits', 'total_debits', 
        'net_amount', 'uploaded_at'
    ]
    list_filter = ['account__bank_name', 'statement_type', 'statement_from_date', 'statement_to_date']
    search_fields = ['account__bank_name', 'account__account_abbr', 'account__account_number']
    readonly_fields = ['id', 'uploaded_at', 'total_credits', 'total_debits', 'net_amount']
    inlines = [StatementDetailInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'account', 'source_file', 'statement_type')
        }),
        ('Date Range', {
            'fields': ('statement_from_date', 'statement_to_date')
        }),
        ('Summary', {
            'fields': ('total_credits', 'total_debits', 'net_amount', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StatementDetail)
class StatementDetailAdmin(admin.ModelAdmin):
    list_display = [
        'item', 'statement', 'transaction_date', 
        'amount', 'direction'
    ]
    list_filter = ['direction', 'transaction_date', 'statement__account__bank_name']
    search_fields = ['item', 'statement__account__bank_name', 'statement__account__account_abbr']
    readonly_fields = ['id']
    date_hierarchy = 'transaction_date'
