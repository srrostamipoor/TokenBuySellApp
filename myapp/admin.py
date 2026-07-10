from django.contrib import admin
from .models import Account
from .models import transaction_list
from .models import order_note_admin,order,order_list,invoice
# Register your models here.

class AccountAdmin(admin.ModelAdmin):
  list_display = ('email','username','phone','is_active','last_active','registered_on','wallet_address','balance')
  readonly_fields = ('last_active','registered_on','wallet_address','balance')
  list_display_links = ('email','username','phone','is_active')
  odering = ('-last_active')

admin.site.register(Account, AccountAdmin)
admin.site.register(transaction_list)
# Register your models here.
admin.site.register(order)
admin.site.register(order_note_admin)

admin.site.register(invoice)