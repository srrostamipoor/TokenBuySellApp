from django.shortcuts import render,redirect
from .models import AccountManager,Account 
from .models import transaction_list 
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import order,order_list,order_note_admin,invoice
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
import re

from django.conf import settings
from django.db import transaction as db_transaction

from .services import BlockchainError, TokenService

logger = logging.getLogger(__name__)



#----------------------------------------------------


special_char_list = r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"
email_special_char_list = r"!\"#$%&'()*+,/:;<=>?@[\]^`{|}~"
def num_checker(string):
    return any(i.isdigit() for i in string)

def special_char_checker(string):
    for i in string:
      if i in special_char_list:
          return True
    return False

def email_special_char_checker(string):
    if "@" in string:
        email = re.split(r'@+', string)
        print(email)
        for i in email[0]:
            if i in special_char_list:
                return True
        return False
    else:
        return True

#---------------------------------------------------------

def register(request):

    if request.POST:
        post_wallet_address=request.POST['wallet_address']
        post_username = request.POST['username']
        post_password = request.POST['password']
        post_conf_password =request.POST['confirm_password']
        post_email = request.POST['email']
        post_phone =  request.POST['phone']
        post_first_name = request.POST['first_name']
        post_last_name = request.POST['last_name']
        check_username = Account.objects.all().filter(username=post_username)
        check_email = Account.objects.all().filter(email=post_email)
        check_phone = Account.objects.filter(phone=post_phone).exists()

        # Checking for number

        if num_checker(post_first_name)==True:
            messages.error(request, "Sorry, First Name can't contain number")
            return redirect("register")

        if num_checker(post_last_name) == True:
            messages.error(request, "Sorry, Last Name can't contain number")
            return redirect("register")

        # Checking for special character

        if special_char_checker(post_first_name):
            messages.error(request, "Sorry, First Name can't contain a special character.")
            return redirect("register")

        if special_char_checker(post_last_name):
            messages.error(request,"Sorry, Last Name can't contain a special character.")
            return redirect("register")

        if special_char_checker(post_username):
            messages.error(request, "Sorry, Username can't contain a special character.")
            return redirect("register")

        if email_special_char_checker(post_email):
            messages.error(request, "Sorry, Email can't contain a special character.")
            return redirect("register")
        
        if post_password != post_conf_password:

            messages.error(request, 'Password and Confirm Password Does not match')
            return redirect("register")
        if check_phone ==True:
            messages.error(request,"An user with the phone number already exits.")
            return redirect("register")
        


        if not check_username or not check_email:
            user = Account.objects.create(
                wallet_address=post_wallet_address,
                first_name=post_first_name,
                last_name=post_last_name,
                username=post_username,
                email=post_email,
                phone = post_phone,
            )
            user.set_password(post_password)
            user.save()
            messages.success(request, 'Your account has been registered. Please Login now')
            return redirect("login")
        else:
            messages.error(request, "Sorry, an user with the same credentials already exits. Please login to your account")
            return redirect("login")

    else:
        if request.user.is_authenticated:
            return redirect('dashboard.html')
        else:
            return render(request, 'register.html')


#----------------------------------------------------
def login(request):
     if request.user.is_authenticated:
         return redirect("dashboard")
     if request.POST:
         session_old = request.session.session_key
         post_email = request.POST['email']
         post_password = request.POST['password']
         user = auth.authenticate(email=post_email,password=post_password)
         if user is not None:

             auth.login(request, user)
             try:
               session_new = request.session.session_key
               act =Account.objects.get(email=post_email)
               act.account_session=session_new
               act.last_active = datetime.now()
               act.save()
             except:
                 pass
             messages.success(request, "You have been logged in.")
             return redirect('dashboard')
         else:
             messages.error(request, "Sorry your Email/Password don't match")
             return redirect('login')

     return render(request,"login.html")
#--------------------------------------------------------------------
@login_required(login_url="/login")
def logout(request):
    if request.user.is_authenticated:
      auth.logout(request)
      messages.success(request,"You have been logged out successfully.")
      return redirect("login")
    else:
      messages.error(request,"Sorry you need to be logged in to do this action")
      return redirect("login")

#------------------------------------------------------------

def account_home(request):
    if request.user.is_authenticated:
       user1 = Account.objects.get(email=request.user.email)
       orders = order.objects.all().filter(client=user1).order_by('date_created')[:4]
       total_oders = len(order.objects.all().filter(client=user1).order_by('date_created'))
       dilevered_orders = len(order.objects.all().filter(client=user1,order_status="COMPLETED"))
       print(total_oders)
       print(dilevered_orders)
       registered_on = user1.registered_on
       registered_on = datetime.fromisoformat(str(registered_on)).strftime("%d/%m/%Y")
       last_login = user1.last_active
       last_login = datetime.fromisoformat(str(last_login)).strftime("%d/%m/%Y")
       context={
               'first_name': request.user.first_name,
               'last_name': request.user.last_name,
               'order_id_list' : orders,
               'total_orders':total_oders,
               'registered_on':registered_on,
               'dilevered_orders':dilevered_orders,
               'last_login':last_login,

            }
       return render(request, "dashboard.html",context=context)
    else:
       messages.error(request,"Sorry, You are not logged in. Please Login and try again")
       return render(request, "login.html")


#---------------------------------
def contact(request):


    return render(request, 'contact-us.html')
#----------------------------------------------
def about(request):

    return render(request, 'about.html')
#----------------------------

@login_required(login_url="/login")
def charge_account(request):
    if request.POST:
        client = request.user
        charge_update = int(request.POST['charge-Account']) 
        client.balance=client.balance+charge_update
        client.save()
        #-----------------------------
        req_user = request.user

        if req_user.is_authenticated:

            #checking if transaction ID alreay exits in db

            transaction_id = request.POST['transaction_id']
            invoice_exits = invoice.objects.filter(transaction_id=transaction_id).exists()

            if invoice_exits == True:
                messages.error(request,"Sorry, transaction Id alreay exits.")
                return render(request, 'charge.html')
        
            client = request.user
            print(client)
            order_note = request.POST['order_note']
            
            order_save = order.objects.create(
                client=client,
               # order_note_user=order_note,

            )
            
            order_list_save = order_list.objects.create(
                    order_id=order_save,
                    order_price=charge_update,
                )
            order_list_save.save()
            # working on invoice
            total_price = charge_update
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            address = request.POST['address']
            city = request.POST['city']
            division = request.POST['division']
            zip = request.POST['zip']
            country = request.POST['country']
            order_note = request.POST['order_note']
            
            save_invoice = invoice.objects.create(
                order_id=order_save,
                total_price=total_price,
                first_name=first_name,
                last_name=last_name,
                address=address,
                division=division,
                city=city,
                zip=zip,
                country=country,
                transaction_id=transaction_id,
                order_note=order_note,
                transaction_method = 'bkash',
                invoice_status="PENDING_CHECK",


            )
            order_status_update = order.objects.filter(order_id=order_save.order_id).update(order_status="PROCESSING")

    else:
        messages.error(request,"Sorry,The operation was not successful. try again")
        return redirect(account_home)
    messages.success(request, 'The operation was successful.')
    return redirect(account_home)
#-----------------------------------   
def charge(request):
    if request.user.is_authenticated:
        return render(request, 'charge.html')
    else:
        messages.error(request,"You need to be registered to place an order ")
        return render(request, 'register.html')
    
#-----------------------------------------
def registershow(request):

    return render(request, 'register.html')

#------------------------------------------------------------------------

def orders(request):
        if request.user.is_authenticated:
            user = Account.objects.get(email=request.user.email)
            order_id = order.objects.all().filter(client=user).order_by('date_created')

            all_orders = Paginator(order.objects.all().filter(client=user).order_by('-date_created'), 10)
            page = request.GET.get('page')

            try:
                orders = all_orders.page(page)
            except PageNotAnInteger:
                orders = all_orders.page(1)
            except EmptyPage:
                orders=  all_orders.page(all_orders.num_pages)

            context={

                'order_id_list' : orders,
            }
            return render(request,"list-orders.html",context)
        else:
            messages.error(request,"Sorry, you need to be logged in to view your orders")
            return render(request,"login.html")
 

@login_required(login_url="/login")
def view_order(request, order_id):
      if request.user.is_authenticated:

          print(order_id)
          order_items_list = order_list.objects.all().filter(order_id=order_id)
          invoice_details = invoice.objects.all().filter(order_id=order_id)
          context={
              "order_id":order_id,

              "order_items_list":order_items_list,
              "invoice_list": invoice_details
          }
          return render(request,"view_order.html",context=context)
      else:
          return  render(request,"login.html")


@login_required(login_url="/login")
def view_invoice(request, invoice_id):
     if request.user.is_authenticated:
         invoice_dat = invoice.objects.get(invoice_id=invoice_id)

         context = {

             'invoice':invoice_dat

         }
         return render(request,"view_invoice.html",context=context)
     else:
         return  render(request,"login.html")

#-----------------------------------------------------------------------


#---------------------------------------
def buy(request):
    if request.user.is_authenticated:
        return render(request, 'buy_token.html')
    else:
        messages.error(request,"You need to be registered to place an order ")
        return render(request, 'register.html')
#---------------------------------------------------------------
@login_required(login_url="/login")
def buy_token(request):
    """
    Buy tokens with the credit balance held in the user's account.

    Flow:
      1. Validate the requested amount.
      2. Lock the user row and check the credit balance (prevents double-spend).
      3. Send the ERC-20 transfer on-chain.
      4. Only if the transfer succeeds, deduct credit and record the transaction.

    Steps 3 and 4 are deliberately ordered this way: we never deduct the user's
    balance for a transfer that failed on-chain.
    """
    if request.method != "POST":
        return redirect(account_home)

    raw_amount = request.POST.get("token-value", "")
    try:
        token_amount = int(raw_amount)
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid number of tokens.")
        return redirect(account_home)

    if token_amount <= 0:
        messages.error(request, "The number of tokens must be greater than zero.")
        return redirect(account_home)

    try:
        service = TokenService()
    except BlockchainError as exc:
        logger.error("Blockchain unavailable: %s", exc)
        messages.error(request, "The token service is temporarily unavailable.")
        return redirect(account_home)

    cost = service.price_for(token_amount)

    # Lock the account row so two concurrent requests cannot spend the same credit.
    with db_transaction.atomic():
        account = Account.objects.select_for_update().get(pk=request.user.pk)
        if account.balance < cost:
            messages.error(request, "Insufficient balance. Please charge your account first.")
            return redirect(account_home)

    try:
        tx_hash = service.transfer(account.wallet_address, token_amount)
    except BlockchainError as exc:
        messages.error(request, str(exc))
        return redirect(account_home)

    # The transfer succeeded on-chain. Now settle the off-chain ledger.
    with db_transaction.atomic():
        account = Account.objects.select_for_update().get(pk=request.user.pk)
        account.balance -= cost
        account.save(update_fields=["balance"])

        transaction_list.objects.create(
            transaction_from=settings.TREASURY_ADDRESS,
            transaction_to=account.wallet_address,
            transaction_price=cost,
            transaction_value=token_amount,
            transaction_txhash=tx_hash,
        )

    messages.success(request, f"Purchase complete. Transaction hash: {tx_hash}")
    return redirect(account_home)
#-------------------------------------------------------------------------------

@login_required(login_url="/login")
def transactions(request):
        if request.user.is_authenticated:
            user = Account.objects.get(email=request.user.email)
            address=user.wallet_address
            transaction_id = transaction_list.objects.all().filter(transaction_to=address).order_by('transaction_date')

            all_transactions = Paginator(transaction_list.objects.all().filter(transaction_to=address).order_by('transaction_date'), 10)
            page = request.GET.get('page')

            try:
                transactions =  all_transactions.page(page)
            except PageNotAnInteger:
               transactions =  all_transactions.page(1)
            except EmptyPage:
                transactions=   all_transactions.page( all_transactions.num_pages)

            context={

                'transaction_id_list' : transactions,
            }
            return render(request,"list-transaction.html",context)
        else:
            messages.error("Sorry, you need to be logged in to view your orders")
            return  redirect("login")
#--------------------------------------------------------view_transaction
@login_required(login_url="/login")
def view_transaction(request,transaction_id):
      if request.user.is_authenticated:
          print(transaction_id)
          transaction_items_list =transaction_list.objects.all().filter(transaction_id=transaction_id)
       
          context={
              "transaction_id":transaction_id,
              "transaction_items_list":transaction_items_list,
              }
          return render(request,"view_transaction.html",context=context)
      else:
          return  render(request,"login.html")
#---------------------------------------------------
      
def about(request):

    return render(request, 'about.html')
#--------------------------------------------------------
def home(request):
        # page = request.GET.get('page', 1)
        # offset = request.GET.get('offset', 20)
        url = settings.ETHERSCAN_API_URL
        params = {
            'module':'account',
            'action':'tokentx',
            'contractaddress': settings.TOKEN_CONTRACT_ADDRESS,
            'address':'0x79FB56E28e27338cc36a015c35a1497C70987cE3',
            'page':1,
            'offset':30,
            'startblock':0,
            'endblock':99999999,
            'sort':'desc',
            'apikey': settings.ETHERSCAN_API_KEY,
           }
        response = requests.get(url, params=params)
        transactions = response.json()["result"]
        
        all_transactions = Paginator( transactions, 10)
        page = request.GET.get('page')

        try:
            transactions =  all_transactions.page(page)
        except PageNotAnInteger:
            transactions =  all_transactions.page(1)
        except EmptyPage:
            transactions=   all_transactions.page( all_transactions.num_pages)

        context={
             'transaction_id_list' : transactions,
            }
        return render(request,"index.html",context)
#----------------------------------------------------------------
def show_transaction(request,transaction_hash):
        # transaction_items_list = transaction_list.objects.get(transaction_txhash=transaction_hash)
        transaction_items_list =transaction_list.objects.all().filter(transaction_txhash=transaction_hash)
        context={
              "transaction_txhash":transaction_hash,
              "transaction_items_list":transaction_items_list,
              }
        return render(request,"show_transaction.html",context=context)

#0xbdf24f8f5bf31a7599fe3e7be0b0433c11599f383d96b8c093f8ae019c7d8da9
def search(request):
        transaction_hash=request.POST['search']
        transaction_items_list =transaction_list.objects.all().filter(transaction_txhash=transaction_hash)
        context={
              "transaction_txhash":transaction_hash,
              "transaction_items_list":transaction_items_list,
              }
        return render(request,"show_transaction.html",context=context)
     
#-------------------------------------------------------------
def change_pwd(request):
    if request.POST:
        password = request.POST['password']
        confirm_password = request.POST['verify_password']
        old_password = request.POST['old_password']
        if password == confirm_password:
            user = Account.objects.get(email=request.user.email)
            if user.check_password(old_password):
              user.set_password(password)
              user.save()
              messages.success(request,"Your Password has been successfully chanaged.")
              return redirect("login")
            else:
              messages.error(request, "Sorry, your old password doesn't match our record.")
              return redirect("change_pwd")
        else:
           messages.error(request, "Sorry your password and verify password doesn't match.")
           return redirect("change_pwd")
    else:
      return render(request,"change_password.html")
    
#----------------------------------------------------------------

@login_required(login_url="/login")
def profile_edit(request):
    if request.user.is_authenticated:
        if request.POST:
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            phone = request.POST['phone']

            # Checking for numbers

            if num_checker(first_name) == True:
                messages.error(request, "Sorry, First Name can't contain number.")
                return redirect("profile_edit")

            if num_checker(last_name) == True:
                messages.error(request, "Sorry, Last Name can't contain number.")
                return redirect("profile_edit")

            # Checking for special character

            if special_char_checker(first_name):
                messages.error(request, "Sorry, First Name can't contain a special character.")
                return redirect("profile_edit")

            if special_char_checker(last_name):
                messages.error(request, "Sorry, Last Name can't contain a special character.")
                return redirect("profile_edit")

            if email_special_char_checker(email):
                messages.error(request, "Sorry, Email can't contain a special character.")
                return redirect("profile_edit")



            user = Account.objects.all().filter(username=request.user.username)
            user.update(first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone)
            messages.success(request, "Your Profile has been updated")

        return render(request, "edit_profile.html")

    else:
        messages.error(request,"Sorry, You need to be logged in to do this action.")
        return redirect('login')
#------------------------------------------------------------------
def about(request):

    return render(request, 'about.html')
