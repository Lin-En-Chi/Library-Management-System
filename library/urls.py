"""library URL Configuration"""
from django.contrib import admin
from django.urls import path
from libraryapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 讀者端
    path('', views.index),
    path('index/', views.index),
    path('register/', views.register),                              # 會員申請
    path('login/', views.user_login),                               # 會員登入
    path('logout/', views.user_logout),                             # 登出
    path('manual/', views.manual),                                  # 使用手冊（隱藏入口）
    path('search/', views.book_search),                             # 書籍查找
    path('book/<str:isbn>/', views.book_detail),                    # 書籍資訊
    path('borrow/<str:isbn>/', views.borrow_book),                  # 借書
    path('reserve/<str:isbn>/', views.reserve_book),                # 預約
    path('my_loans/', views.my_loans),                              # 個人借閱資訊
    path('return/<int:loan_id>/', views.return_book),               # 還書

    # 管理員端
    path('adminmain/', views.adminmain),                            # 管理員主頁
    path('admin_books/', views.admin_books),                        # 管理書籍
    path('admin_book_add/', views.admin_book_add),                  # 新增書籍
    path('admin_book_edit/<str:isbn>/', views.admin_book_edit),     # 編輯書籍
    path('admin_book_delete/<str:isbn>/', views.admin_book_delete), # 刪除書籍
    path('admin_copies/<str:isbn>/', views.admin_copies),           # 管理副本
    path('admin_loans/', views.admin_loans),                        # 查看所有借閱記錄
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
