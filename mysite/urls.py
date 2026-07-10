from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from myapp.views import home
from myapp.views import register
from myapp.views import login
from myapp.views import logout
from myapp.views import account_home
from myapp.views import contact
from myapp.views import charge
from myapp.views import charge_account
from myapp.views import registershow
from myapp.views import orders
from myapp.views import transactions
from myapp.views import view_order
from myapp.views import view_transaction
from myapp.views import show_transaction
from myapp.views import view_invoice
from myapp.views import buy_token
from myapp.views import buy
from myapp.views import search
from myapp.views import profile_edit
from myapp.views import change_pwd
from myapp.views import about
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home,name="home"),
    path('register/',register, name="register" ),
    path('login/', login, name="login"),
    path('logout/', logout, name="logout"),
    path("dashboard/", account_home, name="dashboard"),
    path('contact',contact),
    path('charge/',charge),
    path('charge-account/',charge_account),
    path('registershow/',registershow),
    path('dashboard/orders',orders,name="orders"),
    path("dashboard/view_order/<int:order_id>", view_order, name="view_order"),
    path("dashboard/view_invoice/<int:invoice_id>", view_invoice,name="view_invoice"),
    path('buy_token/',buy_token),
    path('buy/',buy),
    path('dashboard/transactions',transactions,name="transactions"),
    path("dashboard/view_transaction/<int:transaction_id>", view_transaction, name="view_transaction"),
    path("show_transaction/<transaction_hash>", show_transaction, name="show_transaction"),
    path("search/", search, name="search"),
    path('dashboard/profile_edit', profile_edit,name="profile_edit"),
    path('dashboard/change_pwd', change_pwd,name="change_pwd"),
    path('about',about),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)