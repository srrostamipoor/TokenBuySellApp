from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class AccountManager(BaseUserManager):

     def create_user(self, first_name, last_name,username,phone, email,wallet_address,password=None,balance=0):

       user = self.model(
           email=self.normalize_email(email),
           first_name=first_name,
           last_name=last_name,
           username=username,
           wallet_address=wallet_address,
           phone=phone,
           balance=balance
            )
       user.is_admin = False
       user.is_superuser = False
       user.is_staff = False
       user.is_active = True
       user.set_password(password)
       user.save(using=self._db)
       return user

     def create_superuser(self, first_name, last_name,username,phone, email,wallet_address,password=None,balance=0):

       user = self.model(
           email=self.normalize_email(email),
           first_name=first_name,
           last_name=last_name,
           username=username,
           wallet_address=wallet_address,
           phone=phone,
           balance=balance
            )
       user.is_admin = True
       user.is_superuser = True
       user.is_staff = True
       user.is_active = True
       user.set_password(password)
       user.save(using=self._db)
       return user


class Account(AbstractBaseUser):
    account_session = models.CharField(max_length=250,default='default_value')
    wallet_address = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100,blank=True)
    username = models.CharField(max_length=100,unique=True)
    phone = models.CharField(max_length=100,unique=True)
    email = models.CharField(max_length=100,unique=True)

    registered_on = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    #registration_ip = models.CharField(max_length=100,blank=False)
    #last_login_ip = models.CharField(max_length=100, blank=True)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name','last_name','username','phone','wallet_address']
    objects = AccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


#---------------------------------------------------------------------------

class order(models.Model):
    order_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Account, on_delete = models.CASCADE)
    status = [("DRAFT","Draft"),
               ("PENDING","Pending"),
              ("PROCESSING", "processing"),
              ("REJECTED","Rejected"),
              ("CANCELLED","Cancelled"),
              ("DELIVERED","Delivered"),
              ("COMPLETED","Completed")]
    order_status = models.CharField(max_length=30,blank=True,choices=status)
    date_created = models.DateTimeField(blank=False,auto_now_add=True)
    date_updated = models.DateTimeField(blank=False,auto_now=True)

    def __str__(self):
        return str(self.order_id)



class order_list(models.Model):
    order_id = models.ForeignKey(order, blank=False,on_delete=models.DO_NOTHING)
    order_price = models.IntegerField(blank=False)
    def __str__(self):
        return str(self. order_id)



class order_note_admin(models.Model):
    order_id = models.ForeignKey(order,blank=False,on_delete=models.DO_NOTHING)
    message = models.CharField(max_length=3000,blank=True)


class invoice(models.Model):
    status = (("NOT_PAID","Not Paid")
              ,("PAID","Paid"),
              ("PENDING_PAY","Pending Payment"),
              ("REJECTED","Rejected"),
              ("FRAUD","Fraud"),
              ("TIMEOUT","Timeout"),
              ("PENDING_CHECK","Pending Check"),)


    invoice_id = models.AutoField(primary_key=True)
    invoice_status = models.CharField(max_length=300, blank=False, choices=status,default="Pending Payment")
    order_id = models.ForeignKey(order,null=True, blank=False,on_delete=models.DO_NOTHING)
    total_price = models.IntegerField(blank=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    """ billing Details - 
    Decided to put it here because Most website use it this way """

    first_name=models.CharField(max_length=70,blank=False)
    last_name=models.CharField(max_length=70,blank=False)
    address = models.CharField(max_length=500,blank=False)
    city = models.CharField(max_length=100,blank=False)
    division = models.CharField(max_length=60, blank=False)
    zip= models.CharField(max_length=60,blank=False)
    country = models.CharField(max_length=100,blank=True)
    methods = [("bkash","Bkash"),("nagad","Nagad"),("roket","Rocket")]
    transaction_method = models.CharField(max_length=100,blank=False,choices=methods)
    transaction_id  = models.CharField(max_length=100,blank=False,unique=True)
    order_note = models.CharField(max_length=500,blank=True)


    def __str__(self):
        return str(self.invoice_id)




#------------------------------------------------------------------


class transaction_list(models.Model):
    transaction_id =models.AutoField(primary_key=True)
    transaction_price = models.IntegerField(blank=False, default=0)
    transaction_from = models.CharField(max_length=100)
    transaction_to = models.CharField(max_length=100)
    transaction_txhash=models.CharField(max_length=100)
    transaction_value=models.IntegerField(blank=False, default=0)
    transaction_date = models.DateTimeField(blank=False,auto_now_add=True)
    def __str__(self):
        return str(self.transaction_id)










    
    


