from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    對應期中報告 USER 表的額外欄位
    User_id, User_name, Email 由 Django 內建 User 處理
    這裡只存 Phone, Current_state
    """
    STATE_CHOICES = [
        ('active', '正常'),
        ('suspended', '停權'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, default='')
    current_state = models.CharField(max_length=20, choices=STATE_CHOICES, default='active')

    def __str__(self):
        return f"{self.user.username} ({self.current_state})"


class Book(models.Model):
    """對應期中報告 BOOK 表"""
    isbn = models.CharField(max_length=20, primary_key=True)
    title = models.CharField(max_length=200, null=False)
    author = models.CharField(max_length=100, blank=True, default='')
    publisher = models.CharField(max_length=100, blank=True, default='')
    publish_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"{self.title} ({self.isbn})"

    def available_copies(self):
        """回傳目前可借的 copy 數量"""
        return self.copies.filter(status='available').count()

    def total_copies(self):
        """回傳總 copy 數量"""
        return self.copies.count()


class Copy(models.Model):
    """對應期中報告 COPY 表（每本書的實體副本）"""
    STATUS_CHOICES = [
        ('available', '可借閱'),
        ('borrowed', '已借出'),
        ('lost', '遺失'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"{self.book.title} - Copy {self.id} ({self.status})"


class Loan(models.Model):
    """對應期中報告 LOAN 表（借閱記錄）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name='loans')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} borrowed {self.book.title} on {self.borrow_date}"

    def is_returned(self):
        return self.return_date is not None


class Reservation(models.Model):
    """對應期中報告 RESERVATION 表"""
    STATUS_CHOICES = [
        ('waiting', '等待中'),
        ('fulfilled', '已取書'),
        ('cancelled', '已取消'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')

    def __str__(self):
        return f"{self.user.username} reserved {self.book.title} on {self.reservation_date}"


class SearchLog(models.Model):
    """對應期中報告 SEARCH_LOG 表（解開 USER 與 BOOK 之間的 M:N 關係）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_logs', null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='search_logs')
    search_date = models.DateTimeField(auto_now_add=True)
    keyword = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"Search: {self.keyword} -> {self.book.title}"
