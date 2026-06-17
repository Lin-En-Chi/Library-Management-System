from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.conf import settings
from datetime import timedelta, date
from libraryapp import models


# -------------------- 共用工具 --------------------
def get_hot_books(top_n=10):
    """熱門書籍：依借閱次數排序"""
    hot = (
        models.Book.objects
        .annotate(loan_count=Count('loans'))
        .order_by('-loan_count', 'title')[:top_n]
    )
    return hot


def is_admin(user):
    """判斷是否為管理員（superuser 或 staff）"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


# -------------------- 讀者端 --------------------
def index(request):
    """首頁（對應流程圖：首頁 / 登入後首頁）
    根據登入狀態 render 不同 template
    """
    hot_books = get_hot_books()
    if request.user.is_authenticated:
        return render(request, 'index_logged_in.html', locals())
    return render(request, 'index.html', locals())


def register(request):
    """會員申請（對應流程圖：會員申請）"""
    message = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        # 驗證
        if not username or not password:
            message = '帳號和密碼為必填！'
        elif password != password2:
            message = '兩次密碼輸入不一致！'
        elif User.objects.filter(username=username).exists():
            message = '此帳號已被使用！'
        else:
            # 建立 User 和 UserProfile
            user = User.objects.create_user(username=username, password=password, email=email)
            models.UserProfile.objects.create(user=user, phone=phone, current_state='active')
            message = '註冊成功！請登入。'
            return redirect('/login/')

    return render(request, 'register.html', locals())


def user_login(request):
    """會員登入（對應流程圖：帳密輸入）"""
    message = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # 隱藏入口：teach / teach123 進入使用手冊
        if username == 'teach' and password == 'teach123':
            return redirect('/manual/')

        user = authenticate(username=username, password=password)
        if user is not None:
            # 檢查 UserProfile 狀態
            profile = getattr(user, 'profile', None)
            if profile and profile.current_state == 'suspended':
                message = '此帳號已被停權！'
            else:
                auth_login(request, user)
                # 管理員導向管理頁面，一般使用者導向首頁
                if is_admin(user):
                    return redirect('/adminmain/')
                return redirect('/index/')
        else:
            message = '帳號或密碼錯誤！'
    return render(request, 'login.html', locals())


def manual(request):
    """使用手冊（隱藏入口：登入頁輸入 teach / teach123）"""
    return render(request, 'manual.html', locals())


def user_logout(request):
    """登出"""
    auth_logout(request)
    return redirect('/index/')


def book_search(request):
    """書籍查找（對應流程圖：查書）"""
    keyword = request.GET.get('keyword', '').strip()
    books = []
    if keyword:
        books = models.Book.objects.filter(
            Q(title__icontains=keyword) |
            Q(author__icontains=keyword) |
            Q(isbn__icontains=keyword) |
            Q(category__icontains=keyword)
        )
        # 寫入 SearchLog
        user = request.user if request.user.is_authenticated else None
        for book in books:
            models.SearchLog.objects.create(user=user, book=book, keyword=keyword)
    # 全部館藏（供搜尋框下方瀏覽參考）
    all_books = models.Book.objects.all().order_by('category', 'title')
    return render(request, 'search.html', locals())


def book_detail(request, isbn):
    """書籍資訊（對應流程圖：書籍資訊）"""
    book = get_object_or_404(models.Book, isbn=isbn)
    available = book.available_copies()
    total = book.total_copies()
    # 是否已預約此書
    has_reserved = False
    if request.user.is_authenticated:
        has_reserved = models.Reservation.objects.filter(
            user=request.user, book=book, status='waiting'
        ).exists()
    return render(request, 'book_detail.html', locals())


def borrow_book(request, isbn):
    """借書"""
    if not request.user.is_authenticated:
        return redirect('/login/')

    book = get_object_or_404(models.Book, isbn=isbn)
    # 檢查使用者狀態
    profile = getattr(request.user, 'profile', None)
    if profile and profile.current_state == 'suspended':
        message = '您的帳號已被停權，無法借書！'
        return render(request, 'message.html', locals())

    # 找一本 available 的 copy
    available_copy = book.copies.filter(status='available').first()
    if not available_copy:
        message = '此書目前全部借出，請改用預約功能！'
        return render(request, 'message.html', locals())

    # 借出
    available_copy.status = 'borrowed'
    available_copy.save()
    due = date.today() + timedelta(days=settings.LOAN_PERIOD_DAYS)
    models.Loan.objects.create(
        user=request.user,
        copy=available_copy,
        book=book,
        due_date=due,
    )
    message = f'借書成功！請於 {due} 前歸還。'
    return render(request, 'message.html', locals())


def reserve_book(request, isbn):
    """預約"""
    if not request.user.is_authenticated:
        return redirect('/login/')

    book = get_object_or_404(models.Book, isbn=isbn)
    # 是否已預約
    if models.Reservation.objects.filter(user=request.user, book=book, status='waiting').exists():
        message = '您已預約此書！'
        return render(request, 'message.html', locals())

    models.Reservation.objects.create(user=request.user, book=book, status='waiting')
    message = '預約成功！書籍可借時會通知您。'
    return render(request, 'message.html', locals())


def my_loans(request):
    """個人借閱資訊（對應流程圖：讀者借閱資訊）"""
    if not request.user.is_authenticated:
        return redirect('/login/')

    current_loans = models.Loan.objects.filter(
        user=request.user, return_date__isnull=True
    ).order_by('-borrow_date')
    history_loans = models.Loan.objects.filter(
        user=request.user, return_date__isnull=False
    ).order_by('-return_date')
    reservations = models.Reservation.objects.filter(
        user=request.user, status='waiting'
    ).order_by('-reservation_date')

    today = date.today()
    # 計算逾期未還的數量（已借閱且超過應還日）
    overdue_count = current_loans.filter(due_date__lt=today).count()
    return render(request, 'my_loans.html', locals())


def return_book(request, loan_id):
    """還書"""
    if not request.user.is_authenticated:
        return redirect('/login/')

    loan = get_object_or_404(models.Loan, id=loan_id, user=request.user)
    if loan.return_date is not None:
        message = '此書已歸還！'
        return render(request, 'message.html', locals())

    loan.return_date = date.today()
    loan.save()
    # copy 改回可借
    loan.copy.status = 'available'
    loan.copy.save()

    message = '還書成功！'
    return render(request, 'message.html', locals())


# -------------------- 管理員端 --------------------
def adminmain(request):
    """管理員主頁"""
    if not is_admin(request.user):
        return redirect('/login/')

    total_books = models.Book.objects.count()
    total_copies = models.Copy.objects.count()
    total_loans = models.Loan.objects.filter(return_date__isnull=True).count()
    total_users = User.objects.count()
    return render(request, 'adminmain.html', locals())


def admin_books(request):
    """管理書籍清單"""
    if not is_admin(request.user):
        return redirect('/login/')

    books = models.Book.objects.all().order_by('title')
    return render(request, 'admin_books.html', locals())


def admin_book_add(request):
    """新增書籍"""
    if not is_admin(request.user):
        return redirect('/login/')

    message = ''
    if request.method == 'POST':
        isbn = request.POST.get('isbn', '').strip()
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        publisher = request.POST.get('publisher', '').strip()
        publish_date = request.POST.get('publish_date', '').strip()
        category = request.POST.get('category', '').strip()
        location = request.POST.get('location', '').strip()

        if not isbn or not title:
            message = 'ISBN 和書名為必填！'
        elif models.Book.objects.filter(isbn=isbn).exists():
            message = '此 ISBN 已存在！'
        else:
            book = models.Book(
                isbn=isbn, title=title, author=author,
                publisher=publisher, category=category, location=location
            )
            if publish_date:
                book.publish_date = publish_date
            book.save()
            return redirect('/admin_books/')

    return render(request, 'admin_book_form.html', locals())


def admin_book_edit(request, isbn):
    """編輯書籍"""
    if not is_admin(request.user):
        return redirect('/login/')

    book = get_object_or_404(models.Book, isbn=isbn)
    message = ''
    if request.method == 'POST':
        book.title = request.POST.get('title', '').strip()
        book.author = request.POST.get('author', '').strip()
        book.publisher = request.POST.get('publisher', '').strip()
        publish_date = request.POST.get('publish_date', '').strip()
        if publish_date:
            book.publish_date = publish_date
        book.category = request.POST.get('category', '').strip()
        book.location = request.POST.get('location', '').strip()
        book.save()
        return redirect('/admin_books/')

    # 編輯模式
    is_edit = True
    return render(request, 'admin_book_form.html', locals())


def admin_book_delete(request, isbn):
    """刪除書籍"""
    if not is_admin(request.user):
        return redirect('/login/')

    book = get_object_or_404(models.Book, isbn=isbn)
    book.delete()
    return redirect('/admin_books/')


def admin_copies(request, isbn):
    """管理副本（新增該書的副本數量）"""
    if not is_admin(request.user):
        return redirect('/login/')

    book = get_object_or_404(models.Book, isbn=isbn)
    message = ''
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'add':
            try:
                count = int(request.POST.get('count', '1'))
            except ValueError:
                count = 1
            count = max(1, min(count, 100))  # 限制 1-100 之間
            for _ in range(count):
                models.Copy.objects.create(book=book, status='available')
            message = f'已新增 {count} 本副本！'
        elif action == 'delete':
            copy_id = request.POST.get('copy_id', '')
            try:
                copy = models.Copy.objects.get(id=copy_id, book=book)
                if copy.status == 'borrowed':
                    message = '此副本已借出，無法刪除！'
                else:
                    copy.delete()
                    message = '副本已刪除！'
            except models.Copy.DoesNotExist:
                message = '副本不存在！'

    copies = book.copies.all().order_by('id')
    return render(request, 'admin_copies.html', locals())


def admin_loans(request):
    """查看所有借閱記錄"""
    if not is_admin(request.user):
        return redirect('/login/')

    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'active':
        loans = models.Loan.objects.filter(return_date__isnull=True).order_by('-borrow_date')
    elif filter_type == 'returned':
        loans = models.Loan.objects.filter(return_date__isnull=False).order_by('-return_date')
    else:
        loans = models.Loan.objects.all().order_by('-borrow_date')

    today = date.today()
    return render(request, 'admin_loans.html', locals())
