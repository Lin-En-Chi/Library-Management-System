from django.contrib import admin
from libraryapp import models

admin.site.register(models.UserProfile)
admin.site.register(models.Book)
admin.site.register(models.Copy)
admin.site.register(models.Loan)
admin.site.register(models.Reservation)
admin.site.register(models.SearchLog)
